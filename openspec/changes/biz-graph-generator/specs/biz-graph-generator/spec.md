## ADDED Requirements

### Requirement: 从语义图生成业务能力图
系统 SHALL 能够从 semantic-graph.json 读取数据，生成包含 L3-L6 层级的业务能力图 (biz-graph.json)。

#### Scenario: 生成 L4 活动节点
- **WHEN** 读取 semantic-graph.json 的节点数据
- **THEN** 每个方法节点转换为 L4，包含 id/name/description/input/output/flow/flow_chart

#### Scenario: 生成 L5 规则节点
- **WHEN** 读取 semantic-graph.json 节点的 business_rules
- **THEN** 每个 business_rules 项转换为 L5，包含 id/name/content/rule_type

#### Scenario: 生成 L3 流程
- **WHEN** 从入口方法沿 CALL 边遍历调用链
- **THEN** 构建 L3，包含 contains(L4列表) 和 flow_chart

#### Scenario: 生成 L6 类节点
- **WHEN** 读取方法 input/output 的类型
- **THEN** 提取类型转换为 L6，包含 id/name/class_type/package

### Requirement: 边关系建立
系统 SHALL 正确建立节点之间的边关系。

#### Scenario: 建立 contains 边
- **WHEN** L4 包含 L5 (business_rules)
- **THEN** 建立 contains 边: L4 contains L5

#### Scenario: 建立 references 边
- **WHEN** L4 引用 L6 (input/output 类型)
- **THEN** 建立 references 边: L4 references L6

#### Scenario: 建立 calls 边
- **WHEN** L4 调用其他 L4 (CALL 类型边)
- **THEN** 建立 calls 边: L4 calls L4

### Requirement: 生成交互式 HTML 可视化
系统 SHALL 生成 biz-graph.html，支持交互式查看业务能力图。

#### Scenario: 点击节点显示属性
- **WHEN** 用户点击图中的节点
- **THEN** 右侧面板显示该节点的详细信息 (description/input/output/contains/references)

#### Scenario: 筛选节点类型
- **WHEN** 用户选择筛选条件 (L3/L4/L5/L6)
- **THEN** 图中只显示对应层级的节点

#### Scenario: 渲染 Mermaid 流程图
- **WHEN** 选中 L3 或 L4 节点
- **THEN** 节点详情中渲染 flow_chart 为 Mermaid 图表
