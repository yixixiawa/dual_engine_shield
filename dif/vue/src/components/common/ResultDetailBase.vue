<template>
  <div class="result-detail-container">
    <!-- 头部：结果摘要 -->
    <div class="result-header">
      <div class="header-left">
        <div :class="['status-badge', statusClass]">
          {{ statusLabel }}
        </div>
        <div class="header-info">
          <h3>{{ title }}</h3>
          <p class="timestamp">{{ formatTime(timestamp) }}</p>
        </div>
      </div>
      <div class="header-right">
        <div v-if="severity" :class="['severity-badge', severityClass]">
          {{ severityLabel }}
        </div>
      </div>
    </div>

    <!-- 基础信息 -->
    <div class="basic-info">
      <div v-for="(item, key) in basicInfo" :key="key" class="info-item">
        <span class="info-label">{{ item.label }}:</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </div>

    <!-- 详细内容（Tab切换） -->
    <div v-if="tabs.length > 0" class="details-section">
      <div class="tab-buttons">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 内容 -->
      <div class="tab-content">
        <!-- 代码片段 -->
        <div v-if="activeTab === 'code'" class="code-section">
          <pre><code>{{ codeSnippet }}</code></pre>
        </div>

        <!-- 原因分析 -->
        <div v-if="activeTab === 'reason'" class="reason-section">
          <p>{{ reason }}</p>
        </div>

        <!-- 详细数据 -->
        <div v-if="activeTab === 'details'" class="details-data">
          <div v-for="(value, key) in detailedData" :key="key" class="detail-item">
            <span class="detail-label">{{ formatLabel(key) }}:</span>
            <span class="detail-value">{{ formatValue(value) }}</span>
          </div>
        </div>

        <!-- 自定义内容 -->
        <slot v-if="activeTab === 'custom'" name="custom-content"></slot>
      </div>
    </div>

    <!-- 标签 -->
    <div v-if="tags.length > 0" class="tags-section">
      <span v-for="tag in tags" :key="tag" class="tag">{{ tag }}</span>
    </div>

    <!-- 操作按钮 -->
    <div v-if="actions.length > 0" class="actions-section">
      <button
        v-for="action in actions"
        :key="action.id"
        :class="['action-btn', action.type]"
        @click="$emit('action', action.id)"
      >
        {{ action.label }}
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import type { PropType } from 'vue';

export interface TabConfig {
  id: string;
  label: string;
  content?: string;
}

export interface ActionConfig {
  id: string;
  label: string;
  type?: 'primary' | 'danger' | 'default';
}

export interface BasicInfoItem {
  label: string;
  value: any;
}

export default defineComponent({
  name: 'ResultDetail',
  props: {
    // 标题
    title: {
      type: String,
      required: true,
    },
    // 状态（vulnerable, safe, suspicious, etc）
    status: {
      type: String,
      required: true,
    },
    // 严重等级
    severity: {
      type: String,
      default: null, // 'critical', 'high', 'medium', 'low'
    },
    // 时间戳
    timestamp: {
      type: [Number, String, Date],
      default: () => new Date(),
    },
    // 基础信息（显示在头部下方）
    basicInfo: {
      type: Object as PropType<Record<string, BasicInfoItem>>,
      default: () => ({}),
    },
    // 代码片段
    codeSnippet: {
      type: String,
      default: '',
    },
    // 原因描述
    reason: {
      type: String,
      default: '',
    },
    // 详细数据
    detailedData: {
      type: Object as PropType<Record<string, any>>,
      default: () => ({}),
    },
    // Tabs配置
    tabs: {
      type: Array as PropType<TabConfig[]>,
      default: () => [
        { id: 'details', label: '详情' },
        { id: 'reason', label: '原因' },
      ],
    },
    // 标签
    tags: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
    // 操作按钮
    actions: {
      type: Array as PropType<ActionConfig[]>,
      default: () => [],
    },
    // 状态颜色映射
    statusColorMap: {
      type: Object as PropType<Record<string, string>>,
      default: () => ({
        vulnerable: 'danger',
        safe: 'success',
        suspicious: 'warning',
      }),
    },
    // 严重等级颜色映射
    severityColorMap: {
      type: Object as PropType<Record<string, string>>,
      default: () => ({
        critical: 'danger',
        high: 'danger',
        medium: 'warning',
        low: 'success',
      }),
    },
  },
  emits: ['action'],
  data() {
    return {
      activeTab: 'details' as string,
    };
  },
  computed: {
    statusClass(): string {
      return this.statusColorMap[this.status?.toLowerCase()] || 'default';
    },
    statusLabel(): string {
      return this.formatLabel(this.status);
    },
    severityClass(): string {
      return this.severity ? this.severityColorMap[this.severity?.toLowerCase()] || 'default' : '';
    },
    severityLabel(): string {
      return this.severity ? this.formatLabel(this.severity) : '';
    },
  },
  methods: {
    formatTime(time: number | string | Date): string {
      const date = typeof time === 'string' || typeof time === 'number' ? new Date(time) : time;
      return date.toLocaleString();
    },
    formatLabel(label: string): string {
      return label
        .replace(/_/g, ' ')
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/^./, (char) => char.toUpperCase());
    },
    formatValue(value: any): string {
      if (typeof value === 'object') {
        return JSON.stringify(value, null, 2);
      }
      return String(value);
    },
  },
});
</script>

