#!/usr/bin/env python
"""业务能力图生成器 CLI"""

import argparse
import json
import os
import sys

# 添加 src 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_biz.builder import build_biz_graph
from graph_biz.html_generator import generate_html


def main():
    parser = argparse.ArgumentParser(description='业务能力图生成器')
    parser.add_argument('--semantic-graph', default='output/semantic-graph.json',
                        help='语义图文件路径')
    parser.add_argument('--code-graph', default='output/code-graph.json',
                        help='代码图文件路径 (可选)')
    parser.add_argument('--output-json', default='output/biz-graph.json',
                        help='输出 JSON 文件路径')
    parser.add_argument('--output-html', default='output/biz-graph.html',
                        help='输出 HTML 文件路径')
    
    args = parser.parse_args()
    
    # 获取绝对路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    semantic_path = os.path.join(base_dir, args.semantic_graph)
    code_path = os.path.join(base_dir, args.code_graph) if args.code_graph else None
    output_json = os.path.join(base_dir, args.output_json)
    output_html = os.path.join(base_dir, args.output_html)
    
    print(f"读取语义图: {semantic_path}")
    
    # 构建业务能力图
    print("构建业务能力图...")
    biz_graph = build_biz_graph(semantic_path, code_path)
    
    # 保存 JSON
    print(f"保存 JSON: {output_json}")
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(biz_graph, f, ensure_ascii=False, indent=2)
    
    # 生成 HTML
    print(f"生成 HTML: {output_html}")
    generate_html(biz_graph, output_html)
    
    # 统计
    nodes = biz_graph.get('nodes', [])
    edges = biz_graph.get('edges', [])
    
    l3_count = len([n for n in nodes if n.get('level') == 3])
    l4_count = len([n for n in nodes if n.get('level') == 4])
    l5_count = len([n for n in nodes if n.get('level') == 5])
    l6_count = len([n for n in nodes if n.get('level') == 6])
    
    print(f"\n生成完成!")
    print(f"  L3 流程: {l3_count}")
    print(f"  L4 活动: {l4_count}")
    print(f"  L5 规则: {l5_count}")
    print(f"  L6 类: {l6_count}")
    print(f"  边: {len(edges)}")


if __name__ == '__main__':
    main()
