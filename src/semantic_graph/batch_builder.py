#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量语义图生成器 - 为所有入口方法生成语义图

用法:
    python batch_semantic_builder.py [--graph GRAPH_FILE] [--depth DEPTH] [--output OUTPUT]
"""

import argparse
import json
import os
import sys
import logging
from typing import List, Dict, Set, Tuple
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

from src.code_graph.graph.filter import load_graph_from_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BatchSemanticGraphBuilder:
    """批量语义图构建器"""

    DEFAULT_EDGE_TYPES = {"CALL", "CONTAINS", "EXTENDS", "IMPLEMENTS", "REFERENCES", "OVERRIDE"}

    def __init__(self, graph_file: str):
        self.graph_file = graph_file
        self.graph_filter = load_graph_from_json(graph_file)
        self.all_nodes = []
        self.all_edges = []
        
        # 加载 semantic-graph.json 获取语义信息
        semantic_path = graph_file.replace('code-graph.json', 'semantic-graph.json')
        self.semantic_map = {}
        if os.path.exists(semantic_path):
            with open(semantic_path, 'r', encoding='utf-8') as f:
                sem_data = json.load(f)
                for n in sem_data.get('nodes', []):
                    nid = n.get('id')
                    if nid:
                        self.semantic_map[nid] = n
                logger.info(f"加载语义信息: {len(self.semantic_map)} 个节点")
        
    def build_all_entries(self, depth: int = 3, max_entries: int = None, single_entry: str = None):
        """为所有入口方法生成语义图"""
        
        # 从 code-graph.json 获取入口点
        with open(self.graph_file, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        # 如果指定了单一口入口，使用该入口
        if single_entry:
            entry_points = [single_entry]
            logger.info(f"使用指定入口: {single_entry}")
        else:
            entry_points = graph_data.get('meta', {}).get('entryPoints', [])
            logger.info(f"找到 {len(entry_points)} 个入口点")
        
        if max_entries:
            entry_points = entry_points[:max_entries]
            logger.info(f"限制处理前 {max_entries} 个入口")
        
        all_semantic_nodes = []
        all_semantic_edges = []
        method_semantic_map = {}  # method_id -> semantic_node
        
        for i, entry in enumerate(entry_points):
            logger.info(f"[{i+1}/{len(entry_points)}] 处理入口: {entry}")
            
            # 聚焦子图
            nodes, edges = self._focus_subgraph(entry, depth)
            
            # 标记入口
            for n in nodes:
                if n.get('id') == entry:
                    n['isEntry'] = True
                    break
            
            # 合并语义信息
            for n in nodes:
                nid = n.get('id')
                if nid in self.semantic_map:
                    sem = self.semantic_map[nid].get('semantic', {})
                    n['semantic'] = sem
            
            # 收集节点和边
            for n in nodes:
                node_id = n.get('id', '')
                if n.get('kind') == 'METHOD':
                    method_semantic_map[node_id] = n
            
            all_semantic_nodes.extend(nodes)
            all_semantic_edges.extend(edges)
        
        # 去重
        seen_nodes = {}
        unique_nodes = []
        for n in all_semantic_nodes:
            nid = n.get('id')
            if nid not in seen_nodes:
                seen_nodes[nid] = True
                unique_nodes.append(n)
        
        seen_edges = set()
        unique_edges = []
        for e in all_semantic_edges:
            key = (e.get('from'), e.get('to'), e.get('type'))
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(e)
        
        logger.info(f"去重后 - 节点: {len(unique_nodes)}, 边: {len(unique_edges)}")
        
        return {
            "meta": {
                "total_entries": len(entry_points),
                "depth": depth,
                "total_nodes": len(unique_nodes),
                "total_edges": len(unique_edges)
            },
            "nodes": unique_nodes,
            "edges": unique_edges
        }
    
    def _focus_subgraph(self, target: str, depth: int) -> Tuple[List[Dict], List[Dict]]:
        """获取聚焦的子图"""
        
        edge_types = self.DEFAULT_EDGE_TYPES.copy()
        
        # BFS 查找可达节点
        visited = self._bfs_with_depth(target, depth)
        
        # 获取节点和边
        nodes = [n for n in self.graph_filter.all_nodes if n["id"] in visited]
        node_ids = {n["id"] for n in nodes}
        
        edges = [
            e for e in self.graph_filter.all_edges
            if e.get("type") in edge_types and 
            e["from"] in node_ids and 
            e["to"] in node_ids
        ]
        
        return nodes, edges
    
    def _bfs_with_depth(self, start_id: str, max_depth: int) -> Set[str]:
        """带深度的 BFS 遍历"""
        adj = self.graph_filter.build_adjacency(self.DEFAULT_EDGE_TYPES)
        
        visited = set()
        depth_map = {start_id: 0}
        queue = deque([start_id])
        visited.add(start_id)
        
        while queue:
            current = queue.popleft()
            current_depth = depth_map.get(current, 0)
            
            if current_depth >= max_depth:
                continue
            
            neighbors = adj.get(current, set())
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    depth_map[neighbor] = current_depth + 1
                    queue.append(neighbor)
        
        return visited


def main():
    parser = argparse.ArgumentParser(description='批量语义图构建器')
    parser.add_argument('--graph', '-g', default='F:/code/python/code-graph/output/code-graph.json', help='代码图文件')
    parser.add_argument('--depth', '-d', type=int, default=20, help='BFS 遍历深度')
    parser.add_argument('--output', '-o', default='F:/code/python/code-graph/output/biz-semantic-graph.json', help='输出文件')
    parser.add_argument('--max-entries', type=int, default=None, help='最大入口数')
    parser.add_argument('--entry', '-e', default='com.roncoo.pay.controller.F2FPayController#initPay', help='指定入口方法')
    
    args = parser.parse_args()
    
    logger.info(f"读取代码图: {args.graph}")
    
    # 构建器
    builder = BatchSemanticGraphBuilder(args.graph)
    
    # 构建所有入口的语义图
    logger.info(f"开始构建语义图，深度: {args.depth}, 入口: {args.entry}")
    result = builder.build_all_entries(depth=args.depth, max_entries=args.max_entries, single_entry=args.entry)
    
    # 保存
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    logger.info(f"保存到: {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"完成! 节点: {result['meta']['total_nodes']}, 边: {result['meta']['total_edges']}")


if __name__ == '__main__':
    main()