<style scoped lang="scss">
.result-detail-container {
  background: #fff;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      .status-badge {
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;

        &.danger {
          background: #ff4d4f;
          color: #fff;
        }

        &.success {
          background: #52c41a;
          color: #fff;
        }

        &.warning {
          background: #faad14;
          color: #fff;
        }

        &.default {
          background: #d9d9d9;
          color: #000;
        }
      }

      .header-info {
        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .timestamp {
          margin: 4px 0 0;
          color: #999;
          font-size: 12px;
        }
      }
    }

    .header-right {
      .severity-badge {
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 12px;

        &.danger {
          background: #ff4d4f;
          color: #fff;
        }

        &.warning {
          background: #faad14;
          color: #fff;
        }

        &.success {
          background: #52c41a;
          color: #fff;
        }

        &.default {
          background: #d9d9d9;
          color: #000;
        }
      }
    }
  }

  .basic-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    margin-bottom: 24px;

    .info-item {
      .info-label {
        font-weight: 600;
        color: #333;
        margin-right: 8px;
      }

      .info-value {
        color: #666;
      }
    }
  }

  .details-section {
    margin-bottom: 24px;

    .tab-buttons {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      border-bottom: 2px solid #f0f0f0;

      .tab-button {
        padding: 8px 16px;
        background: none;
        border: none;
        cursor: pointer;
        color: #666;
        font-weight: 500;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        transition: all 0.3s;

        &:hover {
          color: #1890ff;
        }

        &.active {
          color: #1890ff;
          border-bottom-color: #1890ff;
        }
      }
    }

    .tab-content {
      padding: 16px;
      background: #fafafa;
      border-radius: 4px;

      .code-section {
        pre {
          margin: 0;
          overflow-x: auto;
          background: #f5f5f5;
          padding: 12px;
          border-radius: 4px;
          font-size: 12px;
          line-height: 1.5;

          code {
            font-family: 'Courier New', monospace;
          }
        }
      }

      .reason-section {
        line-height: 1.6;
        color: #333;

        p {
          margin: 0;
        }
      }

      .details-data {
        .detail-item {
          display: flex;
          margin-bottom: 12px;

          .detail-label {
            font-weight: 600;
            color: #333;
            min-width: 150px;
          }

          .detail-value {
            color: #666;
            word-break: break-all;
          }
        }
      }
    }
  }

  .tags-section {
    margin-bottom: 24px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;

    .tag {
      padding: 4px 12px;
      background: #f0f0f0;
      border-radius: 4px;
      font-size: 12px;
      color: #333;
    }
  }

  .actions-section {
    display: flex;
    gap: 8px;

    .action-btn {
      padding: 8px 16px;
      border-radius: 4px;
      border: 1px solid transparent;
      cursor: pointer;
      font-weight: 500;
      transition: all 0.3s;

      &.primary {
        background: #1890ff;
        color: #fff;

        &:hover {
          background: #40a9ff;
        }
      }

      &.danger {
        background: #ff4d4f;
        color: #fff;

        &:hover {
          background: #ff7875;
        }
      }

      &.default {
        background: #f0f0f0;
        color: #333;

        &:hover {
          background: #e0e0e0;
        }
      }
    }
  }
}
</style>
