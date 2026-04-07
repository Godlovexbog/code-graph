## Why

当前代码分析系统已实现代码图 (code-graph.json) 和语义图 (semantic-graph.json)，但缺少业务能力层次的抽象。无法满足需求变更影响分析的场景：需要知道一个需求涉及哪些业务流程(L3)、活动节点(L4)、业务规则(L5)和类(L6)。

## What Changes

- 新增 biz-graph.json：从 semantic-graph.json 提取，生成 L3-L6 业务能力图
- 新增 biz-graph.html：交互式可视化，支持点击节点查看属性
- 实现 L4/L5/L6 节点抽取逻辑：从 semantic-graph 和代码中提取
- 实现 L3 流程构建：从入口方法调用链组装

## Capabilities

### New Capabilities
- `biz-graph-generator`: 从语义图生成业务能力图 (L3-L6)
- `biz-graph-visualizer`: 业务能力图交互式可视化

## Impact

- 新增输入：semantic-graph.json
- 新增输出：biz-graph.json, biz-graph.html
- 修改：无