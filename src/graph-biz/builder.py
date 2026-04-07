import json
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
        
    def load_data(self):
        """加载数据"""
        with open(self.semantic_graph_path, 'r', encoding='utf-8') as f:
            self.semantic_data = json.load(f)
        
        if self.code_graph_path:
            with open(self.code_graph_path, 'r', encoding='utf-8') as f:
                self.code_data = json.load(f)
    
    def build(self) -> BizGraph:
        """构建业务能力图"""
        if not self.semantic_data:
            self.load_data()
        
        # 1. 构建 L6 (类)
        self._build_l6_nodes()
        
        # 2. 构建 L4 (活动) 和 L5 (规则)
        self._build_l4_l5_nodes()
        
        # 3. 构建 L3 (流程) - 遍历所有入口
        self._build_all_l3_processes()
        
        # 4. 建立边关系
        self._build_edges()
        
        # 5. 映射调用边 (L4 calls L4)
        self._build_calls_edges()
        
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
        """构建 L6 类节点"""
        # 从所有方法的 input/output 类型提取类
        classes: Set[str] = set()
        
        for node in self.semantic_data.get('nodes', []):
            sem = node.get('semantic', {})
            
            # 兼容两种格式
            if not sem:
                sem = {
                    'input': node.get('input', []),
                    'output': node.get('output', {})
                }
            
            # input 类型
            for inp in sem.get('input', []):
                inp_type = inp.get('type', '')
                if inp_type and inp_type not in ['String', 'BigDecimal', 'int', 'long', 'boolean', 'void', 'Model', 'HttpServletRequest', 'HttpServletResponse', 'BindingResult']:
                    classes.add(inp_type)
            
            # output 类型
            out = sem.get('output', {})
            out_type = out.get('type', '')
            if out_type and out_type not in ['String', 'BigDecimal', 'int', 'long', 'boolean', 'void']:
                classes.add(out_type)
            
            # 也从 parameters 提取类类型
            params = node.get('parameters', [])
            for p in params:
                ptype = p.get('type', '')
                if ptype and ptype not in ['String', 'BigDecimal', 'int', 'long', 'boolean', 'void', 'Model', 'HttpServletRequest', 'HttpServletResponse', 'BindingResult']:
                    classes.add(ptype)
        
        # 创建 L6 节点
        for class_name in classes:
            l6_id = self._generate_l6_id()
            self.class_name_to_l6[class_name] = l6_id
            
            # 简单分类 heuristic
            class_type = self._guess_class_type(class_name)
            
            l6 = L6Class(
                id=l6_id,
                name=class_name,
                class_type=class_type,
                package=""
            )
            self.biz_graph.add_node(l6)
    
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
        for node in self.semantic_data.get('nodes', []):
            # 只处理 METHOD 类型的节点
            node_kind = node.get('kind', '')
            if node_kind != 'METHOD':
                continue
            
            orig = node.get('original', {})
            sem = node.get('semantic', {})
            
            # 兼容两种格式：batch_builder 生成的简化格式和原有格式
            if not orig:
                orig = {
                    'methodName': node.get('methodName', ''),
                    'className': node.get('className', ''),
                    'file': node.get('file', ''),
                    'parameters': node.get('parameters', []),
                    'returnType': node.get('returnType', ''),
                    'isEntry': node.get('isEntry', False)
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
            
            # L4 名称使用 className.methodName 避免重复
            l4_name = f"{class_name}.{method_name}" if class_name and method_name else method_name
            
            # 创建 L4 节点
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
            
            # 溯源
            l4.source = {
                "origin": "semantic-graph",
                "class": class_name,
                "method": method_name,
                "file": orig.get('file', '')
            }
            
            # 处理 L5 规则
            business_rules = sem.get('business_rules', [])
            l5_ids = []
            for rule_content in business_rules:
                l5_id = self._generate_l5_id()
                l5_ids.append(l5_id)
                
                # 生成规则名称
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
                
                # 建立 L4 contains L5
                self.biz_graph.add_edge(l4_id, l5_id, "contains")
            
            l4.contains = l5_ids
            
            # 建立 L4 references L6
            l6_refs = []
            for inp in l4.input:
                inp_type = inp.get('type', '')
                if inp_type in self.class_name_to_l6:
                    l6_refs.append(self.class_name_to_l6[inp_type])
            
            out_type = l4.output.get('type', '')
            if out_type in self.class_name_to_l6:
                l6_refs.append(self.class_name_to_l6[out_type])
            
            l4.references = list(set(l6_refs))
            
            # 添加 L4 节点
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
        """构建所有 L3 流程 - 每个入口方法一个流程"""
        entry_methods = []
        for node in self.semantic_data.get('nodes', []):
            # 兼容两种格式
            is_entry = node.get('isEntry', False)
            if not is_entry and node.get('original', {}):
                is_entry = node.get('original', {}).get('isEntry', False)
            
            if is_entry:
                entry_methods.append(node.get('id'))
        
        if not entry_methods:
            entry_methods = [self.semantic_data.get('nodes', [{}])[0].get('id')]
        
        call_edges = [e for e in self.semantic_data.get('edges', []) if e.get('type') == 'CALL']
        adj = defaultdict(list)
        for e in call_edges:
            adj[e['from']].append(e['to'])
        
        for entry_method in entry_methods:
            self._build_single_l3_process(entry_method, adj)
    
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
        
        l3 = L3Process(
            id=l3_id,
            name=f"{class_name}.{method_name}",
            description=f"入口方法 {class_name}#{method_name} 的调用链",
            flow_chart=flow_chart
        )
        l3.contains = l4_sequence
        
        all_l6_refs = set()
        for l4 in self.biz_graph.nodes:
            if l4.level == 4 and l4.id in l4_sequence:
                all_l6_refs.update(l4.references)
        
        l3.references = list(all_l6_refs)
        
        self.biz_graph.add_node(l3)
        
        for l4_id in l4_sequence:
            self.biz_graph.add_edge(l3_id, l4_id, "contains")
    
    def _generate_l3_flowchart(self, l4_sequence: List[str]) -> str:
        """生成 L3 流程图"""
        if not l4_sequence:
            return "graph TD\n    A[开始] → Z[结束]"
        
        # 获取 L4 名称
        l4_names = []
        for l4 in self.biz_graph.nodes:
            if l4.level == 4 and l4.id in l4_sequence:
                l4_names.append(l4.name)
        
        # 生成 Mermaid
        lines = ["graph TD"]
        lines.append("    A[开始]")
        
        prev = "A"
        for i, name in enumerate(l4_names):
            node_id = chr(65 + i + 1)  # B, C, D...
            lines.append(f"    {node_id}[{name}]")
            lines.append(f"    {prev} --> {node_id}")
            prev = node_id
        
        lines.append(f"    {prev} --> Z[结束]")
        
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
        """建立调用边 (L4 calls L4)"""
        if not self.code_data:
            return
        
        call_edges = [e for e in self.code_data.get('edges', []) if e.get('type') == 'CALL']
        
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


def build_biz_graph(semantic_graph_path: str, code_graph_path: str = None) -> Dict:
    """构建业务能力图"""
    builder = BizGraphBuilder(semantic_graph_path, code_graph_path)
    biz_graph = builder.build()
    return biz_graph.to_dict()
