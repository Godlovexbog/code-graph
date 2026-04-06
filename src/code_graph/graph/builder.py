import logging
from collections import deque
from typing import List, Dict, Set, Optional, Tuple

from src.code_graph.parser.java_parser import JavaParser, ClassInfo, MethodInfo
from src.code_graph.graph.extractors import (
    CallExtractor, ReferenceExtractor, ContainsExtractor,
    ExtendsExtractor, ImplementsExtractor, OverrideExtractor,
    InterfaceResolver
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """BFS 遍历引擎，构建调用图。"""

    def __init__(self, parser: JavaParser, scan_packages: List[str], entry_points: List[str]):
        self.parser = parser
        self.scan_packages = scan_packages
        self.entry_points = entry_points
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.visited: Set[str] = set()
        self._simple_name_to_fqn: Dict[str, str] = {}  # 简单类名 -> FQN 映射
        self.stats = {
            "total_files_scanned": 0,
            "total_files_parsed": 0,
            "total_files_skipped": 0,
        }

    def build(self, all_classes: List[ClassInfo], java_files_count: int) -> Dict:
        """执行 BFS 构建图，返回 {nodes, edges, meta}。"""
        self.stats["total_files_scanned"] = java_files_count
        self.stats["total_files_parsed"] = len(all_classes)

        # 建立索引
        self.parser.build_indexes(all_classes)

        # 提取所有类和方法节点
        self._collect_all_nodes(all_classes)

        # BFS 遍历
        queue = deque()
        for entry in self.entry_points:
            queue.append(entry)

        call_extractor = CallExtractor()
        ref_extractor = ReferenceExtractor()
        interface_resolver = InterfaceResolver()

        while queue:
            method_fqn = queue.popleft()

            if method_fqn in self.visited:
                continue
            self.visited.add(method_fqn)

            # 解析方法所属的类
            class_fqn, method_name = self._split_method_fqn(method_fqn)
            class_info = self.parser.get_class_info(class_fqn)
            if not class_info:
                continue

            method_info = self._find_method(class_info, method_name)
            if not method_info:
                continue

            # 提取 CALL 边
            call_edges = call_extractor.extract(method_info, class_info, self.parser)
            for edge in call_edges:
                # 解析目标类名: 简单名 -> FQN
                resolved_to = self._resolve_target(edge["to"])
                if resolved_to:
                    edge["to"] = resolved_to
                    self.edges.append(edge)
                    if self._is_in_scope(resolved_to) and resolved_to not in self.visited:
                        queue.append(resolved_to)

            # 接口→实现类展开
            impl_methods = interface_resolver.resolve(method_fqn, self.parser)
            for impl_method in impl_methods:
                # 添加 IMPLEMENTS 边（方法级别）
                self.edges.append({
                    "from": method_fqn,
                    "to": impl_method,
                    "type": "IMPLEMENTS",
                })
                if impl_method not in self.visited:
                    queue.append(impl_method)

            # 提取 REFERENCES 边
            ref_edges = ref_extractor.extract(method_info, class_info, self.parser)
            for edge in ref_edges:
                # 解析目标类名: 简单名 -> FQN
                target = edge["to"]
                resolved = self._simple_name_to_fqn.get(target)
                if resolved:
                    edge["to"] = resolved
                if self._is_in_scope(edge["to"]):
                    self.edges.append(edge)

        # 添加结构边（CONTAINS, EXTENDS, IMPLEMENTS, OVERRIDE）
        self._add_structure_edges(all_classes)

        # 过滤：只保留在范围内的节点和边
        self._filter_in_scope()

        return self._build_output()

    def _collect_all_nodes(self, all_classes: List[ClassInfo]):
        """预先收集所有类和方法节点（BFS 可能涉及到的）。"""
        for cls in all_classes:
            if not self._is_in_scope(cls.fqn):
                continue
            # 建立简单名→FQN映射
            self._simple_name_to_fqn[cls.class_name] = cls.fqn

            self.nodes[cls.fqn] = {
                "id": cls.fqn,
                "kind": "CLASS",
                "className": cls.class_name,
                "package": cls.package,
                "modifiers": cls.modifiers,
                "annotations": cls.annotations,
                "file": cls.file_path,
                "isInterface": cls.is_interface,
                "isAbstract": cls.is_abstract,
                "superClass": cls.super_class,
                "interfaces": cls.interfaces,
            }
            for method in cls.methods:
                method_fqn = f"{cls.fqn}#{method.method_name}"
                self.nodes[method_fqn] = {
                    "id": method_fqn,
                    "kind": "METHOD",
                    "className": cls.class_name,
                    "methodName": method.method_name,
                    "returnType": method.return_type,
                    "parameters": method.parameters,
                    "modifiers": method.modifiers,
                    "annotations": method.annotations,
                    "file": cls.file_path,
                    "lineStart": method.line_start,
                    "lineEnd": method.line_end,
                    "isEntry": method_fqn in self.entry_points,
                }

    def _add_structure_edges(self, all_classes: List[ClassInfo]):
        """添加 CONTAINS, EXTENDS, IMPLEMENTS, OVERRIDE 边。"""
        contains_ext = ContainsExtractor()
        extends_ext = ExtendsExtractor()
        implements_ext = ImplementsExtractor()
        override_ext = OverrideExtractor()

        for cls in all_classes:
            if not self._is_in_scope(cls.fqn):
                continue

            for edge in contains_ext.extract(cls):
                self.edges.append(edge)

            for edge in extends_ext.extract(cls):
                if self._is_in_scope(edge["to"]):
                    self.edges.append(edge)

            for edge in implements_ext.extract(cls):
                if self._is_in_scope(edge["to"]):
                    self.edges.append(edge)

            for edge in override_ext.extract(cls, self.parser):
                if self._is_in_scope(edge["to"]):
                    self.edges.append(edge)

    def _filter_in_scope(self):
        """过滤：只保留在 scan_packages 范围内的节点和边。"""
        valid_nodes = set()
        for node_id in list(self.nodes.keys()):
            if self._is_in_scope(node_id):
                valid_nodes.add(node_id)

        # 移除不在范围内的节点
        self.nodes = {k: v for k, v in self.nodes.items() if k in valid_nodes}

        # 移除涉及无效节点的边
        self.edges = [
            e for e in self.edges
            if e["from"] in valid_nodes and e["to"] in valid_nodes
        ]

    def _is_in_scope(self, fqn: str) -> bool:
        """检查 FQN 是否在 scan_packages 范围内。"""
        for pkg in self.scan_packages:
            if fqn == pkg or fqn.startswith(pkg + ".") or fqn.startswith(pkg + "#"):
                return True
        return False

    def _split_method_fqn(self, method_fqn: str) -> Tuple[str, str]:
        """拆分方法 FQN: com.x.Class#method -> (com.x.Class, method)。"""
        if "#" in method_fqn:
            return method_fqn.rsplit("#", 1)
        return method_fqn, ""

    def _resolve_target(self, target: str) -> Optional[str]:
        """将目标标识符解析为 FQN。
        
        输入可能是:
        - 已经是 FQN: com.x.Service#method
        - 简单类名+方法名: Service#method
        - 变量名+方法名: someVar#method (无法解析)
        """
        if "#" not in target:
            return None
        
        class_part, method_part = target.rsplit("#", 1)
        
        # 如果 class_part 已经是 FQN (包含点号且首字母大写)
        if "." in class_part:
            return target
        
        # 尝试从简单名映射到 FQN
        fqn = self._simple_name_to_fqn.get(class_part)
        if fqn:
            return f"{fqn}#{method_part}"
        
        # 无法解析
        return None

    def _find_method(self, class_info: ClassInfo, method_name: str) -> Optional[MethodInfo]:
        """在类信息中查找指定方法名的 MethodInfo。"""
        for method in class_info.methods:
            if method.method_name == method_name:
                return method
        return None

    def _build_output(self) -> Dict:
        """构建输出 JSON 结构。"""
        nodes_list = list(self.nodes.values())
        edges_list = self.edges

        return {
            "meta": {
                "entryPoints": self.entry_points,
                "scanPackages": self.scan_packages,
                "stats": {
                    "totalNodes": len(nodes_list),
                    "totalEdges": len(edges_list),
                    "filesScanned": self.stats["total_files_scanned"],
                    "filesParsed": self.stats["total_files_parsed"],
                }
            },
            "nodes": nodes_list,
            "edges": edges_list,
        }
