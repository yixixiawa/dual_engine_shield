# 微交互与骨架屏使用指南

## 📱 全局微交互增强

已在 `src/styles/global.scss` 中添加了以下全局交互效果：

### 1️⃣ 悬停反馈 (Hover Feedback)

所有可点击元素在鼠标悬停时都会自动应用：
- **位移效果**: `transform: translateY(-2px)` - 轻微上浮
- **亮度变化**: `filter: brightness(1.05)` - 光线增强
- **过渡时间**: `0.2s` - 平滑过渡

支持的元素类型：
- `button`, `.el-button` - 按钮
- `.el-card`, `[class*="card"]` - 卡片
- `.el-table tbody tr` - 表格行
- `.el-tag` - 标签
- 所有自定义 `[class*="panel"]`

```vue
<template>
  <!-- 所有这些元素都会自动获得悬停效果 -->
  <button>点击我</button>
  <el-card>卡片内容</el-card>
  <el-table>...</el-table>
  <div class="my-panel">自定义面板</div>
</template>

<style scoped>
/* 不需要额外样式，全局已配置 */
</style>
```

### 2️⃣ 平滑过渡 (Smooth Transitions)

- 所有交互元素已添加 `transition: all 0.2s ease`
- 展开/折叠动画: `transition: all 0.3s ease`
- 淡入淡出效果可用的类名:
  - `.fade-enter-active`, `.fade-leave-active`
  - `.collapse-enter-active`, `.collapse-leave-active`
  - `.slide-in-*-enter-active`, `.slide-in-*-leave-active`

```vue
<template>
  <transition name="fade">
    <div v-if="visible">淡入淡出效果</div>
  </transition>

  <transition name="slide-in-down">
    <div v-if="visible">从上滑入</div>
  </transition>

  <transition name="collapse">
    <div v-if="visible">折叠展开</div>
  </transition>
</template>
```

---

## 💀 骨架屏 (Skeleton Screen)

用灰色闪烁块代替加载旋转器，提升视觉质感。

### 使用方法

#### 基础用法

```vue
<template>
  <div>
    <!-- 列表骨架屏 (默认) -->
    <SkeletonLoader v-if="isLoading" type="list" :rows="3" />
    <div v-else>实际内容</div>

    <!-- 卡片骨架屏 -->
    <SkeletonLoader v-if="isLoading" type="card" />

    <!-- 表格骨架屏 -->
    <SkeletonLoader v-if="isLoading" type="table" :rows="5" :columns="4" />

    <!-- 网格骨架屏 -->
    <SkeletonLoader v-if="isLoading" type="grid" :rows="6" />

    <!-- 段落骨架屏 -->
    <SkeletonLoader v-if="isLoading" type="paragraph" :rows="4" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

const isLoading = ref(true)

// 模拟数据加载
setTimeout(() => {
  isLoading.value = false
}, 2000)
</script>
```

### 组件 Props

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `type` | string | `'list'` | 骨架屏类型: `list`, `card`, `table`, `grid`, `paragraph`, `text` |
| `rows` | number | `3` | 行数 |
| `columns` | number | `4` | 列数（仅table类型有效） |
| `size` | string | `'medium'` | 尺寸: `small`, `medium`, `large` |

### 骨架屏类型详解

#### 📋 List (列表骨架屏)
适用于列表、评论、消息等

```vue
<SkeletonLoader type="list" :rows="3" />
```

#### 📦 Card (卡片骨架屏)
适用于单个卡片、博客文章等

```vue
<SkeletonLoader type="card" />
```

#### 📊 Table (表格骨架屏)
适用于数据表格

```vue
<SkeletonLoader type="table" :rows="5" :columns="4" />
```

#### 🎲 Grid (网格骨架屏)
适用于产品网格、图片网格等

```vue
<SkeletonLoader type="grid" :rows="6" />
```

#### 📝 Paragraph (段落骨架屏)
适用于文章正文、描述等

```vue
<SkeletonLoader type="paragraph" :rows="4" />
```

#### 📄 Text (纯文本骨架屏)
适用于简单文本行

```vue
<SkeletonLoader type="text" :rows="3" />
```

### 实际应用示例

#### 钓鱼检测组件中的应用

```vue
<template>
  <div class="phishing-detection">
    <!-- 历史记录加载状态 -->
    <el-card v-if="isLoading" shadow="hover">
      <SkeletonLoader type="table" :rows="5" :columns="6" />
    </el-card>
    <el-card v-else shadow="hover">
      <HistoryTable :history="detectionStore.history" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import HistoryTable from './HistoryTable.vue'

const isLoading = ref(false)

const handleDetect = async (url) => {
  isLoading.value = true
  try {
    // 调用检测API
    await detectPhishing(url)
  } finally {
    isLoading.value = false
  }
}
</script>
```

