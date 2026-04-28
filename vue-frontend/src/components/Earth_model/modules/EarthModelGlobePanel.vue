<template>
    <div class="middle-section">
        <div class="globe-wrapper">
            <div v-if="loading" class="loading-container">
                <el-skeleton :rows="1" animated style="width: 100%; height: 100%" />
                <div class="loading-text">加载地球模型中...</div>
            </div>
            <div v-else class="earth" :id="GLOBE_CONTAINER_ID"></div>
            <div class="mode-indicator">当前模式：{{ displayMode === '3d' ? '3D 地球' : '2D 平面图' }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, nextTick, ref } from 'vue'

const GLOBE_CONTAINER_ID = 'globeContainer'

const props = defineProps<{
    displayMode: '2d' | '3d'
    loading?: boolean
}>()

const animationFrameId = ref<number | null>(null)

// 获取 globe 实例的辅助函数
const getGlobeInstance = (): any => {
    const container = document.getElementById(GLOBE_CONTAINER_ID)
    if (!container) return null
    
    // 尝试多种方式获取 globe 实例
    return (window as any).__globeInstance || 
           (container as any).__globeInstance || 
           (container as any).earthFlyLine ||
           (container.firstElementChild as any)?.__globeInstance
}

// 持续渲染函数（解决“无法继续渲染”问题）
const startRenderLoop = () => {
    const globeInstance = getGlobeInstance()
    let frameCount = 0
    
    if (globeInstance && typeof globeInstance.render === 'function') {
        const render = () => {
            globeInstance.render()
            
            // 每30帧检查一次canvas尺寸，确保不会被拉伸
            frameCount++
            if (frameCount % 30 === 0) {
                const container = document.getElementById(GLOBE_CONTAINER_ID)
                if (container) {
                    const canvas = container.querySelector('canvas')
                    if (canvas) {
                        const containerWidth = container.clientWidth
                        const containerHeight = container.clientHeight
                        const canvasWidth = canvas.width / window.devicePixelRatio
                        const canvasHeight = canvas.height / window.devicePixelRatio
                        
                        // 如果canvas尺寸与容器不匹配，重新调整
                        if (Math.abs(canvasWidth - containerWidth) > 1 || 
                            Math.abs(canvasHeight - containerHeight) > 1) {
                            handleResize()
                        }
                    }
                }
            }
            
            animationFrameId.value = requestAnimationFrame(render)
        }
        render()
    }
}

const stopRenderLoop = () => {
    if (animationFrameId.value) {
        cancelAnimationFrame(animationFrameId.value)
        animationFrameId.value = null
    }
}

// 暴露给父组件调用的 resize 方法
const handleResize = () => {
    const container = document.getElementById(GLOBE_CONTAINER_ID)
    if (!container) return

    const width = container.clientWidth
    const height = container.clientHeight

    // 确保尺寸有效
    if (width <= 0 || height <= 0) return

    const globeInstance = getGlobeInstance()

    if (globeInstance) {
        // 方法1：内置 resize 方法（earth-flyline 库可能有此方法）
        if (typeof globeInstance.resize === 'function') {
            globeInstance.resize(width, height)
        }
        // 方法2：手动调整相机和渲染器（Three.js 风格）
        else if (globeInstance.camera && globeInstance.renderer) {
            globeInstance.camera.aspect = width / height
            globeInstance.camera.updateProjectionMatrix()
            globeInstance.renderer.setSize(width, height)
            // 同步更新渲染器的像素比以支持高分辨率屏幕
            if (globeInstance.renderer.setPixelRatio) {
                globeInstance.renderer.setPixelRatio(window.devicePixelRatio)
            }
        }
        // 方法3：尝试 setSize 方法
        else if (typeof globeInstance.setSize === 'function') {
            globeInstance.setSize(width, height)
        }
        // 方法4：尝试获取内部的 renderer 对象
        else if (globeInstance._renderer) {
            if (globeInstance._camera) {
                globeInstance._camera.aspect = width / height
                globeInstance._camera.updateProjectionMatrix()
            }
            globeInstance._renderer.setSize(width, height)
            if (globeInstance._renderer.setPixelRatio) {
                globeInstance._renderer.setPixelRatio(window.devicePixelRatio)
            }
        }
        // 方法5：尝试 canvas 元素直接设置尺寸
        else {
            const canvas = container.querySelector('canvas')
            if (canvas) {
                canvas.width = width * window.devicePixelRatio
                canvas.height = height * window.devicePixelRatio
                canvas.style.width = `${width}px`
                canvas.style.height = `${height}px`
            }
        }
        
        // 触发重绘 - 关键修复：resize 后必须调用 render()
        if (typeof globeInstance.render === 'function') {
            globeInstance.render()
        }
    }
}

