# MiroFish Frontend - Chinese Text Translation Inventory

## Overview
Complete inventory of Chinese text found in the MiroFish frontend application that requires translation to English.

**Scan Date:** 2026-03-15
**Total Files with Chinese:** 20 files
**Total Chinese Character Occurrences:** 1,986
**Total Unique Chinese Strings:** ~1,100+

---

## File-by-File Breakdown

### 1. **App.vue** (5 occurrences)
**Location:** `/src/App.vue`
- Comments only (no user-facing text)
- Examples:
  - Line 6: `使用 Vue Router 来管理页面` (Using Vue Router to manage pages)
  - Line 10: `全局样式重置` (Global style reset)
  - Line 25: `滚动条样式` (Scrollbar style)
  - Line 43: `全局按钮样式` (Global button style)

**Priority:** LOW (Comments only)

---

### 2. **api/graph.js** (13 occurrences)
**Location:** `/src/api/graph.js`
- JSDoc comments for API functions
- Examples:
  - `生成本体（上传文档和模拟需求）` (Generate ontology - upload docs and simulation requirements)
  - `构建图谱` (Build graph)
  - `查询任务状态` (Query task status)
  - `获取图谱数据` (Get graph data)
  - `获取项目信息` (Get project information)

**Priority:** LOW (Comments only)

---

### 3. **api/index.js** (12 occurrences)
**Location:** `/src/api/index.js`
- Comments in API configuration
- Examples:
  - `创建axios实例` (Create axios instance)
  - `5分钟超时（本体生成可能需要较长时间）` (5-minute timeout - ontology generation may take longer)
  - `请求拦截器` (Request interceptor)
  - `响应拦截器（容错重试机制）` (Response interceptor - error handling retry mechanism)
  - `处理网络错误` (Handle network errors)

**Priority:** LOW (Comments only)

---

### 4. **api/report.js** (12 occurrences)
**Location:** `/src/api/report.js`
- JSDoc comments
- Examples:
  - `开始报告生成` (Start report generation)
  - `获取报告生成状态` (Get report generation status)
  - `获取 Agent 日志（增量）` (Get Agent logs - incremental)
  - `获取控制台日志` (Get console logs)
  - `与 Report Agent 对话` (Dialogue with Report Agent)

**Priority:** LOW (Comments only)

---

### 5. **api/simulation.js** (38 occurrences)
**Location:** `/src/api/simulation.js`
- JSDoc comments for simulation API functions
- Examples:
  - `创建模拟` (Create simulation)
  - `准备模拟环境（异步任务）` (Prepare simulation environment - async task)
  - `获取模拟的 Agent Profiles` (Get simulation Agent Profiles)
  - `启动模拟` (Start simulation)
  - `停止模拟` (Stop simulation)
  - `关闭模拟环境（优雅退出）` (Close simulation environment - graceful exit)
  - `获取模拟运行实时状态` (Get simulation run real-time status)
  - `获取历史模拟列表（带项目详情）` (Get historical simulation list - with project details)

**Priority:** LOW (Comments only)

---

### 6. **components/GraphPanel.vue** (134 occurrences, 128 unique)
**Location:** `/src/components/GraphPanel.vue`
**Priority:** MEDIUM (Mix of UI text and comments)

**Key User-Facing Strings:**
- `刷新图谱` (Refresh graph) - Title attribute
- `最大化/还原` (Maximize/Restore) - Title attribute
- `GraphRAG长短期记忆实时更新中` (GraphRAG short/long-term memory real-time updating)
- `实时更新中...` (Real-time updating...)
- `还有少量内容处理中，建议稍后手动刷新图谱` (Some content is still being processed, suggest manually refreshing the graph later)
- `关闭提示` (Close hint) - Title attribute
- `图谱数据加载中...` (Graph data loading...)
- `等待本体生成...` (Waiting for ontology generation...)

**UI Elements:**
- Node Details panel labels
- Relationship information text

---

### 7. **components/HistoryDatabase.vue** (218 occurrences, 184 unique)
**Location:** `/src/components/HistoryDatabase.vue`
**Priority:** HIGH (Significant user-facing content)

**Key User-Facing Strings:**
- `推演记录` (Simulation Records/History)
- `暂无文件` (No files)
- Various status indicators and labels
- Project card titles and descriptions
- Navigation and interaction text

