<template>
  <div class="skeleton-loader" :class="[`skeleton-${type}`, `skeleton-${size}`]">
    <!-- 列表骨架屏 -->
    <template v-if="type === 'list'">
      <div v-for="index in rows" :key="index" class="skeleton-item">
        <div class="skeleton skeleton-avatar"></div>
        <div class="skeleton-content">
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-text"></div>
          <div class="skeleton skeleton-text small"></div>
        </div>
      </div>
    </template>

    <!-- 卡片骨架屏 -->
    <template v-else-if="type === 'card'">
      <div class="skeleton-card-wrapper">
        <div class="skeleton skeleton-title" style="width: 80%"></div>
        <div class="skeleton-content">
          <div v-for="index in 3" :key="index" class="skeleton skeleton-text"></div>
        </div>
        <div class="skeleton-footer">
          <div class="skeleton" style="width: 60px; height: 32px; border-radius: 4px;"></div>
          <div class="skeleton" style="width: 80px; height: 32px; border-radius: 4px;"></div>
        </div>
      </div>
    </template>

    <!-- 表格骨架屏 -->
    <template v-else-if="type === 'table'">
      <div class="skeleton-table-wrapper">
        <!-- 表头 -->
        <div class="skeleton-table-header">
          <div v-for="col in columns" :key="col" class="skeleton-cell">
            <div class="skeleton skeleton-text" :style="{ width: '100%' }"></div>
          </div>
        </div>
        <!-- 行 -->
        <div v-for="row in rows" :key="row" class="skeleton-table-row">
          <div v-for="col in columns" :key="`${row}-${col}`" class="skeleton-cell">
            <div class="skeleton skeleton-text"></div>
          </div>
        </div>
      </div>
    </template>

    <!-- 网格骨架屏 -->
    <template v-else-if="type === 'grid'">
      <div class="skeleton-grid-wrapper">
        <div v-for="index in rows" :key="index" class="skeleton skeleton-card"></div>
      </div>
    </template>

    <!-- 段落骨架屏 -->
    <template v-else-if="type === 'paragraph'">
      <div class="skeleton-paragraph-wrapper">
        <div class="skeleton skeleton-title"></div>
        <div v-for="index in rows" :key="index" class="skeleton skeleton-text"></div>
      </div>
    </template>

    <!-- 文本骨架屏 -->
    <template v-else>
      <div v-for="index in rows" :key="index" class="skeleton skeleton-text"></div>
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  type?: 'list' | 'card' | 'table' | 'grid' | 'paragraph' | 'text'
  rows?: number
  columns?: number
  size?: 'small' | 'medium' | 'large'
}>(), {
  type: 'list',
  rows: 3,
  columns: 4,
  size: 'medium'
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.skeleton-loader {
  width: 100%;
}

// 骨架屏动画
@keyframes skeleton-loading {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

// 通用骨架块
.skeleton {
  background: linear-gradient(90deg, 
    #e5e7eb 25%, 
    #f3f4f6 50%, 
    #e5e7eb 75%);
  background-size: 1000px 100%;
  animation: skeleton-loading 2s infinite;
  border-radius: 4px;
}

// 列表类型
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .skeleton-item {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 12px;
    background: white;
    border-radius: 8px;
    border: 1px solid rgba(79, 70, 229, 0.1);

    .skeleton-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .skeleton-content {
      flex: 1;

      .skeleton-title {
        height: 18px;
        margin-bottom: 8px;
        width: 70%;
      }

      .skeleton-text {
        height: 14px;
        margin-bottom: 6px;

        &.small {
          height: 12px;
          width: 50%;
        }

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }
}

// 卡片类型
.skeleton-card {
  .skeleton-card-wrapper {
    background: white;
    border-radius: 8px;
    padding: 16px;
    border: 1px solid rgba(79, 70, 229, 0.1);

    .skeleton-title {
      height: 24px;
      margin-bottom: 12px;
    }

    .skeleton-content {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 16px;

      .skeleton-text {
        height: 16px;

        &:last-child {
          width: 80%;
        }
      }
    }

    .skeleton-footer {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
    }
  }
}

// 表格类型
.skeleton-table {
  .skeleton-table-wrapper {
    border: 1px solid rgba(79, 70, 229, 0.1);
    border-radius: 8px;
    overflow: hidden;

    .skeleton-table-header {
      display: grid;
      grid-template-columns: repeat(v-bind(columns), 1fr);
      gap: 0;
      padding: 12px;
      background: rgba(79, 70, 229, 0.05);
      border-bottom: 1px solid rgba(79, 70, 229, 0.1);

      .skeleton-cell {
        padding: 8px;

        .skeleton-text {
          height: 16px;
        }
      }
    }

    .skeleton-table-row {
      display: grid;
      grid-template-columns: repeat(v-bind(columns), 1fr);
      gap: 0;
      padding: 12px;
      border-bottom: 1px solid rgba(79, 70, 229, 0.1);

      &:last-child {
        border-bottom: none;
      }

      .skeleton-cell {
        padding: 8px;

        .skeleton-text {
          height: 14px;
        }
      }
    }
  }
}

// 网格类型
.skeleton-grid {
  .skeleton-grid-wrapper {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;

    .skeleton-card {
      height: 160px;
    }
  }
}

// 段落类型
.skeleton-paragraph {
  .skeleton-paragraph-wrapper {
    .skeleton-title {
      height: 24px;
      margin-bottom: 16px;
      width: 60%;
    }

    .skeleton-text {
      height: 14px;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}

// 尺寸变体
.skeleton-small {
  .skeleton-title {
    height: 16px;
  }

  .skeleton-text {
    height: 12px;
  }

  .skeleton-item {
    padding: 8px !important;

    .skeleton-avatar {
      width: 32px;
      height: 32px;
    }
  }
}

.skeleton-large {
  .skeleton-title {
    height: 32px;
  }

  .skeleton-text {
    height: 18px;
  }

  .skeleton-item {
    padding: 16px !important;

    .skeleton-avatar {
      width: 48px;
      height: 48px;
    }
  }
}
</style>
