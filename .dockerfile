FROM node:20.14-alpine AS frontend

WORKDIR /app/dual_engine_shield

# 复制 package 文件
COPY dual_engine_shield/package*.json ./
RUN npm ci --only=production  # 推荐使用 ci 替代 install 提高可靠性

# 复制源码并构建
COPY dual_engine_shield/ .
RUN npm run build

# 后端构建阶段 - 使用 Go 1.24（最新稳定版）
FROM golang:1.24-alpine AS backend

WORKDIR /app/go-backend

# 设置 Go 代理加速
ENV GOPROXY=https://goproxy.cn,direct

COPY go-backend/go.mod go-backend/go.sum ./
RUN go mod download

COPY go-backend/ .

# 编译优化：减小二进制体积
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o dual-shield ./cmd/server/main.go

# 最终运行阶段
FROM alpine:3.20  # 使用更新的 Alpine

# 安装必要的依赖
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    curl \
    ca-certificates  # 添加证书支持

# 创建非 root 用户（安全最佳实践）
RUN addgroup -g 1000 -S appgroup && \
    adduser -u 1000 -S appuser -G appgroup

# 创建应用目录
WORKDIR /app

# 复制前端构建产物
COPY --from=frontend /app/earth-Model/dist ./frontend

# 复制后端二进制文件
COPY --from=backend /app/go-backend/dual-shield ./

# 复制后端配置和数据
COPY go-backend/config.yaml ./
COPY go-backend/data/ ./data/

# 复制Python相关文件（增加错误处理）
COPY go-backend/internal/python/ ./internal/python/
COPY go-backend/vulscan/ ./vulscan/

# 安装Python依赖（检查文件是否存在）
RUN if [ -f "./vulscan/model_zoo/requirements.txt" ]; then \
        pip3 install --no-cache-dir -r ./vulscan/model_zoo/requirements.txt; \
    else \
        echo "Warning: requirements.txt not found"; \
    fi

# 更改文件所有权
RUN chown -R appuser:appgroup /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["./dual-shield"]