**Notable Sections:**
- Title: `推演记录` (visible on home page)
- Empty state text: `暂无文件` (No files)
- File count display: `+X 个文件` (+X files)
- Status icons with tooltips: `图谱构建`, `环境搭建`, `分析报告`

---

### 8. **components/Step1GraphBuild.vue** (36 occurrences, 31 unique)
**Location:** `/src/components/Step1GraphBuild.vue`
**Priority:** MEDIUM (Workflow step component)

**Key User-Facing Strings:**
- `本体生成` (Ontology Generation) - Step title
- `正在分析文档...` (Analyzing documents...)
- `GENERATED ENTITY TYPES` - Labels
- `GENERATED RELATION TYPES` - Labels
- `GraphRAG构建` (GraphRAG Building) - Step title
- `基于生成的本体，将文档自动分块后调用 Zep 构建知识图谱...` (Based on generated ontology, automatically chunk documents and call Zep to build knowledge graph...)
- `实体节点` (Entity nodes)
- `关系边` (Relationship edges)
- `构建完成` (Build completed)
- `图谱构建已完成，请进入下一步进行模拟环境搭建` (Graph building completed, proceed to next step for simulation environment setup)
- `进入环境搭建 ➝` (Enter environment setup)

---

### 9. **components/Step2EnvSetup.vue** (313 occurrences, 241 unique)
**Location:** `/src/components/Step2EnvSetup.vue`
**Priority:** VERY HIGH (Major workflow step with extensive Chinese UI text)

**Key Sections & Strings:**
- Step 1: `模拟实例初始化` (Simulation Instance Initialization)
- Step 2: `生成 Agent 人设` (Generate Agent Personas)
  - `当前Agent数` (Current Agent Count)
  - `预期Agent总数` (Expected Total Agents)
  - `现实种子当前关联话题数` (Current Topic Count for Seed)
  - `已生成的 Agent 人设` (Generated Agent Personas)
  - Profile fields: `username`, `profession`, `bio`, `interested_topics`
  - `未知职业` (Unknown profession)
  - `暂无简介` (No biography)
  
- Step 3: `配置模拟参数` (Configure Simulation Parameters)
  - `模拟配置（从模板生成）` (Simulation Configuration - from template)
  - `配置编辑` (Configuration edit)
  - Time-related settings and labels

**Extensive Chinese UI Text** - requires careful translation of all configuration labels and instructions

---

### 10. **components/Step3Simulation.vue** (113 occurrences, 103 unique)
**Location:** `/src/components/Step3Simulation.vue`
**Priority:** HIGH (Real-time simulation monitoring)

**Key User-Facing Strings:**
- Platform headers: `Info Plaza`, `Topic Community`
- Status labels and metrics
- `开启图谱实时刷新 (30s)` (Enable real-time graph refresh - 30s)
- `停止图谱实时刷新` (Stop real-time graph refresh)
- `开始生成结果报告` (Start generating result report)
- Round progress indicators
- Elapsed time displays
- Action counters (ACTS)

---

### 11. **components/Step4Report.vue** (389 occurrences, 271 unique)
**Location:** `/src/components/Step4Report.vue`
**Priority:** VERY HIGH (Report generation with extensive content)

**Key Sections:**
- Report generation status tracking
- Section generation progress
- `正在生成...` (Generating...)
- `Waiting for Report Agent...` (partial English)
- Timeline and workflow visualization
- Agent interaction labels
- Content markdown rendering with Chinese labels

**Major Chinese Content Areas:**
- Report outline structure
- Section titles and descriptions
- Status indicators
- Tool usage tracking
- Timeline metrics

---

### 12. **components/Step5Interaction.vue** (141 occurrences, 115 unique)
**Location:** `/src/components/Step5Interaction.vue`
**Priority:** HIGH (Interactive component)

**Key User-Facing Strings:**
- `深度互动` (Deep Interaction) - Step title
- `与世界中任意个体对话` (Dialogue with any individual in the world)
- `与模拟个体对话` (Dialogue with simulated individuals)
- `与 ReportAgent 进行对话` (Dialogue with ReportAgent)
- Profile selection and interaction labels
- Chat interface labels
- Message history display

---

### 13. **store/pendingUpload.js** (5 occurrences)
**Location:** `/src/store/pendingUpload.js`
- Comments only
- `临时存储待上传的文件和需求` (Temporarily store files and requirements to upload)
- `用于首页点击启动引擎后立即跳转，在Process页面再进行API调用` (Used for immediate navigation after clicking start engine on home page, then perform API calls on Process page)

