# 双擎智盾 (Dual Engine Shield) - 智能安全检测平台

## 项目结构

```
src/
├── components/              # 组件目录
│   ├── Layout/              # 布局组件
│   │   ├── Sidebar.vue      # 侧边栏导航组件
│   │   └── MainLayout.vue   # 主布局组件
│   ├── PhishingDetection/   # 钓鱼检测组件
│   │   ├── PhishingDetection.vue  # 钓鱼检测主组件
│   │   ├── ModelSelector.vue      # 模型选择组件
│   │   ├── DetectionPanel.vue     # 检测输入面板
│   │   ├── ResultPanel.vue        # 检测结果面板
│   │   ├── HistoryTable.vue       # 历史记录表格
│   │   └── ModelDetailPanel.vue   # 模型详情面板
│   ├── VulnerabilityDetection/ # 漏洞检测组件
│   │   ├── VulnerabilityDetection.vue # 漏洞检测主组件
│   │   ├── CodeEditor.vue             # 代码编辑器组件
│   │   ├── FileUploader.vue           # 文件上传组件
│   │   ├── VulnResultPanel.vue        # 漏洞结果面板
│   │   ├── TabSwitcher.vue            # 标签切换组件
│   │   ├── FolderScanner.vue          # 文件夹扫描组件
│   │   ├── LanguageSelector.vue       # 语言选择组件
│   │   └── MultifFileUploader.vue     # 多文件上传组件
│   ├── CombinedDetection/   # 综合检测组件
│   │   └── CombinedDetection.vue  # 综合检测主组件
│   ├── TaskManager/         # 任务管理组件
│   │   ├── TaskManager.vue     # 任务管理主组件
│   │   ├── StatCard.vue        # 统计卡片组件
│   │   └── TaskResultBadge.vue # 任务结果徽章组件
│   └── common/              # 通用组件
│       ├── WhitelistPanel.vue     # 白名单管理面板
│       ├── TaskDetailModal.vue    # 任务详情模态框
│       └── ProgressBar.vue        # 进度条组件
├── views/                   # 页面视图
│   └── Dashboard.vue        # 仪表盘页面
├── stores/                  # 状态管理
│   ├── detection.ts         # 检测相关状态
│   ├── tasks.ts             # 任务相关状态
│   ├── vulnerability.ts     # 漏洞相关状态
│   └── whitelist.ts         # 白名单相关状态
├── api/                     # API 接口
│   └── index.ts             # API 接口定义
├── styles/                  # 样式文件
│   ├── variables.scss       # 变量定义
│   ├── mixins.scss          # 混合器定义
│   └── global.scss          # 全局样式
├── App.vue                  # 应用根组件
└── main.ts                  # 应用入口文件
```

## 组件功能说明

### 布局组件

- **Sidebar.vue**: 侧边栏导航组件，提供应用的主要导航功能，包含各个模块的入口。
- **MainLayout.vue**: 主布局组件，负责组织应用的整体布局结构，包含侧边栏和主内容区域。

### 钓鱼检测组件

- **PhishingDetection.vue**: 钓鱼检测主组件，整合其他钓鱼检测相关组件，提供完整的钓鱼检测功能。
- **ModelSelector.vue**: 模型选择组件，允许用户选择不同的钓鱼检测模型（如 SVM、GTE、N-gram 等）。
- **DetectionPanel.vue**: 检测输入面板，用于用户输入需要检测的 URL 或内容。
- **ResultPanel.vue**: 检测结果面板，展示钓鱼检测的结果和详细信息。
- **HistoryTable.vue**: 历史记录表格，展示过去的钓鱼检测记录。
- **ModelDetailPanel.vue**: 模型详情面板，展示当前选中模型的详细信息和配置。

### 漏洞检测组件

- **VulnerabilityDetection.vue**: 漏洞检测主组件，整合其他漏洞检测相关组件，提供完整的漏洞检测功能。
- **CodeEditor.vue**: 代码编辑器组件，允许用户直接输入代码进行漏洞检测。
- **FileUploader.vue**: 文件上传组件，允许用户上传文件进行漏洞检测。
- **VulnResultPanel.vue**: 漏洞结果面板，展示漏洞检测的结果和详细信息。
- **TabSwitcher.vue**: 标签切换组件，用于在不同的漏洞检测模式之间切换。
- **FolderScanner.vue**: 文件夹扫描组件，允许用户扫描整个文件夹中的漏洞。
- **LanguageSelector.vue**: 语言选择组件，用于选择代码的编程语言，以便进行更准确的漏洞检测。
- **MultifFileUploader.vue**: 多文件上传组件，允许用户同时上传多个文件进行漏洞检测。

### 综合检测组件

- **CombinedDetection.vue**: 综合检测组件，整合钓鱼检测和漏洞检测功能，提供一站式的安全检测服务。

### 任务管理组件

- **TaskManager.vue**: 任务管理主组件，用于管理和监控所有安全检测任务。
- **StatCard.vue**: 统计卡片组件，展示任务统计信息，如任务数量、成功率等。
- **TaskResultBadge.vue**: 任务结果徽章组件，直观展示任务的状态和结果。

### 通用组件

- **WhitelistPanel.vue**: 白名单管理面板，用于管理白名单中的 URL 或内容，这些内容将被跳过检测。
- **TaskDetailModal.vue**: 任务详情模态框，展示任务的详细信息和执行过程。
- **ProgressBar.vue**: 进度条组件，展示任务执行的进度。

### 状态管理

- **detection.ts**: 检测相关状态管理，包括检测配置、历史记录等。
- **tasks.ts**: 任务相关状态管理，包括任务列表、任务状态等。
- **vulnerability.ts**: 漏洞相关状态管理，包括漏洞规则、漏洞历史等。
- **whitelist.ts**: 白名单相关状态管理，包括白名单列表、白名单规则等。

### 样式文件

- **variables.scss**: 变量定义文件，包含颜色、字体、间距等样式变量。
- **mixins.scss**: 混合器定义文件，包含可重用的样式混合器。
- **global.scss**: 全局样式文件，包含应用的全局样式设置。

## 技术栈

- **前端框架**: Vue 3
- **状态管理**: Pinia
- **UI 框架**: Element Plus
- **样式预处理**: SCSS
- **构建工具**: Vite
- **类型系统**: TypeScript

## 核心功能

1. **钓鱼检测**: 使用多种模型（SVM、GTE、N-gram）检测钓鱼网站和内容。
2. **漏洞检测**: 检测代码和文件中的安全漏洞。
3. **综合检测**: 同时进行钓鱼检测和漏洞检测。
4. **任务管理**: 管理和监控安全检测任务。
5. **白名单管理**: 管理白名单，跳过对特定内容的检测。

## 运行项目

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 项目特点

- **模块化设计**: 采用组件化和模块化设计，代码结构清晰，易于维护和扩展。
- **多模型支持**: 支持多种钓鱼检测模型，提高检测准确性。
- **多语言支持**: 支持多种编程语言的漏洞检测。
- **用户友好**: 界面设计美观，操作简单直观。
- **实时反馈**: 提供实时的检测结果和进度反馈。

## 未来规划

- **更多检测模型**: 集成更多先进的安全检测模型。
- **API 接口**: 提供 API 接口，方便与其他系统集成。
- **批量检测**: 支持批量检测功能，提高检测效率。
- **报告导出**: 支持导出检测报告，方便分析和归档。
- **自定义规则**: 支持用户自定义检测规则，满足特定需求。