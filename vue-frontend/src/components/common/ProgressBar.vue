<template>
    <div class="progress-bar-container" :class="{ 'show-label': showLabel }">
        <div v-if="showLabel" class="progress-header">
            <span class="progress-title">{{ title }}</span>
            <span class="progress-percentage">{{ percentage }}%</span>
        </div>

        <div class="progress-track" :style="trackStyle">
            <div class="progress-fill" :style="fillStyle" :class="[
                `progress-${type}`,
                { 'striped': striped, 'animated': animated }
            ]">
                <span v-if="showInnerLabel && percentage > 15" class="inner-label">
                    {{ percentage }}%
                </span>
            </div>
        </div>

        <div v-if="showStatus" class="progress-status">
            <span v-if="status" class="status-text">{{ status }}</span>
            <span v-if="showTime && duration > 0" class="duration-text">
                <el-icon>
                    <Timer />
                </el-icon>
                {{ formatDuration(duration) }}
            </span>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
    percentage: number
    title?: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    status?: string
    showLabel?: boolean
    showInnerLabel?: boolean
    showStatus?: boolean
    showTime?: boolean
    duration?: number
    striped?: boolean
    animated?: boolean
    height?: number
    color?: string
}>(), {
    title: '',
    type: 'primary',
    status: '',
    showLabel: true,
    showInnerLabel: false,
    showStatus: false,
    showTime: false,
    duration: 0,
    striped: false,
    animated: false,
    height: 8,
    color: ''
})

const trackStyle = computed(() => ({
    height: `${props.height}px`,
    borderRadius: `${props.height / 2}px`
}))

const fillStyle = computed(() => {
    const width = Math.min(Math.max(props.percentage, 0), 100)
    const styles: Record<string, string> = {
        width: `${width}%`
    }

    if (props.color) {
        styles.backgroundColor = props.color
        styles.backgroundImage = 'none'
    }

    return styles
})

const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    const seconds = ms / 1000
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainSeconds = (seconds % 60).toFixed(0)
    return `${minutes}m ${remainSeconds}s`
}
</script>

<style lang="scss" scoped>
.progress-bar-container {
    width: 100%;

    &.show-label {
        .progress-track {
            margin-top: 0.25rem;
        }
    }

    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.875rem;
        margin-bottom: 0.25rem;

        .progress-title {
            color: #374151;
            font-weight: 500;
        }

        .progress-percentage {
            color: #6b7280;
            font-family: monospace;
            font-weight: 600;
        }
    }

    .progress-track {
        background: #e5e7eb;
        border-radius: 9999px;
        overflow: hidden;
        position: relative;
    }

    .progress-fill {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding-right: 0.5rem;

        &.progress-primary {
            background: linear-gradient(90deg, #3b82f6, #60a5fa);
        }

        &.progress-success {
            background: linear-gradient(90deg, #10b981, #34d399);
        }

        &.progress-warning {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
        }

        &.progress-danger {
            background: linear-gradient(90deg, #ef4444, #f87171);
        }

        &.progress-info {
            background: linear-gradient(90deg, #8b5cf6, #a78bfa);
        }

        &.striped {
            background-size: 40px 40px;
            background-image: linear-gradient(45deg,
                    rgba(255, 255, 255, 0.15) 25%,
                    transparent 25%,
                    transparent 50%,
                    rgba(255, 255, 255, 0.15) 50%,
                    rgba(255, 255, 255, 0.15) 75%,
                    transparent 75%,
                    transparent);

            &.animated {
                animation: progress-stripes 1s linear infinite;
            }
        }

        .inner-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
        }
    }

    .progress-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
        font-size: 0.75rem;

        .status-text {
            color: #6b7280;
        }

        .duration-text {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            color: #9ca3af;
        }
    }
}

@keyframes progress-stripes {
    from {
        background-position: 40px 0;
    }

    to {
        background-position: 0 0;
    }
}
</style>