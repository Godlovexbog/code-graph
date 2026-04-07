## Context

当前项目已实现代码图和语义图生成，需要在此基础上构建业务能力图 (biz-graph)。根据 `docs/业务能力图设计文档.md` 的定义，业务能力图包含 L3-L6 四个层级：
- L3: 业务流程 (Process)
- L4: 活动/节点 (Activity)  
- L5: 规则 (Rule)
- L6: 类 (Class)

输入：semantic-graph.json (当前只有1个入口方法 F2FPayController#initPay)
输出：biz-graph.json + biz-graph.html

## Goals / Non-Goals

**Goals:**
- 从 semantic-graph.json 提取 L4 (活动) 和 L5 (规则)
- 构建 L3 (流程)：从入口方法调用链组装
- 生成 L6 (类)：从代码引用中提取 (LLM增强)
- 生成交互式 HTML 可视化

**Non-Goals:**
- L1/L2 抽象 (需要扩展入口覆盖后实现)
- LLM 源码分析提取 L5/L6 (当前直接用 semantic-graph 数据)
- 完整覆盖所有入口 (只处理当前1个入口)

## Decisions

1. **数据源策略**: 优先使用 semantic-graph.json 已有数据，L4/L5 直接提取，暂不调用 LLM 读取源码
2. **L3 构建**: 从入口方法沿 CALL 边遍历，按调用顺序构建 L3
3. **L4 构建**: 每个方法节点 → L4，使用 semantic-graph 的 description/flow/flow_chart
4. **L5 构建**: 每个 business_rules 项 → L5
5. **L6 构建**: 从方法的 input/output 类型提取，暂时简化处理
6. **HTML 可视化**: 复用 semantic-graph.html 的 ECharts 交互模式

## Risks / Trade-offs

- [风险] 当前只有1个入口，L3只能构建1个流程 → 后续扩展入口
- [风险] L6 类信息不完整 → 后续用 LLM 增强
- [风险] L5 规则来源只有 semantic-graph 的 business_rules → 后续从源码提取