**Priority:** LOW (Comments only)

---

### 14. **views/Home.vue** (121 occurrences, 116 unique)
**Location:** `/src/views/Home.vue`
**Priority:** VERY HIGH (Landing page - user-facing)

**Key Hero Section Strings:**
- `简洁通用的群体智能引擎` (Concise universal collective intelligence engine)
- `v0.1-预览版` (v0.1-preview)
- `上传任意报告 / 即刻推演未来` (Upload any report / Instantly predict the future)
- `上帝视角注入变量，在复杂的群体交互中寻找动态环境下的"局部最优解"` (Inject variables from god's perspective, find "local optimal solutions" in dynamic environments within complex group interactions)
- `让未来在 Agent 群中预演，让决策在百战后胜出` (Let the future be rehearsed in the Agent swarm, let decisions prevail after hundreds of battles)

**Left Panel:**
- `系统状态` (System Status)
- `准备就绪` (Ready)
- `预测引擎待命中，可上传多份非结构化数据以初始化模拟序列` (Prediction engine on standby, can upload multiple unstructured data to initialize simulation sequence)
- `低成本` (Low cost)
- `常规模拟平均5$/次` (Regular simulation average $5/time)
- `高可用` (High availability)
- `最多百万级Agent模拟` (Up to millions of Agent simulations)
- `工作流序列` (Workflow sequence)

**Workflow Steps (5 steps):**
1. `图谱构建` - `现实种子提取 & 个体与群体记忆注入 & GraphRAG构建`
2. `环境搭建` - `实体关系抽取 & 人设生成 & 环境配置Agent注入仿真参数`
3. `开始模拟` - `双平台并行模拟 & 自动解析预测需求 & 动态更新时序记忆`
4. `报告生成` - `ReportAgent拥有丰富的工具集与模拟后环境进行深度交互`
5. `深度互动` - `与模拟世界中的任意一位进行对话 & 与ReportAgent进行对话`

**Right Panel (Upload Console):**
- `01 / 现实种子` (01 / Reality Seed)
- `支持格式: PDF, MD, TXT` (Supported formats: PDF, MD, TXT)
- `拖拽文件上传` (Drag and drop files to upload)
- `或点击浏览文件系统` (Or click to browse file system)
- `02 / 模拟提示词` (02 / Simulation Prompt)
- `// 用自然语言输入模拟或预测需求...` (// Input simulation or prediction requirements in natural language...)
- `启动引擎` (Start engine)
- `初始化中...` (Initializing...)

---

### 15. **views/InteractionView.vue** (22 occurrences)
**Location:** `/src/views/InteractionView.vue`
**Priority:** MEDIUM (Logs and status text)

**Strings:**
- `加载报告数据: ${reportId}` (Loading report data)
- `项目加载成功: ${projectId}` (Project loaded successfully)
- `获取报告信息失败` (Failed to get report information)
- `加载异常` (Loading exception)
- `InteractionView 初始化` (InteractionView initialization)

---

### 16. **views/MainView.vue** (22 occurrences)
**Location:** `/src/views/MainView.vue`
**Priority:** MEDIUM (Step navigation)

**Strings:**
- `图谱` (Graph)
- `双栏` (Split view)
- `工作台` (Workbench)
- Step names with numbers

---

### 17. **views/Process.vue** (231 occurrences, 196 unique)
**Location:** `/src/views/Process.vue`
**Priority:** VERY HIGH (Main workflow orchestration)

**Key Strings:**
- `顶部导航栏` (Top navigation bar)
- `中间步骤指示器` (Middle step indicator)
- `实时知识图谱` (Real-time knowledge graph)
- `节点` (Nodes)
- `关系` (Relationships)
- `刷新图谱` (Refresh graph)
- `退出全屏` (Exit fullscreen)
- `全屏显示` (Fullscreen)
- Navigation and workflow step labels
- Status messages and logs
- Error handling text

---

### 18. **views/ReportView.vue** (22 occurrences)
**Location:** `/src/views/ReportView.vue`
**Priority:** MEDIUM (Report viewing step)

**Strings:**
- Similar to InteractionView
- `加载报告数据` (Loading report data)
- `项目加载成功` (Project loaded successfully)
- `图谱数据加载成功` (Graph data loaded successfully)
- `ReportView 初始化` (ReportView initialization)

---

### 19. **views/SimulationRunView.vue** (72 occurrences, 64 unique)
**Location:** `/src/views/SimulationRunView.vue`
**Priority:** HIGH (Simulation execution)

**Strings:**
- `开启图谱实时刷新 (30s)` (Enable real-time graph refresh)
- `停止图谱实时刷新` (Stop real-time graph refresh)
- `准备返回 Step 2，正在关闭模拟...` (Preparing to return to Step 2, closing simulation...)
- `正在关闭模拟环境...` (Closing simulation environment...)
- `模拟环境已关闭` (Simulation environment closed)
- `关闭模拟环境失败，尝试强制停止...` (Failed to close simulation environment, attempting force stop...)
- `模拟已强制停止` (Simulation force stopped)
- Error and status messages

---

### 20. **views/SimulationView.vue** (67 occurrences, 56 unique)
**Location:** `/src/views/SimulationView.vue`
**Priority:** HIGH (Environment setup step)

**Strings:**
- `环境搭建` (Environment setup)
- `模拟初始化` (Simulation initialization)
- `检测到模拟环境正在运行，正在关闭...` (Detected running simulation environment, closing...)
- `检测到模拟状态为运行中，正在停止...` (Detected running simulation state, stopping...)
- `使用自动配置的模拟轮数` (Using auto-configured simulation rounds)
- Error and status messages

---

### 21. **index.html** (2 occurrences)
**Location:** `/frontend/index.html`
**Priority:** MEDIUM

**Strings:**
- `<html lang="zh-CN">` - Language attribute
- `<meta name="description" content="MiroFish - 社交媒体舆论模拟系统" />` (MiroFish - Social Media Opinion Simulation System)
- `<title>MiroFish - 预测万物</title>` (MiroFish - Predict Everything)

---

## Translation Categories

### 1. **UI Labels & Navigation** (HIGH PRIORITY)
- Step titles and names
- Button labels
- Menu items
- Form labels
- Tab titles

### 2. **User-Facing Messages** (HIGH PRIORITY)
- Status messages
- Success/error notifications
- Loading states
- Empty state messages
- Placeholder text

### 3. **Instructions & Descriptions** (MEDIUM PRIORITY)
- Help text
- Instructions
- Tool tips
- Descriptive text
- Feature explanations

### 4. **Code Comments** (LOW PRIORITY)
- JSDoc comments
- Inline comments
- File headers
- Algorithm explanations

### 5. **Data Labels** (MEDIUM PRIORITY)
- Field names
- Column headers
- Status indicators
- Configuration options

---

## Estimated Translation Effort

| Component | Complexity | Est. Strings | Priority |
|-----------|-----------|--------------|----------|
| Home.vue | High | 116 | VERY HIGH |
| Step2EnvSetup.vue | Very High | 241 | VERY HIGH |
| Step4Report.vue | Very High | 271 | VERY HIGH |
| Process.vue | High | 196 | VERY HIGH |
| HistoryDatabase.vue | High | 184 | HIGH |
| Step5Interaction.vue | Medium | 115 | HIGH |
| GraphPanel.vue | Medium | 128 | MEDIUM |
| Step3Simulation.vue | Medium | 103 | HIGH |
| SimulationView.vue | Medium | 56 | HIGH |
| SimulationRunView.vue | Medium | 64 | HIGH |
| Step1GraphBuild.vue | Medium | 31 | MEDIUM |
| MainView.vue | Low | 14 | MEDIUM |
| InteractionView.vue | Low | 17 | MEDIUM |
| ReportView.vue | Low | 17 | MEDIUM |
| API files (graph.js, index.js, report.js, simulation.js) | Low | 75 | LOW |
| App.vue & Other | Very Low | 10 | LOW |
| **TOTAL** | - | **1,400+** | - |

---

## Notes

1. **Most Critical Files for User Experience:**
   - `Home.vue` - Landing page marketing copy
   - `Step2EnvSetup.vue` - Complex workflow with many configuration options
   - `Step4Report.vue` - Report generation with extensive content

2. **Internationalization Strategy:**
   - Consider implementing i18n (Vue I18n) for dynamic language switching
   - Store translations in separate locale files (`en.json`, `zh.json`, etc.)
   - Use translation keys instead of hardcoded strings where possible

3. **Testing Considerations:**
   - Text length may vary significantly between Chinese and English
   - UI layout adjustments may be needed for longer English text
   - Date/time formatting should be locale-aware

4. **Comment Translation:**
   - While low priority, consider translating comments for developer experience
   - This aids future maintenance and onboarding

