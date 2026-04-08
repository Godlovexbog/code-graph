import json
import re
import os
import requests
from typing import Dict, List, Any, Set
from collections import defaultdict

try:
    from .models import L3Process, L4Activity, L5Rule, L6Class, BizGraph
except ImportError:
    from models import L3Process, L4Activity, L5Rule, L6Class, BizGraph


class BizGraphBuilder:
    """业务能力图构建器"""
    
    def __init__(self, semantic_graph_path: str, code_graph_path: str = None):
        self.semantic_graph_path = semantic_graph_path
        self.code_graph_path = code_graph_path
        self.semantic_data = None
        self.code_data = None
        self.biz_graph = BizGraph()
        
        # ID 计数器
        self.l3_count = 0
        self.l4_count = 0
        self.l5_count = 0
        self.l6_count = 0
        
        # ID 映射
        self.method_to_l4: Dict[str, str] = {}
        self.class_name_to_l6: Dict[str, str] = {}
        
        # 过滤配置
        self.exclude_class_patterns = [
            'Exception', 'Error', 'Throwable', 'RuntimeException',
            'Util', 'Helper', 'Common', 'Constant', 'Config',
            'VO', 'BO', 'DTO', 'PO', 'DAO', 'Entity', 'Bean',
            'Request', 'Response', 'Result', 'Base'
        ]
        self.always_filter_methods = ['hashCode', 'equals', 'toString', 'clone', 'finalize']
        
    def load_data(self):
        """加载数据"""
        with open(self.semantic_graph_path, 'r', encoding='utf-8') as f:
            self.semantic_data = json.load(f)
        
        if self.code_graph_path:
            with open(self.code_graph_path, 'r', encoding='utf-8') as f:
                self.code_data = json.load(f)
    
    def _filter_method_ids(self, method_ids: Set[str]) -> Set[str]:
        """过滤没有业务语义的方法ID"""
        # 先构建 IMPLEMENTS 映射
        impl_map = {}  # interface -> impl
        impl_reverse = {}  # impl -> interface
        for edge in self.semantic_data.get('edges', []):
            if edge.get('type') == 'IMPLEMENTS':
                impl_map[edge.get('from')] = edge.get('to')
                impl_reverse[edge.get('to')] = edge.get('from')
        
        filtered = set()
        
        for method_id in method_ids:
            if '#' not in method_id:
                continue
            
            class_name, method_name = method_id.rsplit('#', 1)
            
            # 1. 类级别过滤
            if any(p in class_name for p in self.exclude_class_patterns):
                continue
            
            # 2. 始终过滤的方法
            if method_name in self.always_filter_methods:
                continue
            
            # 3. setter 方法过滤
            if method_name.startswith('set'):
                continue
            
            # 4. 短 getter 过滤
            if method_name.startswith('get') or method_name.startswith('is'):
                # 如果是 interface（有实现类），保留
                if method_id in impl_map:
                    pass
                # 如果是实现类（有 interface），也保留
                elif method_id in impl_reverse:
                    pass
                else:
                    line_count = self._get_method_line_count(method_id)
                    if line_count <= 3:
                        continue
            
            filtered.add(method_id)
        
        print(f"方法过滤: {len(method_ids)} -> {len(filtered)} (过滤掉 {len(method_ids) - len(filtered)})")
        return filtered
    
    def _get_method_line_count(self, method_id: str) -> int:
        """获取方法行数"""
        if not self.code_data:
            return 10  # 默认保留
        
        for node in self.code_data.get('nodes', []):
            if node.get('id') == method_id:
                line_start = node.get('lineStart', 0)
                line_end = node.get('lineEnd', 0)
                return max(1, line_end - line_start + 1)
        return 10
    
    def build(self) -> BizGraph:
        """构建业务能力图"""
        if not self.semantic_data:
            self.load_data()
        
        # 1. 构建 L6 (类)
        self._build_l6_nodes()
        
        # 2. 构建 L4 (活动) 和 L5 (规则)
        self._build_l4_l5_nodes()
        
        # 3. 构建 L3 (流程) - 每个入口方法一个流程
        self._build_all_l3_processes()
        
        # 4. 建立边关系
        self._build_edges()
        
        # 5. 映射调用边 (L4 calls L4)
        self._build_calls_edges()
        
        # 6. 后过滤：移除没有业务语义的节点
        self._filter_disconnected_nodes()
        
        return self.biz_graph
    
    def _generate_l3_id(self) -> str:
        self.l3_count += 1
        return f"L3-{self.l3_count:03d}"
    
    def _generate_l4_id(self) -> str:
        self.l4_count += 1
        return f"L4-{self.l4_count:03d}"
    
    def _generate_l5_id(self) -> str:
        self.l5_count += 1
        return f"L5-{self.l5_count:03d}"
    
    def _generate_l6_id(self) -> str:
        self.l6_count += 1
        return f"L6-{self.l6_count:03d}"
    
    def _build_l6_nodes(self):
        """构建 L6 类节点 - 基于包名和类名模式过滤"""
        
        # 获取项目业务包前缀（用于正向筛选）
        biz_package_prefix = 'com.roncoo.pay'
        
        # 排除规则
        exclude_patterns = [
            # 包级别排除
            'java.', 'javax.', 'sun.',
            'org.apache.commons', 'org.springframework', 'org.slf4j',
            'com.fasterxml.jackson', 'com.alibaba.fastjson',
            # 类名后缀排除
            'Util', 'Helper', 'Factory', 'Common', 'Constant', 'Config',
            'VO', 'BO', 'DTO', 'PO', 'DAO', 'Bean', 'Entity',
            # 基本类型包装类
            'Integer', 'Long', 'Short', 'Double', 'Float', 'Byte', 'Boolean', 'Character',
            # 集合框架
            'List', 'Map', 'Set', 'Collection', 'ArrayList', 'HashMap', 'HashSet', 'LinkedList', 'SortedMap', 'SortedSet',
            # 日期时间
            'Date', 'Time', 'Timestamp', 'LocalDate', 'LocalDateTime', 'LocalTime',
            # I/O
            'InputStream', 'OutputStream', 'Reader', 'Writer', 'BufferedReader', 'BufferedWriter',
            # 其他工具类
            'Object', 'Class', 'String', 'StringBuilder', 'StringBuffer',
            'BigDecimal', 'BigInteger',
            'Void', 'Iterable', 'Iterator', 'Comparable', 'Serializable',
            'HttpServletRequest', 'HttpServletResponse', 'HttpSession',
            'BindingResult', 'Model', 'ModelMap', 'RedirectAttributes',
        ]
        
        # 从所有方法的 input/output 类型提取类
        classes: Set[str] = set()
        
        for node in self.semantic_data.get('nodes', []):
            sem = node.get('semantic', {})
            if not sem:
                sem = {'input': node.get('input', []), 'output': node.get('output', {})}
            
            for inp in sem.get('input', []):
                inp_type = inp.get('type', '')
                if inp_type:
                    classes.add(inp_type)
            
            out = sem.get('output', {})
            out_type = out.get('type', '')
            if out_type:
                classes.add(out_type)
            
            params = node.get('parameters', [])
            for p in params:
                ptype = p.get('type', '')
                if ptype:
                    classes.add(ptype)
        
        # 过滤类
        def should_keep_class(class_name: str) -> bool:
            # 如果是业务包内的类，保留
            if class_name.startswith(biz_package_prefix):
                return True
            
            # 检查是否匹配排除模式
            for pattern in exclude_patterns:
                if class_name == pattern or class_name.endswith(pattern) or pattern in class_name:
                    return False
            
            return True
        
        # 创建 L6 节点
        kept_count = 0
        for class_name in classes:
            if should_keep_class(class_name):
                l6_id = self._generate_l6_id()
                self.class_name_to_l6[class_name] = l6_id
                class_type = self._guess_class_type(class_name)
                l6 = L6Class(id=l6_id, name=class_name, class_type=class_type, package="")
                self.biz_graph.add_node(l6)
                kept_count += 1
        
        print(f"L6 类: {len(classes)} -> {kept_count}")
    
    def _guess_class_type(self, class_name: str) -> str:
        """猜测类类型"""
        if 'Vo' in class_name or 'VO' in class_name:
            return 'VO'
        elif 'Bo' in class_name or 'BO' in class_name:
            return 'BO'
        elif 'Dto' in class_name or 'DTO' in class_name:
            return 'DTO'
        elif 'Entity' in class_name or 'entity' in class_name.lower():
            return 'Entity'
        elif 'Po' in class_name or 'PO' in class_name:
            return 'PO'
        elif 'Request' in class_name or 'RequestBo' in class_name:
            return 'BO'
        elif 'Result' in class_name or 'ResultVo' in class_name:
            return 'VO'
        else:
            return 'Entity'
    
    def _build_l4_l5_nodes(self):
        """构建 L4 活动节点和 L5 规则节点"""
        
        # 1. 先收集所有需要创建 L4 的方法（不过滤）
        all_method_ids = set()
        
        # 添加 semantic-graph 中的 METHOD 节点
        for node in self.semantic_data.get('nodes', []):
            if node.get('kind') == 'METHOD':
                all_method_ids.add(node.get('id'))
        
        # 添加被调用但不在 nodes 中的方法（从 CALL/IMPLEMENTS 边提取）
        for edge in self.semantic_data.get('edges', []):
            if edge.get('type') in ('CALL', 'IMPLEMENTS'):
                all_method_ids.add(edge.get('from'))
                all_method_ids.add(edge.get('to'))
        
        # 2. 为每个方法创建 L4（不过滤）
        for method_id in all_method_ids:
            if method_id in self.method_to_l4:
                continue  # 已经创建过了
            
            # 查找这个方法的信息
            node = None
            for n in self.semantic_data.get('nodes', []):
                if n.get('id') == method_id:
                    node = n
                    break
            
            if node:
                self._create_l4_from_node(node)
            else:
                self._create_l4_from_method_id(method_id)
    
    def _filter_disconnected_nodes(self):
        """后过滤：移除没有业务语义的节点 - L4 和 L6"""
        # 构建 L4 -> L5 映射
        l4_to_l5 = {}
        for node in self.biz_graph.nodes:
            if node.level == 4:
                l4_to_l5[node.id] = set(node.contains)
        
        # 构建调用边映射 (from_l4 -> set of to_l4)
        l4_calls = {}
        for edge in self.biz_graph.edges:
            if edge.get('type') == 'calls':
                from_l4 = edge.get('from')
                to_l4 = edge.get('to')
                if from_l4 not in l4_calls:
                    l4_calls[from_l4] = set()
                l4_calls[from_l4].add(to_l4)
        
        # BFS 检查后代是否有 L5 规则
        def has_descendant_rules(l4_id, visited):
            if l4_id in visited:
                return False
            visited.add(l4_id)
            
            # 如果自己有关联 L5，返回 True
            if l4_to_l5.get(l4_id):
                return True
            
            # 检查被调用者的后代
            for callee in l4_calls.get(l4_id, []):
                if has_descendant_rules(callee, visited):
                    return True
            
            return False
        
        # 找出需要保留的 L4
        keep_l4 = set()
        
        for l4_id in l4_to_l5.keys():
            # BFS 检查后代是否有关联规则
            if has_descendant_rules(l4_id, set()):
                keep_l4.add(l4_id)
        
        # 移除不在 keep_l4 中的 L4
        removed_l4 = 0
        for node in list(self.biz_graph.nodes):
            if node.level == 4 and node.id not in keep_l4:
                self.biz_graph.nodes.remove(node)
                removed_l4 += 1
        
        print(f"L4 过滤: {len(l4_to_l5)} -> {len(keep_l4)} (移除 {removed_l4} 个)")
        
        # 过滤 L6: 保留被 L4 引用的
        referenced_l6 = set()
        for node in self.biz_graph.nodes:
            if node.level == 4:
                refs = node.references
                if refs:
                    referenced_l6.update(refs)
        
        removed_l6 = 0
        for node in list(self.biz_graph.nodes):
            if node.level == 6 and node.id not in referenced_l6:
                self.biz_graph.nodes.remove(node)
                removed_l6 += 1
        
        print(f"L6 过滤: 移除 {removed_l6} 个无引用的类")
        removed = 0
        removed_names = []
        for node in list(self.biz_graph.nodes):
            if node.level == 4 and node.id not in keep_l4:
                removed_names.append(node.name)
                self.biz_graph.nodes.remove(node)
                removed += 1
        
        print(f"L4 过滤: {len(l4_to_l5)} -> {len(keep_l4)} (移除 {removed} 个)")
        if removed_names:
            print(f"移除的 L4: {removed_names}")
    
    def _create_l4_from_node(self, node: Dict):
        """从 semantic-graph 节点创建 L4"""
        orig = node.get('original', {})
        sem = node.get('semantic', {})
        
        if not orig:
            orig = {
                'methodName': node.get('methodName', ''),
                'className': node.get('className', ''),
                'file': node.get('file', ''),
                'parameters': node.get('parameters', []),
                'returnType': node.get('returnType', ''),
            }
        
        if not sem:
            sem = {
                'description': node.get('description', ''),
                'flow': node.get('flow', ''),
                'flow_chart': node.get('flow_chart', ''),
                'input': node.get('input', []),
                'output': node.get('output', {}),
                'business_rules': node.get('business_rules', [])
            }
        
        method_id = node.get('id', '')
        method_name = orig.get('methodName', '')
        class_name = orig.get('className', '')
        
        l4_name = f"{class_name}.{method_name}" if class_name and method_name else method_name
        
        l4_id = self._generate_l4_id()
        self.method_to_l4[method_id] = l4_id
        
        l4 = L4Activity(
            id=l4_id,
            name=l4_name,
            description=sem.get('description', ''),
            flow=sem.get('flow', ''),
            flow_chart=sem.get('flow_chart', '')
        )
        l4.input = sem.get('input', [])
        l4.output = sem.get('output', {})
        
        l4.source = {
            "origin": "semantic-graph",
            "class": class_name,
            "method": method_name,
            "file": orig.get('file', '')
        }
        
        # L5 规则
        business_rules = sem.get('business_rules', [])
        l5_ids = []
        for rule_content in business_rules:
            l5_id = self._generate_l5_id()
            l5_ids.append(l5_id)
            
            rule_name = self._generate_rule_name(rule_content)
            rule_type = self._guess_rule_type(rule_content)
            
            l5 = L5Rule(
                id=l5_id,
                name=rule_name,
                content=rule_content,
                rule_type=rule_type
            )
            l5.source = {
                "origin": "semantic-graph",
                "class": class_name,
                "method": method_name
            }
            
            self.biz_graph.add_node(l5)
            self.biz_graph.add_edge(l4_id, l5_id, "contains")
        
        l4.contains = l5_ids
        
        # L4 references L6
        l6_refs = []
        for inp in l4.input:
            inp_type = inp.get('type', '')
            if inp_type in self.class_name_to_l6:
                l6_refs.append(self.class_name_to_l6[inp_type])
        
        out_type = l4.output.get('type', '')
        if out_type in self.class_name_to_l6:
            l6_refs.append(self.class_name_to_l6[out_type])
        
        l4.references = list(set(l6_refs))
        
        self.biz_graph.add_node(l4)
    
    def _create_l4_from_method_id(self, method_id: str):
        """从 method_id 创建 L4（方法不在 semantic-graph nodes 中）"""
        if method_id in self.method_to_l4:
            return  # 已经创建过了
        
        # 解析 className 和 methodName
        if '#' not in method_id:
            class_name = 'Unknown'
            method_name = method_id
        else:
            parts = method_id.split('#')
            class_name = parts[0].split('.')[-1]  # 取最后一部分作为类名
            method_name = parts[-1]
        
        l4_name = f"{class_name}.{method_name}"
        
        l4_id = self._generate_l4_id()
        self.method_to_l4[method_id] = l4_id
        
        l4 = L4Activity(
            id=l4_id,
            name=l4_name,
            description=f"方法 {method_id}",
            flow="",
            flow_chart=""
        )
        
        l4.source = {
            "origin": "edge-derived",
            "method_id": method_id
        }
        
        self.biz_graph.add_node(l4)
    
    def _generate_rule_name(self, content: str) -> str:
        """从规则内容生成名称"""
        if not content:
            return "未命名规则"
        
        # 取前20个字符作为名称
        name = content[:20]
        if len(content) > 20:
            name += "..."
        return name
    
    def _guess_rule_type(self, content: str) -> str:
        """猜测规则类型"""
        content_lower = content.lower()
        
        if 'ip' in content_lower or '白名单' in content_lower or '签名' in content_lower or '安全' in content_lower:
            return 'security'
        elif '校验' in content_lower or '验证' in content_lower or '必须' in content_lower or '不能为空' in content_lower:
            return 'validation'
        elif '重复' in content_lower or '唯一' in content_lower:
            return 'uniqueness'
        else:
            return 'business'
    
    def _build_all_l3_processes(self):
        """构建所有 L3 流程 - 基于已创建的 L4"""
        entry_methods = []
        for node in self.semantic_data.get('nodes', []):
            is_entry = node.get('isEntry', False)
            if not is_entry and node.get('original', {}):
                is_entry = node.get('original', {}).get('isEntry', False)
            
            if is_entry:
                entry_methods.append(node.get('id'))
        
        if not entry_methods:
            return
        
        call_edges = [e for e in self.semantic_data.get('edges', []) if e.get('type') in ('CALL', 'IMPLEMENTS', 'OVERRIDE', 'EXTENDS')]
        
        # 构建 method_id -> implementation 的映射
        method_to_impl = {}
        for e in call_edges:
            from_method = e.get('from', '')
            to_method = e.get('to', '')
            if '#' in from_method and '#' in to_method:
                method_to_impl[from_method] = to_method
        
        adj = defaultdict(list)
        for e in call_edges:
            adj[e['from']].append(e['to'])
        
        for entry_method in entry_methods:
            if entry_method not in self.method_to_l4:
                continue
            
            entry_l4_id = self.method_to_l4[entry_method]
            
            # BFS 找到所有被调用的方法（包括没有 L4 映射的）
            visited = set()
            all_reachable_methods = []
            
            queue = [entry_method]
            while queue:
                node_id = queue.pop(0)
                if node_id in visited:
                    continue
                visited.add(node_id)
                all_reachable_methods.append(node_id)
                
                # 如果这是 interface，尝试跳转到 implementation
                if node_id in method_to_impl:
                    impl = method_to_impl[node_id]
                    if impl not in visited:
                        queue.append(impl)
                
                for next_node in adj.get(node_id, []):
                    if next_node not in visited:
                        queue.append(next_node)
            
            # 获取入口 L4 信息
            entry_l4 = None
            for node in self.biz_graph.nodes:
                if node.id == entry_l4_id:
                    entry_l4 = node
                    break
            
            if not entry_l4:
                continue
            
            # 创建 L3
            l3_id = self._generate_l3_id()
            
            # L3 包含入口 L4 + 所有 BFS 可达的 L4
            all_l4_in_bfs = [self.method_to_l4[m] for m in all_reachable_methods 
                           if m in self.method_to_l4]
            
            # 收集所有 L4 的 L5 和 L6 (只收集 BFS 可达的 L4)
            all_l5_ids = set()
            all_l6_ids = set()
            
            for lid in all_l4_in_bfs:
                for node in self.biz_graph.nodes:
                    if node.id == lid and node.level == 4:
                        all_l5_ids.update(node.contains)
                        all_l6_ids.update(node.references)
            
            # 生成流程图
            print(f"调用 LLM 生成 L3 流程图 (共 {len(all_reachable_methods)} 个方法)...")
            flow_chart = self._generate_l3_flowchart_llm(entry_method, all_reachable_methods)
            
            if not flow_chart:
                # 回退到简单版本
                flow_chart = self._generate_l3_flowchart_simple(all_l4_in_bfs)
            
            # L3 新字段
            # activities: 只有入口 L4
            # rules: 所有 BFS 可达 L4 包含的 L5
            # entities: 所有 BFS 可达的 L6
            entry_l4_id = self.method_to_l4.get(entry_method, '')
            activities_list = [entry_l4_id] if entry_l4_id else []
            
            l3 = L3Process(
                id=l3_id,
                name="L3-" + entry_l4.name,
                description=f"入口方法 {entry_l4.name} 的完整业务流程",
                flow_chart=flow_chart,
                rules=list(all_l5_ids),
                activities=activities_list,
                entities=list(all_l6_ids)
            )
            
            # 兼容旧字段：contains 只包含入口 L4
            l3.contains = activities_list
            l3.references = []  # 旧字段留空
            
            self.biz_graph.add_node(l3)
            
            # 建立 L3 contains L4 边（只对入口 L4）
            for lid in activities_list:
                self.biz_graph.add_edge(l3_id, lid, "contains")
    
    def _build_single_l3_process(self, entry_method: str, adj: Dict):
        """构建单个 L3 流程"""
        visited = set()
        l4_sequence = []
        
        queue = [entry_method]
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            if node_id in self.method_to_l4:
                l4_sequence.append(self.method_to_l4[node_id])
            
            for next_node in adj.get(node_id, []):
                if next_node not in visited:
                    queue.append(next_node)
        
        if not l4_sequence:
            return
        
        entry_orig = None
        for node in self.semantic_data.get('nodes', []):
            if node.get('id') == entry_method:
                entry_orig = node
                break
        
        # 兼容两种格式
        if entry_orig:
            class_name = entry_orig.get('className') or entry_orig.get('original', {}).get('className', 'Unknown')
            method_name = entry_orig.get('methodName') or entry_orig.get('original', {}).get('methodName', 'unknown')
        else:
            class_name = 'Unknown'
            method_name = 'unknown'
        
        l3_id = self._generate_l3_id()
        flow_chart = self._generate_l3_flowchart(l4_sequence)
        
        # L3 包含：L4 + 每个 L4 包含的 L5
        l3_contains = list(l4_sequence)
        l3_references = set()
        
        for l4 in self.biz_graph.nodes:
            if l4.level == 4 and l4.id in l4_sequence:
                # 添加 L4 包含的 L5
                l3_contains.extend(l4.contains)
                # 添加 L4 引用的 L6
                l3_references.update(l4.references)
        
        l3 = L3Process(
            id=l3_id,
            name=f"{class_name}.{method_name}",
            description=f"入口方法 {class_name}#{method_name} 的调用链",
            flow_chart=flow_chart
        )
        l3.contains = l3_contains
        l3.references = list(l3_references)
        
        self.biz_graph.add_node(l3)
        
        for l4_id in l4_sequence:
            self.biz_graph.add_edge(l3_id, l4_id, "contains")
    
    def _generate_l3_flowchart_simple(self, l4_sequence: List[str]) -> str:
        """生成 L3 流程图 - 融合所有 L4 的详细流程为一个大流程"""
        if not l4_sequence:
            return "graph TD\n    START[开始] --> END[结束]"
        
        l4_nodes = [n for n in self.biz_graph.nodes if n.level == 4 and n.id in l4_sequence]
        
        lines = ["graph TD"]
        
        # 融合：按调用顺序把所有 L4 的流程图节点串起来
        lines.append("    START[开始]")
        prev_node = "START"
        step_num = 0
        
        for l4 in l4_nodes:
            flow = l4.flow_chart if l4.flow_chart else ""
            
            # 提取所有节点
            nodes = []
            for line in flow.split('\n'):
                line = line.strip()
                if not line or line.startswith('graph') or line.startswith('style'):
                    continue
                match = re.search(r'([A-Z])\[([^\]]+)\]', line)
                if match:
                    nodes.append(match.group(2)[:20])  # 取节点名，截断
            
            # 如果有子节点，插入到流程中
            if nodes:
                # 只取前几个关键节点
                key_nodes = [n for n in nodes if n and n != '开始' and n != '结束']
                for j, node_name in enumerate(key_nodes[:4]):
                    step_num += 1
                    step_id = f"S{step_num}"
                    lines.append(f"    {step_id}[{node_name}]")
                    lines.append(f"    {prev_node} --> {step_id}")
                    prev_node = step_id
            else:
                # 没有子节点，显示 L4 名称
                step_num += 1
                step_id = f"S{step_num}"
                lines.append(f"    {step_id}[{l4.name.split('.')[-1]}]")
                lines.append(f"    {prev_node} --> {step_id}")
                prev_node = step_id
        
        lines.append(f"    {prev_node} --> END[结束]")
        
        return "\n".join(lines)
    
    def _build_edges(self):
        """建立边关系"""
        # L4 contains L5 在 _build_l4_l5_nodes 已建立
        # L3 contains L4 在 _build_l3_process 已建立
        
        # 建立 L4 references L6
        for l4 in self.biz_graph.nodes:
            if l4.level == 4:
                for l6_id in l4.references:
                    self.biz_graph.add_edge(l4.id, l6_id, "references")
    
    def _build_calls_edges(self):
        """建立调用边 (L4 calls L4) - 包括 IMPLEMENTS/OVERRIDE 关系"""
        if not self.code_data:
            return
        
        call_edges = [e for e in self.code_data.get('edges', []) if e.get('type') in ('CALL', 'IMPLEMENTS')]
        
        for e in call_edges:
            from_method = e.get('from', '')
            to_method = e.get('to', '')
            
            if from_method in self.method_to_l4 and to_method in self.method_to_l4:
                from_l4 = self.method_to_l4[from_method]
                to_l4 = self.method_to_l4[to_method]
                
                # 添加到 calls 列表
                for l4 in self.biz_graph.nodes:
                    if l4.id == from_l4:
                        if to_l4 not in l4.calls:
                            l4.calls.append(to_l4)
                
                # 添加边
                self.biz_graph.add_edge(from_l4, to_l4, "calls")

    def _generate_l3_flowchart_llm(self, entry_method: str, all_reachable_methods: List[str]) -> str:
        """使用 LLM 生成 L3 流程图 - 基于完整的可达方法列表"""
        
        # 收集所有可达方法的语义信息
        methods_info = []
        
        # 先从 semantic_data 获取完整信息
        method_semantic_map = {}
        for node in self.semantic_data.get('nodes', []):
            node_id = node.get('id', '')
            if node_id in all_reachable_methods:
                sem = node.get('semantic', {})
                if not sem:
                    sem = {
                        'description': node.get('description', ''),
                        'flow': node.get('flow', ''),
                        'flow_chart': node.get('flow_chart', '')
                    }
                method_semantic_map[node_id] = {
                    'method_id': node_id,
                    'method': node.get('className', '') + '.' + node.get('methodName', ''),
                    'description': sem.get('description', ''),
                    'flow': sem.get('flow', ''),
                    'flow_chart': sem.get('flow_chart', '')
                }
        
        for mid in all_reachable_methods:
            if mid in method_semantic_map:
                methods_info.append(method_semantic_map[mid])
            else:
                # 尝试从 code-graph 获取基本信息
                methods_info.append({
                    'method_id': mid,
                    'method': mid.split('#')[-1] if '#' in mid else mid,
                    'description': '从入口方法调用的服务',
                    'flow': '',
                    'flow_chart': ''
                })
        
        if not methods_info:
            return ""
        
        methods_json = json.dumps(methods_info, ensure_ascii=False, indent=2)
        
        prompt = f"""你是一个业务分析师。请根据以下完整的调用链方法列表，生成一个全面的业务主流程图（Mermaid格式）。

## 调用链方法列表（共 {len(methods_info)} 个方法）:
{methods_json}

## 要求:
1. 完整遍历所有方法的 flow 和 flow_chart
2. 按调用顺序整理业务流程
3. 生成一个完整、清晰的 Mermaid 流程图
4. 流程图要展示主要的业务处理步骤、分支逻辑、异常处理等
5. 只输出 Mermaid 流程图代码（graph TD 格式），前后用 ```mermaid 包裹

请直接输出 Mermaid 流程图代码:"""

        try:
            api_key = os.environ.get("QWQ_API_KEY", "sk-3c4f02367af44ee28f081f495a80c8d5")
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "qwen3-coder-plus",
                "input": {"prompt": prompt},
                "parameters": {"max_tokens": 3000, "temperature": 0.7}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=180)
            result = response.json()
            
            if "output" in result and "text" in result["output"]:
                flow_chart = result["output"]["text"]
            elif "output" in result and "choices" in result["output"]:
                if result["output"].get("choices"):
                    flow_chart = result["output"]["choices"][0]["message"]["content"]
            else:
                return ""
            
            # 提取 Mermaid 代码
            if "```mermaid" in flow_chart:
                start = flow_chart.find("```mermaid") + len("```mermaid")
                end = flow_chart.find("```", start)
                if end > start:
                    return flow_chart[start:end].strip()
            elif "graph TD" in flow_chart:
                return flow_chart.strip()
            
            return flow_chart.strip()
            
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return ""


def build_biz_graph(semantic_graph_path: str, code_graph_path: str = None) -> Dict:
    """构建业务能力图"""
    builder = BizGraphBuilder(semantic_graph_path, code_graph_path)
    biz_graph = builder.build()
    return biz_graph.to_dict()
