from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CapabilityNode:
    """业务能力图节点基类"""
    id: str
    name: str
    level: int  # 3-6
    type: str  # process/activity/rule/class
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 溯源
    source: Dict[str, Any] = field(default_factory=dict)
    
    # 边关系
    contains: List[str] = field(default_factory=list)  # 包含的节点 ID
    references: List[str] = field(default_factory=list)  # 引用的节点 ID
    calls: List[str] = field(default_factory=list)  # 调用的节点 ID
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "type": self.type,
            "description": self.description,
            "tags": self.tags,
            "source": self.source,
            "contains": self.contains,
            "references": self.references,
            "calls": self.calls
        }


@dataclass
class L3Process(CapabilityNode):
    """L3: 业务流程"""
    flow_chart: str = ""
    
    def __init__(self, id: str, name: str, description: str = "", flow_chart: str = ""):
        super().__init__(id, name, 3, "process", description)
        self.flow_chart = flow_chart
    
    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["flow_chart"] = self.flow_chart
        return base


@dataclass
class L4Activity(CapabilityNode):
    """L4: 活动节点"""
    flow_chart: str = ""
    flow: str = ""
    input: List[Dict[str, Any]] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    
    def __init__(self, id: str, name: str, description: str = "", flow: str = "", flow_chart: str = "", input: List = None, output: Dict = None):
        super().__init__(id, name, 4, "activity", description)
        self.flow = flow
        self.flow_chart = flow_chart
        self.input = input or []
        self.output = output or {}
    
    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["flow"] = self.flow
        base["flow_chart"] = self.flow_chart
        base["input"] = self.input
        base["output"] = self.output
        return base


@dataclass
class L5Rule(CapabilityNode):
    """L5: 业务规则"""
    content: str = ""
    rule_type: str = ""  # validation/security/business
    source_code: str = ""
    
    def __init__(self, id: str, name: str, content: str = "", rule_type: str = ""):
        super().__init__(id, name, 5, "rule", content)
        self.content = content
        self.rule_type = rule_type
    
    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["content"] = self.content
        base["rule_type"] = self.rule_type
        base["source_code"] = self.source_code
        return base


@dataclass
class L6Class(CapabilityNode):
    """L6: 类"""
    class_type: str = ""  # Entity/PO/DTO/VO/BO
    package: str = ""
    
    def __init__(self, id: str, name: str, class_type: str = "", package: str = ""):
        super().__init__(id, name, 6, "class", name)
        self.class_type = class_type
        self.package = package
    
    def to_dict(self) -> Dict:
        base = super().to_dict()
        base["class_type"] = self.class_type
        base["package"] = self.package
        return base


@dataclass
class BizGraph:
    """业务能力图"""
    meta: Dict[str, Any] = field(default_factory=dict)
    nodes: List[CapabilityNode] = field(default_factory=list)
    edges: List[Dict[str, str]] = field(default_factory=list)
    
    def add_node(self, node: CapabilityNode):
        self.nodes.append(node)
    
    def add_edge(self, from_id: str, to_id: str, edge_type: str):
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "type": edge_type
        })
    
    def to_dict(self) -> Dict:
        return {
            "meta": self.meta,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": self.edges
        }
