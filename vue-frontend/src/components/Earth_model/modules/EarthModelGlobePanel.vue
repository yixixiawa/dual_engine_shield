<template>
    <div class="middle-section">
        <div class="globe-wrapper">
            <div ref="earthContainerRef" class="earth" :id="GLOBE_CONTAINER_ID"></div>
            <div v-if="loading" class="loading-container">
                <el-skeleton :rows="1" animated style="width: 100%; height: 100%" />
                <div class="loading-text">加载地球模型中...</div>
            </div>
            <div class="mode-indicator">当前模式：{{ displayMode === '3d' ? '3D 地球' : '2D 平面图' }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const GLOBE_CONTAINER_ID = 'globeContainer'

defineProps<{
    displayMode: '2d' | '3d'
    loading?: boolean
}>()

const animationFrameId = ref<number | null>(null)
const earthContainerRef = ref<HTMLElement | null>(null)

let resizeObserver: ResizeObserver | null = null
let resizeFrameId: number | null = null

const getContainer = () => earthContainerRef.value || document.getElementById(GLOBE_CONTAINER_ID)

const getGlobeInstance = (): any => {
    const container = getContainer()
    if (!container) return null

    return (window as any).__globeInstance ||
        (container as any).__globeInstance ||
        (container as any).earthFlyLine ||
        (container.firstElementChild as any)?.__globeInstance
}

const getReadyContainer = () => {
    const container = getContainer()
    if (!container) return null

    if (container.clientWidth <= 0 || container.clientHeight <= 0) {
        return null
    }

    return container
}

const waitForReadyContainer = async (maxAttempts = 30, delay = 100): Promise<HTMLElement | null> => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        await nextTick()

        const container = getReadyContainer()
        if (container) return container

        await new Promise(resolve => setTimeout(resolve, delay))
    }

    return null
}

const stopRenderLoop = () => {
    if (animationFrameId.value !== null) {
        cancelAnimationFrame(animationFrameId.value)
        animationFrameId.value = null
    }
}

const handleResize = () => {
    const container = getReadyContainer()
    if (!container) return

    const width = container.clientWidth
    const height = container.clientHeight
    const globeInstance = getGlobeInstance()

    if (globeInstance) {
        if (typeof globeInstance.resize === 'function') {
            globeInstance.resize(width, height)
        } else if (globeInstance.camera && globeInstance.renderer) {
            globeInstance.camera.aspect = width / height
            globeInstance.camera.updateProjectionMatrix()
            globeInstance.renderer.setSize(width, height)

            if (globeInstance.renderer.setPixelRatio) {
                globeInstance.renderer.setPixelRatio(window.devicePixelRatio)
            }
        } else if (typeof globeInstance.setSize === 'function') {
            globeInstance.setSize(width, height)
        } else if (globeInstance._renderer) {
            if (globeInstance._camera) {
                globeInstance._camera.aspect = width / height
                globeInstance._camera.updateProjectionMatrix()
            }

            globeInstance._renderer.setSize(width, height)

            if (globeInstance._renderer.setPixelRatio) {
                globeInstance._renderer.setPixelRatio(window.devicePixelRatio)
            }
        }

        if (typeof globeInstance.render === 'function') {
            globeInstance.render()
        }
    }

    const canvas = container.querySelector('canvas')
    if (canvas) {
        canvas.width = width * window.devicePixelRatio
        canvas.height = height * window.devicePixelRatio
        canvas.style.width = `${width}px`
        canvas.style.height = `${height}px`
    }
}

const scheduleResize = () => {
    if (resizeFrameId !== null) return

    resizeFrameId = requestAnimationFrame(() => {
        resizeFrameId = null
        handleResize()
    })
}

const startRenderLoop = () => {
    stopRenderLoop()

    const globeInstance = getGlobeInstance()
    if (!globeInstance || typeof globeInstance.render !== 'function') return

    let frameCount = 0

    const render = () => {
        globeInstance.render()

        frameCount++
        if (frameCount % 30 === 0) {
            const container = getReadyContainer()
            const canvas = container?.querySelector('canvas')

            if (container && canvas) {
                const canvasWidth = canvas.width / window.devicePixelRatio
                const canvasHeight = canvas.height / window.devicePixelRatio

                if (
                    Math.abs(canvasWidth - container.clientWidth) > 1 ||
                    Math.abs(canvasHeight - container.clientHeight) > 1
                ) {
                    scheduleResize()
                }
            }
        }

        animationFrameId.value = requestAnimationFrame(render)
    }

    render()
}

onMounted(() => {
    const container = getContainer()

    if (container && typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect
                if (width > 0 && height > 0) {
                    scheduleResize()
                }
            }
        })
        resizeObserver.observe(container)
    }

    window.addEventListener('resize', scheduleResize)
})

onBeforeUnmount(() => {
    if (resizeFrameId !== null) {
        cancelAnimationFrame(resizeFrameId)
        resizeFrameId = null
    }

    resizeObserver?.disconnect()
    resizeObserver = null
    window.removeEventListener('resize', scheduleResize)
    stopRenderLoop()
})

defineExpose({
    handleResize,
    waitForReadyContainer,
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
            z-index: 3;
        }

        .loading-container {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #f5f7fa;
            z-index: 2;
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
