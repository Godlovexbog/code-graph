from typing import List, Dict, Optional
from src.code_graph.parser.java_parser import ClassInfo, MethodInfo, JavaParser


class CallExtractor:
    """从方法 AST 提取 CALL 边（方法→方法调用）。"""

    def extract(self, method_info: MethodInfo, class_info: ClassInfo, parser: JavaParser) -> List[Dict]:
        calls = parser.extract_calls(method_info, class_info)
        edges = []
        for call in calls:
            target_class = call["target_class"]
            target_method = call["target_method"]
            if target_class and target_method:
                edges.append({
                    "from": f"{class_info.fqn}#{method_info.method_name}",
                    "to": f"{target_class}#{target_method}",
                    "type": "CALL",
                    "callSite": call.get("call_site", ""),
                    "line": call.get("line", 0),
                })
        return edges


class ReferenceExtractor:
    """提取 REFERENCES 边（方法→类引用）。"""

    def extract(self, method_info: MethodInfo, class_info: ClassInfo, parser: JavaParser) -> List[Dict]:
        refs = parser.extract_references(method_info, class_info)
        edges = []
        for ref in refs:
            target_class = ref["target_class"]
            if target_class:
                edges.append({
                    "from": f"{class_info.fqn}#{method_info.method_name}",
                    "to": target_class,
                    "type": "REFERENCES",
                    "usage": ref.get("usage", "unknown"),
                })
        return edges


class ContainsExtractor:
    """生成 CONTAINS 边（类→方法）。"""

    @staticmethod
    def extract(class_info: ClassInfo) -> List[Dict]:
        edges = []
        for method in class_info.methods:
            edges.append({
                "from": class_info.fqn,
                "to": f"{class_info.fqn}#{method.method_name}",
                "type": "CONTAINS",
            })
        return edges


class ExtendsExtractor:
    """生成 EXTENDS 边（类→父类）。"""

    @staticmethod
    def extract(class_info: ClassInfo) -> List[Dict]:
        edges = []
        if class_info.super_class:
            edges.append({
                "from": class_info.fqn,
                "to": class_info.super_class,
                "type": "EXTENDS",
            })
        return edges


class ImplementsExtractor:
    """生成 IMPLEMENTS 边（类→接口）。"""

    @staticmethod
    def extract(class_info: ClassInfo) -> List[Dict]:
        edges = []
        for iface in class_info.interfaces:
            edges.append({
                "from": class_info.fqn,
                "to": iface,
                "type": "IMPLEMENTS",
            })
        return edges


class OverrideExtractor:
    """生成 OVERRIDE 边（方法→方法，重写/实现关系）。"""

    @staticmethod
    def extract(class_info: ClassInfo, parser: JavaParser) -> List[Dict]:
        edges = []
        # 检查父类方法重写
        if class_info.super_class:
            parent_info = parser.get_class_info(class_info.super_class)
            if parent_info:
                for method in class_info.methods:
                    for parent_method in parent_info.methods:
                        if method.method_name == parent_method.method_name:
                            # 简单匹配：方法名相同即视为重写
                            edges.append({
                                "from": f"{class_info.fqn}#{method.method_name}",
                                "to": f"{parent_info.fqn}#{parent_method.method_name}",
                                "type": "OVERRIDE",
                            })

        # 检查接口方法实现
        for iface_fqn in class_info.interfaces:
            iface_info = parser.get_class_info(iface_fqn)
            if iface_info:
                for method in class_info.methods:
                    for iface_method in iface_info.methods:
                        if method.method_name == iface_method.method_name:
                            edges.append({
                                "from": f"{class_info.fqn}#{method.method_name}",
                                "to": f"{iface_fqn}#{iface_method.method_name}",
                                "type": "OVERRIDE",
                            })

        return edges


class InterfaceResolver:
    """解析接口→实现类，返回实现类中对应方法的 FQN 列表。"""

    @staticmethod
    def resolve(method_fqn: str, parser: JavaParser) -> List[str]:
        """
        给定接口方法 FQN (如 com.x.PayService#createOrder),
        返回所有实现类方法 FQN 列表。
        """
        if "#" not in method_fqn:
            return []

        class_fqn, method_name = method_fqn.rsplit("#", 1)
        class_info = parser.get_class_info(class_fqn)

        if not class_info or not class_info.is_interface:
            return []

        impl_class_fqns = parser.get_implementations(class_fqn)
        result = []
        for impl_fqn in impl_class_fqns:
            impl_info = parser.get_class_info(impl_fqn)
            if impl_info:
                # 查找实现类中是否有同名方法
                for method in impl_info.methods:
                    if method.method_name == method_name:
                        result.append(f"{impl_fqn}#{method_name}")
                        break
        return result
