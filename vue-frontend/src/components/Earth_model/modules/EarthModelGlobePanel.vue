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
    
    if (globeInstance && typeof globeInstance.render === 'function') {
        const render = () => {
            globeInstance.render()
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

    const globeInstance = getGlobeInstance()

    if (globeInstance) {
        // 方法1：内置 resize 方法
        if (typeof globeInstance.resize === 'function') {
            globeInstance.resize(width, height)
        }
        // 方法2：手动调整相机和渲染器
        else if (globeInstance.camera && globeInstance.renderer) {
            globeInstance.camera.aspect = width / height
            globeInstance.camera.updateProjectionMatrix()
            globeInstance.renderer.setSize(width, height)
        }
        // 方法3：尝试 setSize 方法
        else if (typeof globeInstance.setSize === 'function') {
            globeInstance.setSize(width, height)
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
        const resizeObserver = new ResizeObserver(() => {
            handleResize()
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
    
    // 立即检查并启动渲染（不再延迟500ms）
    checkAndStartRender()
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

    .globe-wrapper {
        position: relative;
        width: 100%;
        height: 550px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        overflow: hidden;

        .earth {
            width: 100%;
            height: 100%;
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