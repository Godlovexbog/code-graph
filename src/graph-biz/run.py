#!/usr/bin/env python
"""业务能力图生成器 CLI - 直接运行版本"""

import json
import os
import sys

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入
from models import L3Process, L4Activity, L5Rule, L6Class, BizGraph
from builder import BizGraphBuilder, build_biz_graph
from html_generator import generate_html


def main():
    # 项目根目录 = src 的父目录
    base_dir = os.path.dirname(os.path.dirname(current_dir))
    
    semantic_path = os.path.join(base_dir, 'output', 'biz-semantic-graph.json')
    code_path = os.path.join(base_dir, 'output', 'code-graph.json')
    output_json = os.path.join(base_dir, 'output', 'biz-graph.json')
    output_html = os.path.join(base_dir, 'output', 'biz-graph.html')
    
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
    
    l3_count = len([n for n in nodes if n.get('level') == 3])
    l4_count = len([n for n in nodes if n.get('level') == 4])
    l5_count = len([n for n in nodes if n.get('level') == 5])
    l6_count = len([n for n in nodes if n.get('level') == 6])
    
    print(f"\n生成完成!")
    print(f"  L3 流程: {l3_count}")
    print(f"  L4 活动: {l4_count}")
    print(f"  L5 规则: {l5_count}")
    print(f"  L6 类: {l6_count}")


if __name__ == '__main__':
    main()
