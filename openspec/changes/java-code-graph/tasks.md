## 1. 项目初始化

- [x] 1.1 创建 `src/` 模块目录结构 (`src/scanner/`, `src/parser/`, `src/graph/`, `src/output/`)
- [x] 1.2 创建 `src/__init__.py` 和各子模块的 `__init__.py`
- [x] 1.3 创建 `requirements.txt`，添加 `javalang` 和 `pyyaml` 依赖
- [x] 1.4 创建 `config.yaml` 示例配置文件

## 2. 配置解析模块 (graph-config)

- [x] 2.1 实现 `ConfigLoader` 类，解析 `config.yaml`
- [x] 2.2 支持 `target_project`、`scan_packages`、`entry_points` 三个配置项
- [x] 2.3 支持相对路径和绝对路径解析
- [x] 2.4 添加配置校验（必填项检查、格式校验）

## 3. 扫描与解析模块 (graph-scan)

- [x] 3.1 实现 `FileScanner`：递归扫描目标项目，收集 `.java` 文件，按 `scan_packages` 过滤
- [x] 3.2 实现 `JavaParser`：使用 javalang 解析单个 Java 文件的 AST
- [x] 3.3 从 AST 提取类信息（类名、包名、修饰符、注解、extends、implements、是否为接口/抽象类）
- [x] 3.4 从 AST 提取方法信息（方法名、返回类型、参数列表、修饰符、注解、行号范围）
- [x] 3.5 从 AST 提取方法体内的方法调用表达式（实例调用、静态调用、this 调用）
- [x] 3.6 从 AST 提取方法对类的引用（参数类型、返回类型、new 表达式、局部变量类型、静态方法所属类）
- [x] 3.7 处理解析失败：记录警告日志，跳过失败文件
- [x] 3.8 建立索引：类名→文件路径映射、接口→实现类映射

## 4. 图构建引擎 (graph-builder)

- [x] 4.1 实现 `GraphBuilder` 核心类，包含 BFS 遍历引擎
- [x] 4.2 实现 `CallExtractor`：从方法 AST 提取 CALL 边
- [x] 4.3 实现 `InterfaceResolver`：解析接口→实现类，展开实现方法到 BFS 队列
- [x] 4.4 实现 `ReferenceExtractor`：提取 REFERENCES 边（方法→类）
- [x] 4.5 实现 `ContainsExtractor`：生成 CONTAINS 边（类→方法）
- [x] 4.6 实现 `ExtendsExtractor`：生成 EXTENDS 边（类→类）
- [x] 4.7 实现 `ImplementsExtractor`：生成 IMPLEMENTS 边（类→类）
- [x] 4.8 实现 `OverrideExtractor`：生成 OVERRIDE 边（方法→方法）
- [x] 4.9 实现范围过滤：只保留 `scan_packages` 内的节点和边
- [x] 4.10 实现 BFS visited 去重和循环调用处理
- [x] 4.11 入口方法解析：从 `FQN#methodName` 格式定位入口方法 AST

## 5. 输出模块 (graph-output)

- [x] 5.1 实现 `JsonExporter`：将图数据输出为标准 JSON 格式（meta + nodes + edges）
- [x] 5.2 实现 `HtmlGenerator`：生成基于 Cytoscape.js 的单文件 HTML 可视化页面
- [x] 5.3 HTML 页面支持力导向布局、节点样式区分（CLASS vs METHOD）、入口方法高亮
- [x] 5.4 HTML 页面支持点击节点显示详情面板
- [x] 5.5 确保输出目录 `output/` 存在，写入 `graph.json` 和 `graph.html`

## 6. 入口与集成

- [x] 6.1 创建 `main.py` 入口脚本（替换现有示例文件），整合配置加载→扫描→解析→图构建→输出全流程
- [x] 6.2 添加命令行参数支持（`--config` 指定配置文件路径）
- [x] 6.3 添加进度日志输出（扫描进度、解析进度、BFS 进度）
- [x] 6.4 添加统计信息输出（节点数、边数、扫描文件数、跳过文件数）

## 7. 测试与验证

- [x] 7.1 准备测试用 Java 项目（包含 Controller/Service/Dao 层级、接口/实现类、继承关系）
- [x] 7.2 运行工具，验证 JSON 输出格式正确
- [x] 7.3 打开 HTML 页面，验证可视化显示正常
- [x] 7.4 验证接口→实现类展开正确
- [x] 7.5 验证范围过滤正确（外部库不出现在图中）
- [x] 7.6 验证循环调用不会导致死循环
