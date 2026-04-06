"""
Graph Filter - 图过滤和搜索模块

提供图数据的过滤、搜索、聚焦等功能，支持：
- 按节点类型过滤
- 按边类型过滤
- BFS 遍历搜索
- 聚焦到指定节点
"""

from typing import List, Dict, Set, Optional, Any, Tuple
from collections import deque
import json


class GraphFilter:
    """图过滤器"""
    
    DEFAULT_NODE_TYPES = {"CLASS", "METHOD", "INTERFACE", "ENTRY"}
    DEFAULT_EDGE_TYPES = {"CALL", "CONTAINS", "EXTENDS", "IMPLEMENTS", "REFERENCES", "OVERRIDE"}
    
    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        """
        初始化图过滤器
        
        Args:
            nodes: 节点列表，每个节点包含 id, kind 等属性
            edges: 边列表，每条边包含 source, target, type 等属性
        """
        self.all_nodes = nodes
        self.all_edges = edges
        self.node_index = {n["id"]: n for n in nodes}
        self.edge_index = {(e["source"], e["target"]): e for e in edges}
        
    def build_adjacency(self, edge_types: Optional[Set[str]] = None) -> Dict[str, Set[str]]:
        """
        构建邻接表
        
        Args:
            edge_types: 要包含的边类型，为空表示所有边
            
        Returns:
            邻接表，key 为节点 id，value 为邻居节点 id 集合
        """
        adj = {}
        for edge in self.all_edges:
            if edge_types and edge.get("type") not in edge_types:
                continue
            source = edge["source"]
            target = edge["target"]
            if source not in adj:
                adj[source] = set()
            adj[source].add(target)
        return adj
    
    def bfs_traverse(
        self, 
        start_ids: List[str], 
        edge_types: Optional[Set[str]] = None,
        max_depth: Optional[int] = None
    ) -> Set[str]:
        """
        BFS 遍历查找连通节点
        
        Args:
            start_ids: 起始节点 id 列表
            edge_types: 要遍历的边类型，为空表示所有边
            max_depth: 最大深度，None 表示不限
            
        Returns:
            所有可达节点的 id 集合
        """
        adj = self.build_adjacency(edge_types)
        visited = set()
        queue = deque(start_ids)
        depth = {sid: 0 for sid in start_ids}
        visited.update(start_ids)
        
        while queue:
            current = queue.popleft()
            current_depth = depth.get(current, 0)
            
            if max_depth is not None and current_depth >= max_depth:
                continue
                
            neighbors = adj.get(current, set())
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    depth[neighbor] = current_depth + 1
                    queue.append(neighbor)
        
        return visited
    
    def filter_by_node_type(
        self, 
        node_types: Set[str],
        connected_only: bool = True,
        edge_types: Optional[Set[str]] = None,
        entry_ids: Optional[Set[str]] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        按节点类型过滤
        
        Args:
            node_types: 要保留的节点类型
            connected_only: 是否只保留连通的节点
            edge_types: 连通性判断使用的边类型
            entry_ids: 入口节点 id 集合（确保这些节点始终保留）
            
        Returns:
            (过滤后的节点列表, 过滤后的边列表)
        """
        connection_types = edge_types or self.DEFAULT_EDGE_TYPES
        
        # 按节点类型过滤
        visible_nodes = [
            n for n in self.all_nodes 
            if n.get("kind") in node_types or (n.get("isInterface") and "INTERFACE" in node_types)
        ]
        
        if not connected_only:
            visible_ids = {n["id"] for n in visible_nodes}
            visible_edges = [
                e for e in self.all_edges
                if e["source"] in visible_ids and e["target"] in visible_ids
            ]
            return visible_nodes, visible_edges
        
        # 找连通的节点
        visible_ids = {n["id"] for n in visible_nodes}
        connected_ids = set()
        
        for edge in self.all_edges:
            if edge.get("type") not in connection_types:
                continue
            if edge["source"] in visible_ids:
                connected_ids.add(edge["source"])
            if edge["target"] in visible_ids:
                connected_ids.add(edge["target"])
        
        # 确保入口节点被保留
        if entry_ids:
            connected_ids.update(entry_ids)
        
        # 过滤节点
        final_nodes = [n for n in visible_nodes if n["id"] in connected_ids]
        final_ids = {n["id"] for n in final_nodes}
        
        # 过滤边
        final_edges = [
            e for e in self.all_edges
            if e["source"] in final_ids and e["target"] in final_ids
        ]
        
        return final_nodes, final_edges
    
    def focus(
        self, 
        target_id: str,
        node_types: Optional[Set[str]] = None,
        edge_types: Optional[Set[str]] = None,
        include_class: bool = True
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        聚焦到指定节点，只显示与其连通的节点
        
        Args:
            target_id: 目标节点 id
            node_types: 要保留的节点类型，为空表示所有类型
            edge_types: BFS 遍历使用的边类型，为空表示所有边
            include_class: 是否包含目标节点所在的类
            
        Returns:
            (聚焦后的节点列表, 聚焦后的边列表)
        """
        node_types = node_types or self.DEFAULT_NODE_TYPES
        edge_types = edge_types or self.DEFAULT_EDGE_TYPES
        
        # BFS 查找所有可达节点
        visited = self.bfs_traverse([target_id], edge_types)
        
        # 如果需要，添加入口方法所在的类
        if include_class and "#" in target_id:
            class_id = target_id.split("#")[0]
            visited.add(class_id)
        
        # 按节点类型过滤
        focus_nodes = [
            n for n in self.all_nodes 
            if n["id"] in visited and (
                n.get("kind") in node_types or 
                (n.get("isInterface") and "INTERFACE" in node_types)
            )
        ]
        focus_ids = {n["id"] for n in focus_nodes}
        
        # 过滤边
        focus_edges = [
            e for e in self.all_edges
            if e.get("type") in edge_types and 
            e["source"] in focus_ids and 
            e["target"] in focus_ids
        ]
        
        return focus_nodes, focus_edges
    
    def search(
        self, 
        query: str,
        node_types: Optional[Set[str]] = None,
        edge_types: Optional[Set[str]] = None,
        prefer_entry: bool = True,
        include_class: bool = True
    ) -> Tuple[Optional[Dict], List[Dict], List[Dict]]:
        """
        搜索节点并聚焦
        
        Args:
            query: 搜索关键词（模糊匹配节点名或 id）
            node_types: 节点类型过滤
            edge_types: 边类型过滤
            prefer_entry: 是否优先匹配入口方法
            include_class: 是否包含目标节点所在的类
            
        Returns:
            (匹配的节点, 聚焦后的节点列表, 聚焦后的边列表)
            如果未找到匹配，返回 (None, [], [])
        """
        node_types = node_types or self.DEFAULT_NODE_TYPES
        query = query.lower()
        
        # 搜索匹配
        if prefer_entry:
            entry_matches = [
                n for n in self.all_nodes
                if n.get("isEntry") and (
                    query in n.get("className", "").lower() or
                    query in n.get("methodName", "").lower() or
                    query in n.get("id", "").lower()
                )
            ]
            if entry_matches:
                target = entry_matches[0]
                focused = self.focus(
                    target["id"], 
                    node_types, 
                    edge_types, 
                    include_class
                )
                return target, focused[0], focused[1]
        
        # 普通搜索
        matches = [
            n for n in self.all_nodes
            if query in n.get("className", "").lower() or
               query in n.get("methodName", "").lower() or
               query in n.get("id", "").lower()
        ]
        
        if not matches:
            return None, [], []
        
        target = matches[0]
        focused = self.focus(
            target["id"], 
            node_types, 
            edge_types, 
            include_class
        )
        return target, focused[0], focused[1]
    
    def get_stats(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """获取统计信息"""
        node_kinds = {}
        edge_types = {}
        
        for n in nodes:
            kind = n.get("kind", "UNKNOWN")
            if n.get("isInterface"):
                kind = "INTERFACE"
            elif n.get("isEntry"):
                kind = "ENTRY"
            node_kinds[kind] = node_kinds.get(kind, 0) + 1
        
        for e in edges:
            t = e.get("type", "UNKNOWN")
            edge_types[t] = edge_types.get(t, 0) + 1
        
        return {
            "totalNodes": len(nodes),
            "totalEdges": len(edges),
            "nodeTypes": node_kinds,
            "edgeTypes": edge_types
        }


def load_graph_from_json(json_path: str) -> 'GraphFilter':
    """从 JSON 文件加载图数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return GraphFilter(data.get("nodes", []), data.get("edges", []))


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.graph.filter <graph.json> [query]")
        sys.exit(1)
    
    graph_file = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else None
    
    gf = load_graph_from_json(graph_file)
    
    if query:
        target, nodes, edges = gf.search(query)
        if target:
            print(f"Found: {target['id']}")
            stats = gf.get_stats(nodes, edges)
            print(f"Focus nodes: {stats['totalNodes']}, edges: {stats['totalEdges']}")
        else:
            print(f"Not found: {query}")
    else:
        nodes, edges = gf.filter_by_node_type(gf.DEFAULT_NODE_TYPES)
        stats = gf.get_stats(nodes, edges)
        print(f"Total nodes: {stats['totalNodes']}, edges: {stats['totalEdges']}")
