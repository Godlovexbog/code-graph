import logging
from typing import List, Dict, Optional, Set, Tuple
import javalang
from javalang.tree import (
    CompilationUnit, ClassDeclaration, InterfaceDeclaration,
    MethodDeclaration, FieldDeclaration, ConstructorDeclaration,
    MethodInvocation, MemberReference, ClassCreator,
    VariableDeclarator, FormalParameter, BasicType, ReferenceType,
    MethodReference, SuperMethodInvocation, This, Literal,
    StatementExpression, LocalVariableDeclaration
)

logger = logging.getLogger(__name__)


class ClassInfo:
    """类信息数据类。"""
    def __init__(self):
        self.fqn: str = ""
        self.class_name: str = ""
        self.package: str = ""
        self.modifiers: List[str] = []
        self.annotations: List[str] = []
        self.is_interface: bool = False
        self.is_abstract: bool = False
        self.super_class: Optional[str] = None
        self.interfaces: List[str] = []
        self.methods: List['MethodInfo'] = []
        self.fields: Dict[str, str] = {}  # 字段名 -> 类型名
        self.file_path: str = ""


class MethodInfo:
    """方法信息数据类。"""
    def __init__(self):
        self.method_name: str = ""
        self.return_type: str = ""
        self.parameters: List[Dict[str, str]] = []
        self.modifiers: List[str] = []
        self.annotations: List[str] = []
        self.line_start: int = 0
        self.line_end: int = 0
        self.is_constructor: bool = False
        self.ast_node = None  # 保留 AST 节点供后续提取调用


