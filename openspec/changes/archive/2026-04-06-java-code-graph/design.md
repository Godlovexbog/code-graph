## Context

本项目是一个空壳 Python 项目（仅含 PyCharm 生成的 `main.py`），目标是构建一个通用的 Java 代码调用图分析工具。工具通过扫描 Java 源码，从指定入口方法出发，使用 BFS 遍历构建方法调用关系图，输出 JSON 数据和 HTML 可视化页面。

**约束条件：**
- 使用 Python 编写，解析库选择 `javalang`（纯 Python，pip 安装即用）
- 前端使用 ECharts，单文件 HTML，无需构建工具
- 仅分析目标项目自身代码（由 `scan_packages` 限定），不追踪 JDK 和第三方库
- 接口→实现类采用保守策略：展开所有实现类
- 支持通过 entry_packages 自动发现入口方法

## Goals / Non-Goals

**Goals:**
- 从给定入口方法（FQN#method）出发，完整追踪项目内的方法调用链
- 支持从入口包自动发现所有 Controller 的 Web 入口方法
- 输出包含 CLASS 和 METHOD 两种节点、六种边类型（CALL / CONTAINS / EXTENDS / IMPLEMENTS / REFERENCES / OVERRIDE）的图数据
- 生成可交互的 HTML 可视化页面，支持搜索聚焦和过滤
- 架构可扩展，Phase 2 可轻松加入新边类型和提取器

**Non-Goals:**
- 不分析 JDK 和第三方库的方法调用
- 不处理反射调用（静态分析无法可靠追踪）
- 不区分静态调用/实例调用/接口调用（统一为 CALL 边）
- 不做运行时分析或性能 profiling

## Decisions

### 1. 解析器选择: javalang

**决策**: 使用 `javalang` 进行 Java AST 解析。

**理由**:
- 纯 Python 实现，`pip install javalang` 即可使用
- 产出的是 AST（不是 CST），节点类型清晰，易于遍历
- 能解析 import、类声明、方法声明、方法调用表达式

**替代方案**:
- `tree-sitter-java`: 速度更快，但产出 CST 且无语义信息，需要大量后处理
- `eclipse-jdt` (via py4j): 语义最精确，但依赖 Eclipse 运行时，过重

**风险**: `javalang` 对 Java 8+ 的某些语法（如 `var`、switch 表达式）支持不全。
**缓解**: 对解析失败的文件记录警告并跳过，不影响整体流程。

### 2. 接口→实现类解析: 保守展开 + 项目内扫描

**决策**: 当 BFS 遇到接口方法调用时，扫描项目中所有 `implements` 该接口的类，将所有实现类方法加入遍历队列。

**理由**:
- 保守策略确保不遗漏调用路径
- 无需解析 Spring 配置文件或注解注入关系
- 实现简单，不依赖外部框架

**CALL 边语义**: CALL 边只连接到源码中直接调用的目标（如接口方法）。实现类方法通过 BFS 展开出现在图中，但不直接从调用方连 CALL 边到每个实现。

### 3. 图模型: 两种节点 + 五种边

**决策**:
- 节点: `CLASS` 和 `METHOD`
- 边: `CALL`（方法→方法）、`CONTAINS`（类→方法）、`EXTENDS`（类→类）、`IMPLEMENTS`（类→类）、`REFERENCES`（方法→类 / 类→类）

**理由**: 覆盖代码理解所需的核心关系，同时保持模型简洁。

### 4. 架构: 提取器模式 (Extractor Pattern)

**决策**: BFS 引擎与边提取逻辑解耦，每种边类型由独立的 `Extractor` 类负责。

```
GraphBuilder
  ├── CallExtractor        (提取方法调用)
  ├── InterfaceResolver    (解析接口→实现类)
  ├── ReferenceExtractor   (提取类引用)
  └── ... (Phase 2 扩展)
```

**理由**: Phase 2 加入新边类型时，只需新增 Extractor 类，无需修改 BFS 核心逻辑。

### 5. 输出: JSON + 单文件 HTML

**决策**:
- JSON 包含 `meta`、`nodes`、`edges` 三个顶级字段
- HTML 为单文件，内联 Cytoscape.js CDN 引用 + 内联 JS/CSS
- HTML 通过 `<script>` 标签直接嵌入 JSON 数据

**理由**: 零部署成本，双击 HTML 文件即可在浏览器中查看。

### 6. 范围过滤: 包名前缀匹配

**决策**: 使用 `scan_packages` 列表中的包名前缀进行匹配。目标方法/类的完整限定名必须以某个包名前缀开头才被视为"在范围内"。

**理由**: 简单、明确、可预测。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| javalang 解析失败 | 部分文件无法分析，调用链断裂 | 记录警告日志，跳过失败文件，继续处理其他文件 |
| 接口实现类过多 | 图膨胀，性能下降 | 可配置 max_depth 和 max_nodes 限制 |
| 循环调用 | BFS 死循环 | visited 集合去重 |
| 泛型类型擦除 | 无法精确解析泛型参数的实际类型 | Phase 1 不处理泛型，按声明类型处理 |
| 内部类/匿名类 | javalang 的 AST 结构可能不同 | 特殊处理内部类的 qualified name 生成 |
| 大项目扫描慢 | 用户体验差 | 预扫描阶段建立索引，BFS 阶段只查询索引 |
