<template>
    <div class="not-found-container">
        <div class="content-wrapper">
            <!-- 背景装饰 -->
            <div class="bg-decoration">
                <div class="circle circle-1"></div>
                <div class="circle circle-2"></div>
                <div class="circle circle-3"></div>
            </div>

            <!-- 主要内容 -->
            <div class="main-content">
                <!-- 404 数字 -->
                <div class="error-code">
                    <span class="code-4">4</span>
                    <span class="code-0">0</span>
                    <span class="code-4">4</span>
                </div>

                <!-- 标题和描述 -->
                <h1 class="title">页面未找到</h1>
                <p class="description">
                    抱歉，您访问的页面不存在或已被移除。
                    <br>
                    请检查URL是否正确，或返回首页。
                </p>

                <!-- 错误详情 -->
                <div class="error-details" v-if="errorPath">
                    <div class="detail-item">
                        <span class="label">访问路径：</span>
                        <span class="value">{{ errorPath }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">当前时间：</span>
                        <span class="value">{{ currentTime }}</span>
                    </div>
                </div>

                <!-- 操作按钮 -->
                <div class="actions">
                    <el-button type="primary" size="large" @click="goHome">
                        <el-icon><HomeFilled /></el-icon>
                        返回首页
                    </el-button>
                    <el-button size="large" @click="goBack">
                        <el-icon><ArrowLeft /></el-icon>
                        返回上一页
                    </el-button>
                </div>

                <!-- 快速链接 -->
                <div class="quick-links">
                    <span class="link-label">快速访问：</span>
                    <router-link to="/combined" class="quick-link">综合检测</router-link>
                    <router-link to="/phishing" class="quick-link">钓鱼检测</router-link>
                    <router-link to="/vulnerability" class="quick-link">漏洞检测</router-link>
                    <router-link to="/tasks" class="quick-link">任务列表</router-link>
                </div>
            </div>

            <!-- 右侧插图 -->
            <div class="illustration">
                <div class="shield-icon">
                    <el-icon><Lock /></el-icon>
                </div>
                <div class="question-marks">
                    <span class="q-mark q-1">?</span>
                    <span class="q-mark q-2">?</span>
                    <span class="q-mark q-3">?</span>
                </div>
            </div>
        </div>

        <!-- 底部信息 -->
        <div class="footer-info">
            <p>双擎智盾 v3.0 · 智能安全检测平台</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { HomeFilled, ArrowLeft, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const errorPath = computed(() => {
    return route.params.pathMatch || route.fullPath
})

const currentTime = computed(() => {
    return new Date().toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
})

const goHome = () => {
    router.push('/')
}

const goBack = () => {
    router.back()
}
</script>

<style lang="scss" scoped>
.not-found-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    position: relative;
    overflow: hidden;
}

.content-wrapper {
    display: flex;
    align-items: center;
    gap: 4rem;
    z-index: 1;
    max-width: 1200px;
    width: 100%;

    @media (max-width: 768px) {
        flex-direction: column;
        gap: 2rem;
        text-align: center;
    }
}

// 背景装饰
.bg-decoration {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    overflow: hidden;
    pointer-events: none;

    .circle {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);

        &.circle-1 {
            width: 400px;
            height: 400px;
            top: -100px;
            right: -100px;
            animation: float 6s ease-in-out infinite;
        }

        &.circle-2 {
            width: 300px;
            height: 300px;
            bottom: -50px;
            left: -50px;
            animation: float 8s ease-in-out infinite reverse;
        }

        &.circle-3 {
            width: 200px;
            height: 200px;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            animation: pulse 4s ease-in-out infinite;
        }
    }
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
}

@keyframes pulse {
    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
    50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.5; }
}

// 主要内容
.main-content {
    flex: 1;

    .error-code {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;

        @media (max-width: 768px) {
            justify-content: center;
        }

        span {
            font-size: 8rem;
            font-weight: 800;
            color: white;
            text-shadow: 4px 4px 0 rgba(0, 0, 0, 0.2);
            animation: bounce 2s ease-in-out infinite;

            &.code-0 {
                animation-delay: 0.1s;
            }

            @media (max-width: 768px) {
                font-size: 5rem;
            }
        }
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }

    .title {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;

        @media (max-width: 768px) {
            font-size: 1.75rem;
        }
    }

    .description {
        font-size: 1.125rem;
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.8;
        margin-bottom: 2rem;
    }

    .error-details {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 2rem;

        .detail-item {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;

            &:last-child {
                margin-bottom: 0;
            }

            .label {
                color: rgba(255, 255, 255, 0.7);
            }

            .value {
                color: white;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        }
    }

    .actions {
        display: flex;
        gap: 1rem;
        margin-bottom: 2rem;

        @media (max-width: 768px) {
            flex-direction: column;
        }

        .el-button {
            padding: 1rem 2rem;
            font-size: 1rem;
            border-radius: 50px;
            transition: all 0.3s ease;

            &:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            }
        }

        .el-button--primary {
            background: white;
            color: #667eea;
            border: none;

            &:hover {
                background: #f0f0f0;
            }
        }

        .el-button:not(.el-button--primary) {
            background: transparent;
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.5);

            &:hover {
                background: rgba(255, 255, 255, 0.1);
                border-color: white;
            }
        }
    }

    .quick-links {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;

        @media (max-width: 768px) {
            justify-content: center;
        }

        .link-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.875rem;
        }

        .quick-link {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
            font-size: 0.875rem;

            &:hover {
                background: rgba(255, 255, 255, 0.25);
                transform: translateY(-2px);
            }
        }
    }
}

// 右侧插图
.illustration {
    flex: 0 0 300px;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;

    @media (max-width: 768px) {
        flex: none;
    }

    .shield-icon {
        width: 200px;
        height: 200px;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(20px);
        border-radius: 40px;
        display: flex;
        justify-content: center;
        align-items: center;
        animation: float 4s ease-in-out infinite;

        .el-icon {
            font-size: 6rem;
            color: white;
        }
    }

    .question-marks {
        position: absolute;
        width: 100%;
        height: 100%;

        .q-mark {
            position: absolute;
            font-size: 3rem;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.5);
            animation: float 3s ease-in-out infinite;

            &.q-1 {
                top: 10%;
                right: 10%;
                animation-delay: 0.2s;
            }

            &.q-2 {
                bottom: 20%;
                left: 5%;
                animation-delay: 0.5s;
            }

            &.q-3 {
                top: 50%;
                right: -10%;
                animation-delay: 0.8s;
            }
        }
    }
}

// 底部信息
.footer-info {
    position: absolute;
    bottom: 2rem;
    text-align: center;

    p {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.875rem;
        margin: 0;
    }
}
</style>
