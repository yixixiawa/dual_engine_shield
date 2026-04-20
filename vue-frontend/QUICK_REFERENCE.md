# 微交互快速参考卡

## 🎯 一页纸速查表

### 骨架屏类型速查

```vue
<!-- 列表骨架 (默认) -->
<SkeletonLoader type="list" :rows="3" />

<!-- 卡片骨架 -->
<SkeletonLoader type="card" />

<!-- 表格骨架 -->
<SkeletonLoader type="table" :rows="5" :columns="4" />

<!-- 网格骨架 -->
<SkeletonLoader type="grid" :rows="6" />

<!-- 段落骨架 -->
<SkeletonLoader type="paragraph" :rows="4" />

<!-- 文本骨架 -->
<SkeletonLoader type="text" :rows="3" />
```

### 全局动画类速查

```vue
<!-- 淡入淡出 -->
<transition name="fade">
  <div v-if="show">内容</div>
</transition>

<!-- 上下滑入 -->
<transition name="slide-in-down">
  <div v-if="show">从上方滑入</div>
</transition>

<!-- 下上滑入 -->
<transition name="slide-in-up">
  <div v-if="show">从下方滑入</div>
</transition>

<!-- 左右滑入 -->
<transition name="slide-in-left">
  <div v-if="show">从左侧滑入</div>
</transition>

<transition name="slide-in-right">
  <div v-if="show">从右侧滑入</div>
</transition>

<!-- 折叠展开 -->
<transition name="collapse">
  <div v-if="show">展开折叠</div>
</transition>
```

### 自动启用的悬停效果

| 元素 | 效果 |
|------|------|
| `button`, `.el-button` | ⬆️ 上浮 + 变亮 + 平滑过渡 |
| `.el-card` 等卡片 | ⬆️ 上浮 + 阴影 + 边框变色 |
| `.el-table tbody tr` | ⬆️ 轻微上浮 + 背景变色 |
| `.el-tag` | 🔍 缩放 + 阴影 |
| `input`, `.el-input` | ✨ 聚焦时发光 |

### 过渡时间标准

```scss
// 快速反馈（推荐用于小元素）
transition: all 0.2s ease;  // 按钮、标签等

// 标准过渡（推荐用于中等元素）
transition: all 0.3s ease;  // 面板、卡片展开等

// 缓慢过渡（避免使用）
transition: all 0.5s ease;  // 通常太慢
```

### 骨架屏属性

```typescript
interface SkeletonLoaderProps {
  type?: 'list' | 'card' | 'table' | 'grid' | 'paragraph' | 'text'  // 类型
  rows?: number        // 行数 (default: 3)
  columns?: number     // 列数，仅 table 有效 (default: 4)
  size?: 'small' | 'medium' | 'large'  // 尺寸 (default: 'medium')
}
```

### 常见用例

#### 1. 列表页面
```vue
<el-card v-if="loading" shadow="hover">
  <SkeletonLoader type="list" :rows="5" />
</el-card>
<el-card v-else shadow="hover">
  <el-table :data="items"><!-- ... --></el-table>
</el-card>
```

#### 2. 详情页面
```vue
<el-card v-if="loading" shadow="hover">
  <SkeletonLoader type="card" />
</el-card>
<div v-else><!-- 详情内容 --></div>
```

#### 3. 网格页面
```vue
<div v-if="loading" class="grid-container">
  <SkeletonLoader type="grid" :rows="6" />
</div>
<div v-else class="grid-container">
  <!-- 网格内容 -->
</div>
```

#### 4. 表格页面
```vue
<el-card v-if="loading" shadow="hover">
  <SkeletonLoader type="table" :rows="5" :columns="6" />
</el-card>
<el-card v-else shadow="hover">
  <el-table :data="tableData"><!-- ... --></el-table>
</el-card>
```

### 颜色和动画变量

```scss
// 主要颜色
$primary: #4f46e5;           // 主紫色
$secondary: #0ea5e9;         // 主蓝色
$success: #10b981;           // 成功绿
$warning: #f59e0b;           // 警告黄
$danger: #ef4444;            // 危险红

// 动画时间
$transition-fast: 0.2s ease;   // 按钮
$transition-normal: 0.3s ease; // 面板
$transition-slow: 0.5s ease;   // 避免使用
```

### 导入骨架屏组件

```vue
<script setup lang="ts">
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
</script>

<template>
  <SkeletonLoader type="list" :rows="3" />
</template>
```

### 常见问题 (FAQ)

**Q: 需要为按钮单独添加悬停效果吗？**
A: 不需要！已全局启用。

**Q: 骨架屏会影响性能吗？**
A: 不会。纯 CSS 动画，GPU 加速。

**Q: 如何自定义骨架屏样式？**
A: 查看 `SkeletonLoader.vue` 中的 SCSS 变量。

**Q: 能改变过渡时间吗？**
A: 可以在组件内通过 `:style` 属性覆盖。

**Q: 支持深色模式吗？**
A: 当前版本不支持，未来计划添加。

### 检查清单 (Checklist)

部署前检查：

- [ ] 所有加载状态都使用了骨架屏
- [ ] 骨架屏类型与实际内容匹配
- [ ] 没有混用多种加载指示器
- [ ] 过渡时间不超过 0.3s
- [ ] 在移动设备上测试过
- [ ] 没有破坏原有功能
- [ ] 性能测试通过

### 文件位置导航

```
src/
├── styles/
│   ├── global.scss          ← 全局微交互样式
│   ├── variables.scss       ← 设计变量
│   └── mixins.scss          ← 样式混合宏
└── components/
    └── common/
        └── SkeletonLoader.vue ← 骨架屏组件

文档：
├── IMPROVEMENTS_SUMMARY.md   ← 改进总结
└── MICRO_INTERACTIONS_GUIDE.md ← 完整指南
```

### 一分钟快速开始

1. **导入骨架屏**
   ```vue
   import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
   ```

2. **在加载时显示**
   ```vue
   <SkeletonLoader v-if="loading" type="list" />
   ```

3. **享受平滑的悬停效果**
   ```vue
   <!-- 自动启用，无需配置 -->
   <el-button>自动有悬停效果</el-button>
   ```

4. **使用过渡动画**
   ```vue
   <transition name="fade">
     <div v-if="show">内容</div>
   </transition>
   ```

### 性能建议

- ✅ 使用合适的骨架屏类型
- ✅ 不超过 5 秒显示加载
- ✅ 在网络慢时显示
- ❌ 不要在网络快时显示
- ❌ 不要过度使用动画

---

**最后一步**: 打开浏览器，刷新页面，享受流畅的微交互体验！✨