#### 任务管理器中的应用

```vue
<template>
  <div class="task-manager">
    <!-- 统计卡片加载 -->
    <div class="stats-grid">
      <div v-if="isLoading" v-for="i in 4" :key="i">
        <SkeletonLoader type="card" size="small" />
      </div>
      <StatCard v-else v-for="stat in stats" :key="stat.label" :stat="stat" />
    </div>

    <!-- 表格加载 -->
    <el-card shadow="hover">
      <SkeletonLoader v-if="tasksLoading" type="table" :rows="5" :columns="7" />
      <el-table v-else :data="tasks" style="width: 100%">
        <!-- 表格列定义 -->
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ref } from 'vue'

const isLoading = ref(true)
const tasksLoading = ref(false)

onMounted(async () => {
  // 加载统计信息
  await loadStats()
  isLoading.value = false
})
</script>
```

---

## 🎨 样式自定义

### 骨架屏样式类

```scss
// 在组件中使用内置的骨架屏样式类
.skeleton {
  // 闪烁动画已内置
}

.skeleton-title {
  height: 24px;
  width: 60%;
}

.skeleton-text {
  height: 16px;
  
  &.small { height: 12px; }
  &.large { height: 20px; }
}

.skeleton-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}
```

### 全局动画类

```scss
// 已在全局样式中定义，可直接使用
.hover-lift {
  // 悬停上浮效果
}

.animate-fade-in {
  // 淡入动画
}
```

---

## 🔄 过渡动画速度指南

| 场景 | 推荐速度 | 类 |
|------|---------|-----|
| 按钮悬停 | `0.2s` | 所有按钮 |
| 卡片过渡 | `0.2s` | `.el-card` 等 |
| 面板展开 | `0.3s` | `.collapse-*` |
| 滑入滑出 | `0.3s` | `.slide-in-*` |
| 淡入淡出 | `0.2s` | `.fade-*` |

---

## 📱 响应式考虑

骨架屏组件已针对移动设备优化：

```vue
<!-- 自动适应屏幕尺寸 -->
<SkeletonLoader type="grid" :rows="isMobile ? 3 : 6" />

<!-- 表格在小屏幕下显示少列 -->
<SkeletonLoader 
  type="table" 
  :rows="5" 
  :columns="isMobile ? 2 : 4" 
/>
```

---

## 🚀 性能优化建议

1. **只在必要时显示骨架屏**
   ```vue
   <!-- ✅ 好做法 -->
   <SkeletonLoader v-if="!hasData && isLoading" />
   
   <!-- ❌ 避免 -->
   <SkeletonLoader v-if="isLoading" />
   <div v-if="hasData">内容</div>
   ```

2. **使用合适的骨架屏类型**
   - 匹配真实内容的布局
   - 避免过度装饰

3. **设置合理的加载超时**
   ```javascript
   const loadingTimeout = setTimeout(() => {
     isLoading.value = false
     showError.value = true
   }, 5000) // 5秒超时
   ```

---

## ✨ 最佳实践

### ✅ 推荐做法

```vue
<template>
  <div>
    <!-- 1. 使用合适的骨架屏类型 -->
    <SkeletonLoader v-if="loading" :type="contentType" />
    
    <!-- 2. 为用户提供反馈 -->
    <div v-if="error" class="error-message">
      加载失败，请重试
    </div>
    
    <!-- 3. 平滑过渡到实际内容 -->
    <transition name="fade">
      <div v-if="loaded">实际内容</div>
    </transition>
  </div>
</template>
```

### ❌ 避免做法

```vue
<!-- 不要混用加载器和骨架屏 -->
<el-loading v-if="loading" />
<SkeletonLoader v-if="loading" />

<!-- 不要显示太长时间的骨架屏 -->
<!-- 不要在网络快速时显示骨架屏 -->
```

---

## 📚 相关文件

- **全局样式**: [src/styles/global.scss](../styles/global.scss)
- **骨架屏组件**: [src/components/common/SkeletonLoader.vue](../components/common/SkeletonLoader.vue)
- **使用示例**:
  - [DetectionPanel.vue](../components/PhishingDetection/DetectionPanel.vue)
  - [TaskManager.vue](../components/TaskManager/TaskManager.vue)

