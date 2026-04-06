## Why

Java 项目代码量大、调用链路复杂，开发者难以快速理解一个入口方法到底调用了哪些下游方法、涉及哪些类和接口。现有工具要么太重（IDE 内置调用层级），要么太浅（简单 grep）。我们需要一个轻量的、可配置的代码调用图生成工具，以 JSON + 可视化 HTML 的形式输出方法调用关系，帮助开发者快速理解代码结构、评估变更影响、排查调用链路。

## What Changes

- 新增 Python 脚本，扫描指定 Java 项目源码，从给定入口方法出发通过 BFS 构建调用图
- 输出标准 JSON 格式的图数据（包含 METHOD 和 CLASS 节点，以及 CALL / CONTAINS / EXTENDS / IMPLEMENTS / REFERENCES 五种边）
- 生成基于 Cytoscape.js 的单文件 HTML 可视化页面，支持交互式浏览调用图
- 支持 YAML 配置入口方法、扫描包范围、目标项目路径
- 支持接口→实现类的自动解析与展开（保守策略：展开所有实现类）
- 严格限定扫描范围在 `scan_packages` 内，外部库（JDK、第三方）不出现在图中

## Capabilities

### New Capabilities

- `graph-scan`: Java 源码扫描与 BFS 调用图构建能力。包含入口解析、AST 解析、方法调用提取、接口实现解析、范围过滤
- `graph-output`: 图数据输出能力。包含 JSON 格式定义、HTML 可视化页面生成
- `graph-config`: YAML 配置解析能力。包含目标项目路径、扫描包、入口方法列表

### Modified Capabilities

<!-- 无现有能力修改 -->

## Impact

- 新增模块: `src/` 下新增 scanner、parser、graph_builder、html_generator 等 Python 模块
- 新增依赖: `javalang` (Python 包，用于 Java AST 解析)
- 新增输出: `output/graph.json` 和 `output/graph.html`
- 不影响现有 `main.py`（保留为示例文件）