class JavaParser:
    """使用 javalang 解析 Java 文件 AST，提取类和方法信息。"""

    def __init__(self):
        self._class_index: Dict[str, ClassInfo] = {}  # FQN -> ClassInfo
        self._interface_index: Dict[str, List[str]] = {}  # interface FQN -> [implementing class FQNs]

    def parse_file(self, file_path: str) -> List[ClassInfo]:
        """解析单个 Java 文件，返回提取的 ClassInfo 列表。"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = javalang.parse.parse(source)
        except Exception as e:
            logger.warning(f"解析失败，跳过文件 {file_path}: {e}")
            return []

        classes = []
        package = self._get_package(tree)

        for path, node in tree.filter(ClassDeclaration):
            cls_info = self._extract_class(node, package, file_path, is_interface=False)
            classes.append(cls_info)
            self._class_index[cls_info.fqn] = cls_info

        for path, node in tree.filter(InterfaceDeclaration):
            cls_info = self._extract_class(node, package, file_path, is_interface=True)
            classes.append(cls_info)
            self._class_index[cls_info.fqn] = cls_info

        return classes

    def build_indexes(self, all_classes: List[ClassInfo]):
        """建立索引：接口→实现类映射。"""
        # 先建立简单名→FQN映射
        name_to_fqn = {}
        for cls in all_classes:
            name_to_fqn[cls.class_name] = cls.fqn

        for cls in all_classes:
            # 更新 super_class 为 FQN
            if cls.super_class and cls.super_class in name_to_fqn:
                cls.super_class = name_to_fqn[cls.super_class]

            for iface_name in cls.interfaces:
                # 尝试将简单名解析为 FQN
                iface_fqn = name_to_fqn.get(iface_name, iface_name)
                if iface_fqn not in self._interface_index:
                    self._interface_index[iface_fqn] = []
                self._interface_index[iface_fqn].append(cls.fqn)

            # 同时更新 ClassInfo 中的 interfaces 为 FQN
            cls.interfaces = [name_to_fqn.get(n, n) for n in cls.interfaces]

    def get_implementations(self, interface_fqn: str) -> List[str]:
        """获取实现指定接口的所有类 FQN。"""
        return self._interface_index.get(interface_fqn, [])

    def get_class_info(self, fqn: str) -> Optional[ClassInfo]:
        """根据 FQN 获取类信息。"""
        return self._class_index.get(fqn)

    def get_all_classes(self) -> List[ClassInfo]:
        return list(self._class_index.values())

    def _get_package(self, tree: CompilationUnit) -> str:
        if tree.package:
            return tree.package.name
        return ""

    def _extract_class(self, node, package: str, file_path: str, is_interface: bool) -> ClassInfo:
        info = ClassInfo()
        info.class_name = node.name
        info.package = package
        info.fqn = f"{package}.{node.name}" if package else node.name
        info.is_interface = is_interface
        info.file_path = file_path

        # 修饰符
        if node.modifiers:
            info.modifiers = list(node.modifiers)
            info.is_abstract = "abstract" in node.modifiers

        # 注解
        info.annotations = self._extract_annotations(node.annotations)

        # 继承
        if node.extends:
            extends_list = node.extends if isinstance(node.extends, list) else [node.extends]
            if extends_list:
                info.super_class = extends_list[0].name

        # 实现接口（只有类有，接口没有）
        if hasattr(node, 'implements') and node.implements:
            info.interfaces = [iface.name for iface in node.implements]

        # 提取方法
        for body_decl in node.body:
            if isinstance(body_decl, MethodDeclaration):
                method_info = self._extract_method(body_decl)
                info.methods.append(method_info)
            elif isinstance(body_decl, ConstructorDeclaration):
                method_info = self._extract_constructor(body_decl)
                info.methods.append(method_info)
            elif isinstance(body_decl, FieldDeclaration):
                self._extract_fields(body_decl, info)

        return info

    def _extract_method(self, node: MethodDeclaration) -> MethodInfo:
        info = MethodInfo()
        info.method_name = node.name
        info.return_type = self._type_to_string(node.return_type)
        info.is_constructor = False
        info.ast_node = node

        if node.modifiers:
            info.modifiers = list(node.modifiers)

        info.annotations = self._extract_annotations(node.annotations)

        if node.parameters:
            for param in node.parameters:
                info.parameters.append({
                    "name": param.name,
                    "type": self._type_to_string(param.type)
                })

        # 行号
        if node.position:
            info.line_start = node.position.line
            info.line_end = self._find_method_end(node)

        return info

    def _extract_constructor(self, node: ConstructorDeclaration) -> MethodInfo:
        info = MethodInfo()
        info.method_name = node.name
        info.return_type = ""
        info.is_constructor = True
        info.ast_node = node

        if node.modifiers:
            info.modifiers = list(node.modifiers)

        info.annotations = self._extract_annotations(node.annotations)

        if node.parameters:
            for param in node.parameters:
                info.parameters.append({
                    "name": param.name,
                    "type": self._type_to_string(param.type)
                })

        if node.position:
            info.line_start = node.position.line
            info.line_end = self._find_method_end(node)

        return info

    def extract_calls(self, method_info: MethodInfo, class_info: ClassInfo) -> List[Dict]:
        """从方法 AST 中提取所有方法调用。"""
        calls = []
        node = method_info.ast_node
        if not node:
            return calls

        for path, call_node in node.filter(MethodInvocation):
            call = self._resolve_method_invocation(call_node, class_info)
            if call:
                calls.append(call)

        for path, call_node in node.filter(SuperMethodInvocation):
            call = {
                "target_class": class_info.super_class or "",
                "target_method": call_node.member,
                "call_site": f"super.{call_node.member}()",
                "line": call_node.position.line if call_node.position else 0,
            }
            calls.append(call)

        return calls

    def extract_references(self, method_info: MethodInfo, class_info: ClassInfo) -> List[Dict]:
        """从方法中提取对类的引用。"""
        refs = []
        node = method_info.ast_node
        if not node:
            return refs

        # 参数类型引用
        for param in method_info.parameters:
            type_name = self._extract_type_name(param["type"])
            if type_name:
                refs.append({"target_class": type_name, "usage": "parameter_type"})

        # 返回类型引用
        if method_info.return_type:
            type_name = self._extract_type_name(method_info.return_type)
            if type_name:
                refs.append({"target_class": type_name, "usage": "return_type"})

        # new 表达式
        for path, creator in node.filter(ClassCreator):
            type_name = self._extract_type_name(creator.type)
            if type_name:
                refs.append({
                    "target_class": type_name,
                    "usage": "new",
                    "line": creator.position.line if creator.position else 0,
                })

        # 局部变量类型
        for path, var_decl in node.filter(LocalVariableDeclaration):
            type_name = self._extract_type_name(var_decl.type)
            if type_name:
                refs.append({
                    "target_class": type_name,
                    "usage": "local_var",
                    "line": var_decl.position.line if var_decl.position else 0,
                })

        # 静态方法调用所属类
        for path, call_node in node.filter(MethodInvocation):
            if call_node.qualifier:
                type_name = self._extract_type_name(call_node.qualifier)
                if type_name:
                    refs.append({
                        "target_class": type_name,
                        "usage": "static_call",
                        "line": call_node.position.line if call_node.position else 0,
                    })

        return refs

    def _resolve_method_invocation(self, node: MethodInvocation, class_info: ClassInfo) -> Optional[Dict]:
        """解析方法调用，返回目标类和方法名。"""
        method_name = node.member
        line = node.position.line if node.position else 0

        # 构建调用代码片段
        call_site = self._build_call_site(node)

        if node.qualifier:
            qualifier_name = self._extract_type_name(node.qualifier)
            if qualifier_name:
                # 1. 先尝试从当前类的字段中解析类型
                resolved_type = class_info.fields.get(qualifier_name)
                if resolved_type:
                    return {
                        "target_class": resolved_type,
                        "target_method": method_name,
                        "call_site": call_site,
                        "line": line,
                    }
                # 2. 如果 qualifier 本身就是类型名（如静态调用 ClassName.method()）
                #    检查是否首字母大写（约定：类名大写，变量名小写）
                if qualifier_name[0].isupper():
                    return {
                        "target_class": qualifier_name,
                        "target_method": method_name,
                        "call_site": call_site,
                        "line": line,
                    }
                # 3. 变量名无法解析为类型，使用变量名作为占位
                return {
                    "target_class": qualifier_name,
                    "target_method": method_name,
                    "call_site": call_site,
                    "line": line,
                }

        # 无修饰符: method() 或 this.method()
        return {
            "target_class": class_info.fqn,
            "target_method": method_name,
            "call_site": call_site,
            "line": line,
        }

    def _build_call_site(self, node: MethodInvocation) -> str:
        """构建调用代码片段。"""
        parts = []
        if node.qualifier:
            if hasattr(node.qualifier, 'member'):
                parts.append(node.qualifier.member)
            elif hasattr(node.qualifier, 'name'):
                parts.append(node.qualifier.name)
            else:
                parts.append(str(node.qualifier))
        parts.append(node.member)
        return f"{'.'.join(parts)}(...)"

    def _extract_type_name(self, type_node) -> Optional[str]:
        """从类型节点提取类型名称。"""
        if type_node is None:
            return None
        if isinstance(type_node, str):
            return type_node
        if hasattr(type_node, 'name'):
            return type_node.name
        if hasattr(type_node, 'qualifier') and type_node.qualifier:
            return f"{type_node.qualifier}.{type_node.name}" if hasattr(type_node, 'name') else str(type_node.qualifier)
        return str(type_node)

    def _type_to_string(self, type_node) -> str:
        """将 javalang 类型节点转为字符串。"""
        if type_node is None:
            return ""
        if isinstance(type_node, str):
            return type_node
        if hasattr(type_node, 'name'):
            return type_node.name
        return str(type_node)

    def _extract_annotations(self, annotations) -> List[str]:
        """提取注解字符串列表。"""
        result = []
        if not annotations:
            return result
        for ann in annotations:
            name = ann.name if hasattr(ann, 'name') else str(ann)
            elements = ""
            if hasattr(ann, 'element') and ann.element:
                elements = f"({ann.element})"
            elif hasattr(ann, 'arguments') and ann.arguments:
                args = ", ".join(str(a) for a in ann.arguments)
                elements = f"({args})"
            result.append(f"@{name}{elements}")
        return result

    def _extract_fields(self, node: FieldDeclaration, class_info: ClassInfo):
        """提取字段名→类型映射。"""
        type_name = self._type_to_string(node.type)
        for declarator in node.declarators:
            class_info.fields[declarator.name] = type_name

    def _find_method_end(self, node) -> int:
        """查找方法结束行号。"""
        max_line = node.position.line if node.position else 0
        for _, child in node:
            if hasattr(child, 'position') and child.position:
                max_line = max(max_line, child.position.line)
        return max_line
