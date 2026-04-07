## 1. 数据结构定义

- [x] 1.1 定义 L3/L4/L5/L6 节点数据结构
- [x] 1.2 定义边关系 (contains/references/calls)
- [x] 1.3 定义输出格式 biz-graph.json schema

## 2. L4/L5 节点抽取

- [x] 2.1 读取 semantic-graph.json
- [x] 2.2 将每个方法转换为 L4 节点
- [x] 2.3 将 business_rules 转换为 L5 节点
- [x] 2.4 建立 L4 contains L5 边

## 3. L6 类节点抽取

- [x] 3.1 从 L4 的 input/output 类型提取 L6
- [x] 3.2 分类为 Entity/PO/DTO/VO/BO
- [x] 3.3 建立 L4 references L6 边

## 4. L3 流程构建

- [x] 4.1 从入口方法沿 CALL 边遍历调用链
- [x] 4.2 按调用顺序构建 L3
- [x] 4.3 L3 contains L4 边
- [x] 4.4 合并所有 L4 引用的 L6 为 L3 references

## 5. 调用边映射

- [x] 5.1 从 code-graph.json 读取 CALL 边
- [x] 5.2 建立 L4 calls L4 边

## 6. HTML 可视化

- [x] 6.1 创建 biz-graph.html
- [x] 6.2 使用 ECharts 力导向图
- [x] 6.3 实现节点点击显示属性面板
- [x] 6.4 实现 L3/L4/L5/L6 类型筛选
- [x] 6.5 集成 Mermaid 渲染流程图

## 7. 测试验证

- [x] 7.1 验证 biz-graph.json 生成正确
- [x] 7.2 验证 HTML 交互功能
- [x] 7.3 验证边关系完整性