// 检查 globe 是否已初始化并启动渲染
const checkAndStartRender = () => {
    const globeInstance = getGlobeInstance()
    if (globeInstance) {
        // 启动渲染循环
        startRenderLoop()
        // 立即触发一次 resize 确保尺寸正确
        handleResize()
    } else {
        // 继续尝试，最多尝试10次
        const attempts = ref(0)
        const tryAgain = () => {
            attempts.value++
            const instance = getGlobeInstance()
            if (instance && attempts.value <= 10) {
                startRenderLoop()
                handleResize()
            } else if (attempts.value <= 10) {
                setTimeout(tryAgain, 100)
            }
        }
        tryAgain()
    }
}

// 监听 displayMode 变化
watch(() => props.displayMode, async () => {
    await nextTick()
    // 模式切换后延迟一点再 resize，确保 DOM 已更新
    setTimeout(() => {
        handleResize()
        // 模式切换后重新启动渲染循环
        stopRenderLoop()
        startRenderLoop()
    }, 100)
})

onMounted(() => {
    const container = document.getElementById(GLOBE_CONTAINER_ID)
    if (container) {
        // 使用 ResizeObserver 监听容器大小变化（比 window resize 更精准）
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect
                if (width > 0 && height > 0) {
                    handleResize()
                }
            }
        })
        resizeObserver.observe(container)
        
        // 备用：监听窗口 resize
        window.addEventListener('resize', handleResize)
        
        // 组件卸载时清理
        onBeforeUnmount(() => {
            resizeObserver.disconnect()
            window.removeEventListener('resize', handleResize)
        })
    }
    
    // 立即检查并启动渲染（带延迟，确保父组件有时间初始化 globe）
    setTimeout(checkAndStartRender, 100)
    
    // 额外的安全检查：再延迟一段时间后再次尝试
    setTimeout(() => {
        const globeInstance = getGlobeInstance()
        if (!globeInstance) {
            console.warn('[GlobePanel] globeInstance 仍未初始化，可能需要检查')
        } else if (animationFrameId.value === null) {
            // 如果渲染循环还没启动，启动它
            startRenderLoop()
        }
    }, 500)
})

onBeforeUnmount(() => {
    stopRenderLoop()
})

// 将方法暴露给父组件
defineExpose({
    handleResize,
    startRenderLoop,
    stopRenderLoop
})
</script>

<style scoped lang="scss">
.middle-section {
    width: 100%;
    min-height: 0;

    .globe-wrapper {
        position: relative;
        width: 100%;
        height: 550px;
        min-height: 400px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        overflow: hidden;
        display: flex;
        flex-direction: column;

        .earth {
            width: 100%;
            height: 100%;
            flex: 1;
            min-height: 0;
        }

        .mode-indicator {
            position: absolute;
            top: 16px;
            right: 16px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.9);
            color: #606266;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            pointer-events: none;
        }

        .loading-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #f5f7fa;
        }

        .loading-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #606266;
            font-size: 14px;
            margin-top: 40px;
        }
    }
}

@media (max-width: 768px) {
    .middle-section .globe-wrapper {
        height: 350px;
    }
}
</style>