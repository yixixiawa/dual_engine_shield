<template>
    <el-card class="engine-card" shadow="hover" :class="`engine-${color}`">
        <div class="engine-header">
            <div class="engine-title">
                <div class="engine-dot" :class="`dot-${color}`"></div>
                <h3>{{ title }}</h3>
            </div>
            <span class="engine-score">{{ (score * 100).toFixed(1) }}%</span>
        </div>
        <p class="engine-desc">{{ description }}</p>
    </el-card>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
    title: string
    description: string
    score: number
    color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
}>(), {
    color: 'primary'
})
</script>

<style lang="scss" scoped>
.engine-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);
    transition: all 0.3s ease;

    &:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.15);
    }

    .engine-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;

        .engine-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;

            h3 {
                font-size: 1rem;
                font-weight: 600;
                margin: 0;
            }
        }

        .engine-score {
            font-size: 1.25rem;
            font-weight: 700;
            font-family: monospace;
        }
    }

    .engine-desc {
        font-size: 0.75rem;
        color: #6b7280;
        margin: 0;
    }

    .engine-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;

        &.dot-primary {
            background: #3b82f6;
        }

        &.dot-success {
            background: #10b981;
        }

        &.dot-warning {
            background: #f59e0b;
        }

        &.dot-danger {
            background: #ef4444;
        }

        &.dot-info {
            background: #8b5cf6;
        }
    }
}

.engine-primary .engine-score {
    color: #3b82f6;
}

.engine-success .engine-score {
    color: #10b981;
}

.engine-warning .engine-score {
    color: #f59e0b;
}

.engine-danger .engine-score {
    color: #ef4444;
}

.engine-info .engine-score {
    color: #8b5cf6;
}
</style>