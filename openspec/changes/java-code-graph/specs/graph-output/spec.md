## ADDED Requirements

### Requirement: JSON 图数据输出
系统 SHALL 输出标准 JSON 格式的图数据，包含 `meta`、`nodes`、`edges` 三个顶级字段。

#### Scenario: 输出合法 JSON
- **WHEN** 扫描完成
- **THEN** 系统生成 `output/graph.json` 文件，内容为合法的 JSON 格式

#### Scenario: JSON 包含 meta 信息
- **WHEN** 生成 JSON
- **THEN** meta 字段包含 entryPoints、scanPackages、stats（totalNodes、totalEdges）

### Requirement: CLASS 节点格式
系统 SHALL 为每个涉及的类生成 CLASS 节点，包含 id、kind、className、package、modifiers、annotations、file、isInterface、isAbstract、superClass、interfaces 属性。

#### Scenario: 生成普通类节点
- **WHEN** 扫描到类 `com.roncoo.pay.controller.F2FPayController`
- **THEN** 生成节点 `{"id": "com.roncoo.pay.controller.F2FPayController", "kind": "CLASS", "className": "F2FPayController", ...}`

#### Scenario: 生成接口类节点
- **WHEN** 扫描到接口 `com.roncoo.pay.service.PayService`
- **THEN** 生成节点 `{"id": "com.roncoo.pay.service.PayService", "kind": "CLASS", "isInterface": true, ...}`

### Requirement: METHOD 节点格式
系统 SHALL 为每个涉及的方法生成 METHOD 节点，包含 id、kind、className、methodName、returnType、parameters、modifiers、annotations、file、lineStart、lineEnd、isEntry 属性。

#### Scenario: 生成入口方法节点
- **WHEN** 入口方法为 `F2FPayController#initPay`
- **THEN** 生成节点 `{"id": "...F2FPayController#initPay", "kind": "METHOD", "isEntry": true, ...}`

#### Scenario: 生成普通方法节点
- **WHEN** 遍历到方法 `PayServiceImpl#createOrder`
- **THEN** 生成节点 `{"id": "...PayServiceImpl#createOrder", "kind": "METHOD", "isEntry": false, ...}`

### Requirement: 边格式
系统 SHALL 为每种边类型生成对应的边记录，包含 from、to、type 属性。CALL 边额外包含 callSite 和 line 属性。REFERENCES 边额外包含 usage 属性。

#### Scenario: 生成 CALL 边
- **WHEN** 方法 A 调用方法 B
- **THEN** 生成边 `{"from": "A", "to": "B", "type": "CALL", "callSite": "...", "line": N}`

#### Scenario: 生成 IMPLEMENTS 边
- **WHEN** 类 A 实现接口 B
- **THEN** 生成边 `{"from": "A", "to": "B", "type": "IMPLEMENTS"}`

#### Scenario: 生成 REFERENCES 边
- **WHEN** 方法 A 通过 new 表达式引用类 B
- **THEN** 生成边 `{"from": "A", "to": "B", "type": "REFERENCES", "usage": "new"}`

### Requirement: HTML 可视化页面生成
系统 SHALL 生成基于 Cytoscape.js 的单文件 HTML 页面，内嵌 JSON 数据，支持交互式浏览调用图。

#### Scenario: 生成可打开的 HTML 文件
- **WHEN** 扫描完成
- **THEN** 系统生成 `output/graph.html`，双击可在浏览器中打开

#### Scenario: 可视化显示节点和边
- **WHEN** 打开 HTML 页面
- **THEN** 页面显示力导向布局的图，包含所有节点和边

#### Scenario: 节点样式区分
- **WHEN** 查看可视化页面
- **THEN** CLASS 节点和 METHOD 节点使用不同的形状或颜色

#### Scenario: 入口方法高亮
- **WHEN** 查看可视化页面
- **THEN** 入口方法节点使用特殊颜色或样式高亮显示

#### Scenario: 点击节点显示详情
- **WHEN** 用户点击一个节点
- **THEN** 页面显示该节点的详细信息（类名、方法名、注解、文件位置等）
