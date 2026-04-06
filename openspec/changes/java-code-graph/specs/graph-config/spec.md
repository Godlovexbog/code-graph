## ADDED Requirements

### Requirement: YAML 配置文件解析
系统 SHALL 支持从 `config.yaml` 文件读取扫描配置，包括目标项目路径、扫描包列表、入口方法列表。

#### Scenario: 解析标准配置文件
- **WHEN** config.yaml 包含 target_project、scan_packages、entry_points
- **THEN** 系统正确解析并加载所有配置项

#### Scenario: 配置文件不存在
- **WHEN** 指定路径的 config.yaml 不存在
- **THEN** 系统报错并提示配置文件路径

### Requirement: 目标项目路径配置
系统 SHALL 通过 `target_project` 配置项指定待分析的 Java 项目根目录路径。

#### Scenario: 使用绝对路径
- **WHEN** target_project 为 `/path/to/roncoo-pay`
- **THEN** 系统在该目录下扫描 Java 源码文件

#### Scenario: 使用相对路径
- **WHEN** target_project 为 `../roncoo-pay`
- **THEN** 系统相对于 config.yaml 所在目录解析路径

### Requirement: 扫描包范围配置
系统 SHALL 通过 `scan_packages` 配置项（字符串列表）指定要分析的 Java 包范围，只有完整限定名匹配这些包前缀的类和方法才会出现在图中。

#### Scenario: 单包扫描
- **WHEN** scan_packages 为 `["com.roncoo.pay"]`
- **THEN** 只有 `com.roncoo.pay.*` 下的类和方法出现在图中

#### Scenario: 多包扫描
- **WHEN** scan_packages 为 `["com.roncoo.pay", "com.roncoo.common"]`
- **THEN** 两个包下的类和方法都出现在图中

### Requirement: 入口方法配置
系统 SHALL 通过 `entry_points` 配置项（字符串列表）指定扫描的入口方法，每个入口方法使用 `FQN#methodName` 格式。

#### Scenario: 单入口扫描
- **WHEN** entry_points 为 `["com.roncoo.pay.controller.F2FPayController#initPay"]`
- **THEN** 系统从该方法开始 BFS 遍历

#### Scenario: 多入口扫描
- **WHEN** entry_points 包含多个方法
- **THEN** 系统从每个入口方法分别开始 BFS 遍历，合并到同一张图中
