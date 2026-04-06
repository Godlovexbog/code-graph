## ADDED Requirements

### Requirement: 入口方法解析
系统 SHALL 支持通过完整限定名（FQN#methodName）格式指定入口方法，例如 `com.roncoo.pay.controller.F2FPayController#initPay`。

#### Scenario: 解析有效的入口方法
- **WHEN** 用户提供格式为 `com.example.MyClass#myMethod` 的入口
- **THEN** 系统解析出类名 `com.example.MyClass` 和方法名 `myMethod`

#### Scenario: 解析无效的入口格式
- **WHEN** 用户提供的入口不包含 `#` 分隔符
- **THEN** 系统报错并提示正确的格式

### Requirement: Java 源码文件扫描
系统 SHALL 递归扫描目标项目目录，收集所有 `.java` 文件，并根据 `scan_packages` 过滤出目标包内的文件。

#### Scenario: 扫描目标包内的文件
- **WHEN** scan_packages 为 `["com.roncoo.pay"]` 且存在文件 `com/roncoo/pay/controller/F2FPayController.java`
- **THEN** 该文件被纳入扫描范围

#### Scenario: 过滤非目标包的文件
- **WHEN** scan_packages 为 `["com.roncoo.pay"]` 且存在文件 `org.apache.commons.lang.StringUtils.java`
- **THEN** 该文件被排除在扫描范围之外

### Requirement: AST 解析
系统 SHALL 使用 javalang 解析每个 Java 文件的 AST，提取类声明、方法声明、方法体、注解、修饰符、import 语句等信息。

#### Scenario: 成功解析标准 Java 文件
- **WHEN** 解析一个包含类和标准方法的 Java 文件
- **THEN** 系统提取出类名、方法名、参数、返回类型、注解、修饰符

#### Scenario: 解析失败的文件
- **WHEN** javalang 无法解析某个 Java 文件（如使用了不支持的语法）
- **THEN** 系统记录警告日志并跳过该文件，继续处理其他文件

### Requirement: 方法调用提取 (CALL)
系统 SHALL 遍历每个方法的 AST，提取其中所有的方法调用表达式，包括实例方法调用、静态方法调用、接口方法调用。

#### Scenario: 提取实例方法调用
- **WHEN** 方法体包含 `payService.createOrder(req)`
- **THEN** 系统提取出调用目标为 `PayService#createOrder`

#### Scenario: 提取静态方法调用
- **WHEN** 方法体包含 `ConfigUtil.loadConfig()`
- **THEN** 系统提取出调用目标为 `ConfigUtil#loadConfig`

#### Scenario: 提取 this 方法调用
- **WHEN** 方法体包含 `this.validate()`
- **THEN** 系统提取出调用目标为当前类中的 `validate` 方法

### Requirement: 接口→实现类解析
系统 SHALL 在 BFS 遍历中遇到接口方法时，扫描项目中所有实现该接口的类，将实现类中对应方法加入遍历队列。

#### Scenario: 展开接口实现类
- **WHEN** BFS 遇到 `PayService#createOrder` 且项目中存在 `PayServiceImpl` 和 `AlipayService` 实现该接口
- **THEN** 系统将 `PayServiceImpl#createOrder` 和 `AlipayService#createOrder` 加入遍历队列

#### Scenario: 接口无实现类
- **WHEN** BFS 遇到一个接口方法但项目中没有找到任何实现类
- **THEN** 系统将该方法标记为叶子节点，不继续展开

### Requirement: 继承关系解析 (EXTENDS)
系统 SHALL 解析每个类的 `extends` 和 `implements` 声明，建立类与父类/接口之间的 EXTENDS 和 IMPLEMENTS 边。

#### Scenario: 解析类继承
- **WHEN** 类 `PayServiceImpl` 声明 `extends AbstractPayService`
- **THEN** 系统生成边 `PayServiceImpl EXTENDS AbstractPayService`（仅当父类在 scan_packages 内）

#### Scenario: 解析接口实现
- **WHEN** 类 `PayServiceImpl` 声明 `implements PayService`
- **THEN** 系统生成边 `PayServiceImpl IMPLEMENTS PayService`（仅当接口在 scan_packages 内）

### Requirement: 类引用提取 (REFERENCES)
系统 SHALL 从方法签名和方法体中提取对类的引用，包括参数类型、返回类型、new 表达式、局部变量类型、静态方法调用所属类。

#### Scenario: 提取参数类型引用
- **WHEN** 方法签名为 `void initPay(HttpServletRequest req)`
- **THEN** 系统生成边 `initPay REFERENCES HttpServletRequest`（仅当类在 scan_packages 内）

#### Scenario: 提取 new 表达式引用
- **WHEN** 方法体包含 `new OrderRequest()`
- **THEN** 系统生成边 `initPay REFERENCES OrderRequest`，usage 为 `new`

#### Scenario: 提取静态方法调用所属类引用
- **WHEN** 方法体包含 `JsonUtil.toString(obj)`
- **THEN** 系统生成边 `initPay REFERENCES JsonUtil`，usage 为 `static_call`

### Requirement: 类包含关系解析 (CONTAINS)
系统 SHALL 为每个类中的每个方法生成 CONTAINS 边。

#### Scenario: 生成 CONTAINS 边
- **WHEN** 类 `F2FPayController` 包含方法 `initPay`
- **THEN** 系统生成边 `F2FPayController CONTAINS initPay`

### Requirement: BFS 遍历引擎
系统 SHALL 使用广度优先搜索（BFS）从入口方法开始遍历，自动去重（visited 集合），遇到循环调用时不重复展开。

#### Scenario: BFS 正常遍历
- **WHEN** 入口方法 A 调用 B，B 调用 C
- **THEN** 遍历顺序为 A → B → C，所有方法和类都出现在图中

#### Scenario: 处理循环调用
- **WHEN** A 调用 B，B 调用 C，C 调用 A
- **THEN** A 只展开一次，不会死循环；图中包含 A→B、B→C、C→A 三条 CALL 边

#### Scenario: 范围边界截断
- **WHEN** 方法 A 调用 `java.util.HashMap#put`
- **THEN** 该调用不生成节点和边，A 在该方向上成为叶子节点

### Requirement: 方法重写关系解析 (OVERRIDE)
系统 SHALL 识别子类重写父类方法或实现类实现接口方法的关系，生成 OVERRIDE 边。

#### Scenario: 识别方法重写
- **WHEN** `AlipayService#createOrder` 重写了 `AbstractPayService#createOrder`
- **THEN** 系统生成边 `AlipayService#createOrder OVERRIDE AbstractPayService#createOrder`
