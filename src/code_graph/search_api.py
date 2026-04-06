#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Graph Search API Server

提供图数据的搜索和过滤API，基于 GraphFilter 模块
支持静态文件服务
"""

import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import logging

from src.code_graph.graph.filter import GraphFilter, load_graph_from_json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GraphAPIHandler(BaseHTTPRequestHandler):
    """Graph API 请求处理器"""
    
    graph_filter = None
    static_dir = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/graph':
            self.send_graph()
        elif path == '/search':
            self.handle_search(query)
        elif path == '/focus':
            self.handle_focus(query)
        elif path == '/filter':
            self.handle_filter(query)
        elif path == '/stats':
            self.handle_stats()
        elif path.startswith('/'):
            self.serve_static(path)
        else:
            self.send_error(404, 'Not Found')
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def serve_static(self, path):
        """服务静态文件"""
        if not self.static_dir:
            self.send_error(404, 'Static files not configured')
            return
        
        # 安全检查：防止路径遍历
        if '..' in path:
            self.send_error(403, 'Forbidden')
            return
        
        # 默认 index.html
        if path == '/':
            path = '/index.html'
        
        file_path = os.path.join(self.static_dir, path.lstrip('/'))
        
        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1]
            content_type = {
                '.html': 'text/html',
                '.js': 'application/javascript',
                '.css': 'text/css',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
            }.get(ext, 'application/octet-stream')
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, 'Not Found')
    
    def send_graph(self):
        """返回完整图数据"""
        if GraphAPIHandler.graph_filter:
            data = {
                'meta': {
                    'entryPoints': [n['id'] for n in GraphAPIHandler.graph_filter.all_nodes if n.get('isEntry')],
                    'nodeTypes': list(GraphFilter.DEFAULT_NODE_TYPES),
                    'edgeTypes': list(GraphFilter.DEFAULT_EDGE_TYPES)
                },
                'nodes': GraphAPIHandler.graph_filter.all_nodes,
                'edges': GraphAPIHandler.graph_filter.all_edges
            }
            self.send_json(data)
        else:
            self.send_json({'error': 'Graph not loaded'}, 500)
    
    def handle_search(self, query):
        """搜索入口方法并聚焦"""
        q = query.get('q', [''])[0]
        node_types = set(query.get('nodeTypes', [''])[0].split(',')) if query.get('nodeTypes') else None
        edge_types = set(query.get('edgeTypes', [''])[0].split(',')) if query.get('edgeTypes') else None
        
        if not q:
            self.send_json({'error': 'Missing query parameter q'})
            return
        
        if not GraphAPIHandler.graph_filter:
            self.send_json({'error': 'Graph not loaded'}, 500)
            return
        
        target, nodes, edges = GraphAPIHandler.graph_filter.search(
            q, 
            node_types=node_types, 
            edge_types=edge_types,
            prefer_entry=True
        )
        
        if target:
            stats = GraphAPIHandler.graph_filter.get_stats(nodes, edges)
            self.send_json({
                'target': target,
                'nodes': nodes,
                'edges': edges,
                'stats': stats
            })
        else:
            self.send_json({'error': f'Not found: {q}'}, 404)
    
    def handle_focus(self, query):
        """聚焦到指定节点"""
        target_id = query.get('target', [''])[0]
        node_types = set(query.get('nodeTypes', [''])[0].split(',')) if query.get('nodeTypes') else None
        edge_types = set(query.get('edgeTypes', [''])[0].split(',')) if query.get('edgeTypes') else None
        
        if not target_id:
            self.send_json({'error': 'Missing query parameter target'})
            return
        
        if not GraphAPIHandler.graph_filter:
            self.send_json({'error': 'Graph not loaded'}, 500)
            return
        
        nodes, edges = GraphAPIHandler.graph_filter.focus(
            target_id,
            node_types=node_types,
            edge_types=edge_types
        )
        
        stats = GraphAPIHandler.graph_filter.get_stats(nodes, edges)
        self.send_json({
            'target': target_id,
            'nodes': nodes,
            'edges': edges,
            'stats': stats
        })
    
    def handle_filter(self, query):
        """按节点类型过滤"""
        node_types = set(query.get('nodeTypes', [''])[0].split(',')) if query.get('nodeTypes') else None
        connected_only = query.get('connected', ['true'])[0].lower() == 'true'
        
        if not GraphAPIHandler.graph_filter:
            self.send_json({'error': 'Graph not loaded'}, 500)
            return
        
        nodes, edges = GraphAPIHandler.graph_filter.filter_by_node_type(
            node_types=node_types or GraphFilter.DEFAULT_NODE_TYPES,
            connected_only=connected_only
        )
        
        stats = GraphAPIHandler.graph_filter.get_stats(nodes, edges)
        self.send_json({
            'nodes': nodes,
            'edges': edges,
            'stats': stats
        })
    
    def handle_stats(self):
        """获取统计信息"""
        if not GraphAPIHandler.graph_filter:
            self.send_json({'error': 'Graph not loaded'}, 500)
            return
        
        nodes, edges = GraphAPIHandler.graph_filter.filter_by_node_type(
            GraphFilter.DEFAULT_NODE_TYPES
        )
        stats = GraphAPIHandler.graph_filter.get_stats(nodes, edges)
        self.send_json(stats)
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


def start_server(graph_file: str, port: int = 8765, static_dir: str = None):
    """启动 API 服务器"""
    logger.info(f"Loading graph from {graph_file}...")
    GraphAPIHandler.graph_filter = load_graph_from_json(graph_file)
    GraphAPIHandler.static_dir = static_dir
    logger.info(f"Graph loaded: {len(GraphAPIHandler.graph_filter.all_nodes)} nodes, {len(GraphAPIHandler.graph_filter.all_edges)} edges")
    
    server = HTTPServer(('', port), GraphAPIHandler)
    logger.info(f"Graph API server running at http://localhost:{port}")
    logger.info(f"  - GET /graph         - 获取完整图数据")
    logger.info(f"  - GET /search?q=xxx  - 搜索并聚焦")
    logger.info(f"  - GET /focus?target=xxx - 聚焦到指定节点")
    logger.info(f"  - GET /filter        - 按类型过滤")
    logger.info(f"  - GET /stats         - 获取统计信息")
    if static_dir:
        logger.info(f"  - Static files served from: {static_dir}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Graph API Server')
    parser.add_argument('--file', '-f', default='output/code-graph.json', help='Graph JSON file path')
    parser.add_argument('--port', '-p', type=int, default=8765, help='Server port')
    parser.add_argument('--static', '-s', default=None, help='Static files directory')
    args = parser.parse_args()
    
    start_server(args.file, args.port, args.static)
