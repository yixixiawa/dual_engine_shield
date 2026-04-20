# -*- coding: utf-8 -*-
"""
对「钓鱼」类别 logit 做 embedding 上的 gradient×input，得到 token 级归因（事后解释）。
与静态规则无关；仅供前端高亮 / 排序展示，不应视为严格因果理由。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def token_attribution_gradient_x_input(
    model,
    tokenizer,
    text: str,
    *,
    device: Any,
    max_length: int = 512,
    phishing_logit_index: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    返回 (token_scores, meta)。
    每个 token 项: index, piece, score, char_start?, char_end?（若分词器支持 offset_mapping）
    score 对 phishing_logit_index 的 logit 使用 ∂logit/∂emb · emb 后在 hidden 维求和。
    """
    import torch

    enc_base: Dict[str, Any] = dict(
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    try:
        encoded = tokenizer(text, **enc_base, return_offsets_mapping=True)
    except TypeError:
        encoded = tokenizer(text, **enc_base)

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    offsets = encoded.get("offset_mapping")
    if offsets is not None:
        offsets = offsets[0].tolist()

    model.eval()
    emb_layer = model.get_input_embeddings()
    # leaf tensor，对 inputs_embeds 反传
    with torch.set_grad_enabled(True):
        base_emb = emb_layer(input_ids).detach()
        input_embeds = base_emb.clone().requires_grad_(True)
        # 归因用 float32，避免半精度下梯度不稳定
        input_embeds = input_embeds.to(dtype=torch.float32)
        input_embeds.requires_grad_(True)
        am = attention_mask
        with torch.cuda.amp.autocast(enabled=False):
            out = model(inputs_embeds=input_embeds, attention_mask=am)
            logits = out.logits.float()
            if logits.shape[-1] <= phishing_logit_index:
                raise ValueError(
                    f"模型 num_labels={logits.shape[-1]}，无法取 logit index={phishing_logit_index}"
                )
            logit = logits[0, phishing_logit_index]
        model.zero_grad(set_to_none=True)
        logit.backward()
        grad = input_embeds.grad
        if grad is None:
            raise RuntimeError("归因反传未产生梯度")
        contrib = (grad * input_embeds).sum(dim=-1).detach()[0]

    mask = attention_mask[0].bool()
    ids = input_ids[0].tolist()
    pieces = tokenizer.convert_ids_to_tokens(ids)
    rows: List[Dict[str, Any]] = []
    for i in range(len(pieces)):
        if not mask[i]:
            continue
        row: Dict[str, Any] = {
            "index": i,
            "piece": pieces[i],
            "score": float(contrib[i].item()),
        }
        if offsets is not None and i < len(offsets):
            a, b = offsets[i]
            if b > a or pieces[i] in ("[CLS]", "[SEP]"):
                row["char_start"] = int(a)
                row["char_end"] = int(b)
        rows.append(row)

    meta = {
        "method": "embedding_gradient_x_input",
        "target": f"logits[{phishing_logit_index}]",
        "note": "对「钓鱼」类 logit 的敏感度近似；正分表示该 token 倾向于提高钓鱼 logit。",
        "max_length": max_length,
    }
    return rows, meta


def top_k_tokens(
    rows: List[Dict[str, Any]], k: int, *, descending: bool = True
) -> List[Dict[str, Any]]:
    """按 score 排序取前 k（默认高分在前，便于展示「推高钓鱼」的片段）。"""
    k = max(1, k)
    sorted_rows = sorted(rows, key=lambda r: r["score"], reverse=descending)
    out = []
    for j, r in enumerate(sorted_rows[:k], start=1):
        x = dict(r)
        x["rank"] = j
        out.append(x)
    return out
