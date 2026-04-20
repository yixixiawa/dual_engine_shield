# -*- coding: utf-8 -*-
"""
钓鱼检测 - Token 级归因（事后解释）
使用 embedding 上的 gradient×input 方法，获得每个 token 对钓鱼分类的贡献度
"""
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


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
    计算每个 token 对钓鱼类别 logit 的贡献度
    
    Args:
        model: 分类模型
        tokenizer: 分词器
        text: 输入文本
        device: 计算设备 (cuda/cpu)
        max_length: 最大长度
        phishing_logit_index: 钓鱼类别的 logit 索引（通常为 1）
    
    Returns:
        (token_scores, meta) 元组
        - token_scores: 每个 token 的分数列表
        - meta: 元数据信息
    """
    import torch
    
    try:
        enc_base = dict(
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        
        # 尝试获取 offset_mapping（字符级位置映射）
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
        
        # 计算梯度
        with torch.set_grad_enabled(True):
            base_emb = emb_layer(input_ids).detach()
            input_embeds = base_emb.clone().requires_grad_(True)
            
            # 使用 float32 避免半精度不稳定
            outputs = model(
                inputs_embeds=input_embeds.float(),
                attention_mask=attention_mask,
                output_hidden_states=False
            )
            
            logits = outputs.logits
            phishing_logit = logits[0, phishing_logit_index]
            
            # 反传梯度
            phishing_logit.backward()
            
            grad = input_embeds.grad  # [1, seq_len, hidden_dim]
            
            # 计算 gradient × input 的 L2 范数
            scores = torch.norm(grad[0] * input_embeds[0].detach(), dim=-1)
            scores = scores.detach().cpu().tolist()

        # 获取 token 文本
        tokens = tokenizer.convert_ids_to_tokens(input_ids[0].tolist())
        
        token_scores = []
        for idx, (token, score) in enumerate(zip(tokens, scores)):
            if token in ("[PAD]", "[CLS]", "[SEP]"):
                continue
            
            item = {
                "index": idx,
                "piece": token,
                "score": float(score),
            }
            
            # 添加字符级位置信息（如果可用）
            if offsets and idx < len(offsets):
                char_start, char_end = offsets[idx]
                if char_start >= 0 and char_end >= 0:
                    item["char_start"] = char_start
                    item["char_end"] = char_end
            
            token_scores.append(item)
        
        meta = {
            "method": "gradient_x_input",
            "model_type": type(model).__name__,
            "tokenizer_type": type(tokenizer).__name__,
            "total_tokens": len(tokens),
            "non_special_tokens": len(token_scores),
        }
        
        return token_scores, meta
        
    except Exception as e:
        logger.error(f"Token 归因计算失败: {str(e)}")
        return [], {"error": str(e)}


def top_k_tokens(
    token_scores: List[Dict[str, Any]],
    k: int = 20,
    descending: bool = True
) -> List[Dict[str, Any]]:
    """
    从 token 分数列表中提取 Top-K
    
    Args:
        token_scores: Token 分数列表
        k: 返回的 token 数量
        descending: 是否降序排列
    
    Returns:
        排序后的 Top-K token 列表
    """
    if not token_scores:
        return []
    
    sorted_tokens = sorted(
        token_scores,
        key=lambda x: x.get("score", 0),
        reverse=descending
    )
    
    return sorted_tokens[:k]


def build_explanation(
    detector: 'PhishingDetector',
    model_text: str,
    top_k: int = 20
) -> Dict[str, Any]:
    """
    为单个检测结果生成 Token 级解释
    
    Args:
        detector: 检测器实例
        model_text: 模型输入文本
        top_k: 每个模型返回的 token 数量
    
    Returns:
        包含解释信息的字典
    """
    per_model: Dict[str, Any] = {}
    errors: List[str] = []

    # 原始模型的解释
    if detector._gte_original is not None and detector._tok_original is not None:
        try:
            rows, meta = token_attribution_gradient_x_input(
                detector._gte_original,
                detector._tok_original,
                model_text,
                device=detector.device,
                max_length=detector.max_length,
            )
            per_model["original"] = {
                "meta": meta,
                "top_tokens": top_k_tokens(rows, top_k, descending=True),
            }
            logger.debug(f"原始模型 Token 归因完成: {len(rows)} tokens")
        except Exception as e:
            logger.warning(f"原始模型归因失败: {str(e)}")
            errors.append(f"original_attribution: {str(e)}")

    # ChiPhish 模型的解释
    if detector._gte_chiphish is not None and detector._tok_chiphish is not None:
        try:
            rows, meta = token_attribution_gradient_x_input(
                detector._gte_chiphish,
                detector._tok_chiphish,
                model_text,
                device=detector.device,
                max_length=detector.max_length,
            )
            per_model["chiphish"] = {
                "meta": meta,
                "top_tokens": top_k_tokens(rows, top_k, descending=True),
            }
            logger.debug(f"ChiPhish 模型 Token 归因完成: {len(rows)} tokens")
        except Exception as e:
            logger.warning(f"ChiPhish 模型归因失败: {str(e)}")
            errors.append(f"chiphish_attribution: {str(e)}")

    return {
        "kind": "TokenAttributionBundle",
        "scope": "per_model_top_tokens",
        "per_model": per_model,
        "errors": errors if errors else None,
        "disclaimer": "事后近似解释，非训练目标中的显式理由。仅供前端参考，不作为最终判断依据。",
    }
