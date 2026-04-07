#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语义图 HTML 生成器 - 独立脚本

从 semantic-graph.json 生成 semantic-graph.html 可视化页面
无需调用 LLM，仅做格式转换

用法:
    python semantic_graph_html.py [--input INPUT] [--output OUTPUT]
"""

import json
import os
import sys
import argparse
import logging

# 添加路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, PROJECT_ROOT)

from src.code_graph.output.semantic_html_generator import SemanticHtmlGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='语义图 HTML 生成器')
    parser.add_argument('--input', '-i', default='F:/code/python/code-graph/output/semantic-graph.json', help='输入的语义图 JSON')
    parser.add_argument('--output', '-o', default='F:/code/python/code-graph/output/semantic-graph.html', help='输出的 HTML 文件')
    
    args = parser.parse_args()
    
    # 读取语义图
    logger.info(f"读取语义图: {args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    
    stats = graph_data.get('meta', {})
    logger.info(f"节点数: {stats.get('total_nodes', 0)}, 边数: {stats.get('total_edges', 0)}")
    
    # 生成 HTML
    output_dir = os.path.dirname(args.output) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"生成 HTML: {args.output}")
    html_path = SemanticHtmlGenerator(output_dir).generate(graph_data)
    
    logger.info(f"✅ 语义图 HTML 已生成: {html_path}")


if __name__ == "__main__":
    main()
