#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语义图构建器 - Semantic Graph Builder

从 code-graph.json 读取代码图，聚焦到指定的入口方法，
读取源文件并调用 LLM 生成语义描述，输出 semantic-graph.json

用法:
    python semantic_graph_builder.py [--graph GRAPH_FILE] [--target TARGET] [--depth DEPTH] [--output OUTPUT]
"""

import argparse
import json
import os
import re
import sys
import logging
from typing import List, Dict, Optional, Set, Tuple
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 添加路径
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


class SemanticGraphBuilder:
    """语义图构建器"""

    DEFAULT_NODE_TYPES = {"CLASS", "METHOD", "INTERFACE", "ENTRY"}
    DEFAULT_EDGE_TYPES = {"CALL", "CONTAINS", "EXTENDS", "IMPLEMENTS", "REFERENCES", "OVERRIDE"}

    def __init__(self, graph_file: str):
        self.graph_file = graph_file
        self.graph_filter = load_graph_from_json(graph_file)
        self.semantic_nodes = []
        self.semantic_edges = []
        
    def focus_subgraph(self, target: str, depth: int = 2) -> Tuple[List[Dict], List[Dict]]:
        """获取聚焦的子图"""
        logger.info(f"聚焦到目标: {target}, 深度: {depth}")
        
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
        
        logger.info(f"子图节点: {len(nodes)}, 边: {len(edges)}")
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

    def read_source_code(self, node: Dict) -> str:
        """读取节点的源代码"""
        file_path = node.get("file")
        if not file_path:
            return ""
        
        if not os.path.isabs(file_path):
            # 尝试从 config 中获取项目根目录
            project_root = self._get_project_root()
            file_path = os.path.join(project_root, file_path)
        
        if not os.path.exists(file_path):
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"读取文件失败 {file_path}: {e}")
            return ""
    
    def _get_project_root(self) -> str:
        """从 graph_file 推断项目根目录"""
        # 假设 graph_file 在项目根目录的 output 子目录
        return os.path.dirname(os.path.dirname(os.path.abspath(self.graph_file)))

    def extract_method_body(self, source: str, node: Dict) -> str:
        """提取方法体内容"""
        line_start = node.get("lineStart", 0)
        line_end = node.get("lineEnd", 0)
        
        if line_start == 0 or line_end == 0:
            return ""
        
        lines = source.split('\n')
        if line_start > len(lines):
            return ""
        
        # 提取方法体，尝试处理多行情况
        body_lines = lines[line_start - 1:line_end]
        return '\n'.join(body_lines)

    def extract_class_fields(self, source: str, class_name: str) -> List[Dict]:
        """提取类的属性"""
        fields = []
        
        # 匹配字段声明
        # private/public/protected 类型 字段名;
        pattern = r'(private|public|protected)\s+(\w+)\s+(\w+)\s*[;=]'
        
        for match in re.finditer(pattern, source):
            modifier = match.group(1)
            field_type = match.group(2)
            field_name = match.group(3)
            
            # 排除常见的非业务字段
            if field_name.startswith('_') or field_name in ['logger', 'log', 'serialVersionUID']:
                continue
            
            fields.append({
                "modifier": modifier,
                "type": field_type,
                "name": field_name
            })
        
        return fields[:20]  # 限制数量

    def build_semantic_prompt(self, node: Dict, source: str, method_body: str = "", class_fields: List[Dict] = None) -> str:
        """构建 LLM 提示词"""
        node_id = node["id"]
        kind = node.get("kind", "METHOD")
        
        prompt = f"""你是一个Java代码语义分析专家。请分析以下Java代码节点，生成业务语义描述。

节点ID: {node_id}
节点类型: {kind}
"""
        
        if kind == "METHOD":
            class_name = node.get("className", "")
            method_name = node.get("methodName", "")
            return_type = node.get("returnType", "")
            parameters = node.get("parameters", "")
            annotations = node.get("annotations", "")
            
            prompt += f"""
类名: {class_name}
方法名: {method_name}
返回类型: {return_type}
参数: {parameters}
注解: {annotations}

方法体代码:
{method_body}

请生成以下JSON格式的语义描述:
{{
    "description": "方法的中文业务描述",
    "input": [
        {{"param": "参数名", "type": "类型", "meaning": "业务含义"}}
    ],
    "output": {{"type": "返回类型", "meaning": "返回值的业务含义"}},
    "flow": "简要的业务流程描述",
    "flow_chart": "Mermaid格式的流程图 (只填flow_chart字段)",
    "business_rules": ["业务规则1", "业务规则2"]
}}

请只返回JSON，不要其他内容。"""
        
        elif kind == "CLASS":
            class_name = node.get("className", "")
            package = node.get("package", "")
            annotations = node.get("annotations", "")
            super_class = node.get("superClass", "")
            interfaces = node.get("interfaces", "")
            
            fields_str = ""
            if class_fields:
                fields_str = "\n".join([f"- {f['type']} {f['name']}" for f in class_fields])
            
            prompt += f"""
包名: {package}
类名: {class_name}
父类: {super_class}
实现接口: {interfaces}
注解: {annotations}

类的属性:
{fields_str}

请生成以下JSON格式的语义描述:
{{
    "description": "类的业务作用描述",
    "responsibilities": ["职责1", "职责2"],
    "dependencies": ["依赖的服务/类"]
}}

请只返回JSON，不要其他内容。"""
        
        return prompt

    def parse_llm_response(self, response: str, kind: str) -> Dict:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # 返回默认结构
        if kind == "METHOD":
            return {
                "description": response[:100],
                "input": [],
                "output": {"type": "", "meaning": ""},
                "flow": "",
                "flow_chart": "",
                "business_rules": []
            }
        else:
            return {
                "description": response[:100],
                "responsibilities": [],
                "dependencies": []
            }


def call_llm(prompt: str, api_key: str = None, model: str = "qwen3-coder-plus") -> str:
    """调用 LLM API - 千问"""
    import requests
    
    if not api_key:
        api_key = os.environ.get("QWQ_API_KEY", "")
    
    if not api_key:
        # 使用默认 API Key
        api_key = "sk-3c4f02367af44ee28f081f495a80c8d5"
    
    # 千问 API 端点 - 使用正确的路径
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        # 兼容两种返回格式
        if "output" in result and "text" in result["output"]:
            return result["output"]["text"]
        elif "output" in result and "choices" in result["output"]:
            # 兼容新格式: output.choices[0].message.content
            if result["output"].get("choices"):
                return result["output"]["choices"][0]["message"]["content"]
        elif "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            logger.warning(f"千问 API 返回格式异常: {result}")
            return '{"description": "API返回异常", "input": [], "output": {}, "flow": ""}'
            
    except requests.exceptions.RequestException as e:
        logger.error(f"调用千问 API 失败: {e}")
        return '{"description": "API调用失败", "input": [], "output": {}, "flow": ""}'


def main():
    parser = argparse.ArgumentParser(description='语义图构建器')
    parser.add_argument('--graph', '-g', default='F:/code/python/code-graph/output/code-graph.json', help='代码图文件')
    parser.add_argument('--target', '-t', default="com.roncoo.pay.controller.F2FPayController#initPay", help='目标入口方法，如 com.roncoo.pay.controller.F2FPayController#initPay')
    parser.add_argument('--depth', '-d', type=int, default=5, help='BFS 遍历深度')
    parser.add_argument('--output', '-o', default='F:/code/python/code-graph/output/semantic-graph.json', help='输出文件')
    parser.add_argument('--api-key', help='LLM API Key')
    parser.add_argument('--model', default='qwen3-coder-plus', help='LLM 模型')
    parser.add_argument('--workers', type=int, default=5, help='并行工作数')
    parser.add_argument('--dry-run', action='store_true', help='只生成不调用 LLM')
    parser.add_argument('--exclude-methods', default='get,set,is,hashCode,equals,toString,clone,finalize', help='排除的方法名模式（逗号分隔）')
    parser.add_argument('--exclude-classes', default='Exception,Error,Throwable,RuntimeException,抽象,Util,Helper,Common,Constant,Config,VO,BO,DTO,PO,DAO,Entity,Bean,Request,Response,Result,Base', help='排除的类名模式（逗号分隔）')
    
    args = parser.parse_args()
    
    # 方法过滤配置
    exclude_patterns = [p.strip() for p in args.exclude_methods.split(',')]
    
    # 类过滤配置
    exclude_class_patterns = [p.strip() for p in args.exclude_classes.split(',')]
    
    logger.info(f"排除的方法模式: {exclude_patterns}")
    logger.info(f"排除的类模式: {exclude_class_patterns}")
    
    # 构建器
    builder = SemanticGraphBuilder(args.graph)
    
    # 确定目标
    if args.target:
        # 聚焦到指定目标
        nodes, edges = builder.focus_subgraph(args.target, args.depth)
    else:
        # 使用全部节点
        nodes = builder.graph_filter.all_nodes
        edges = builder.graph_filter.all_edges
    
    logger.info(f"处理 {len(nodes)} 个节点...")
    
    # 收集需要处理的节点
    method_nodes = [n for n in nodes if n.get("kind") == "METHOD"]
    class_nodes = [n for n in nodes if n.get("kind") in ("CLASS", "INTERFACE")]
    
    # 过滤需要排除的类
    original_class_count = len(class_nodes)
    class_nodes = [
        n for n in class_nodes
        if not any(p in n.get("className", "") for p in exclude_class_patterns)
    ]
    class_filtered_count = original_class_count - len(class_nodes)
    
    # 方法名模式过滤（仅当所属类匹配类过滤模式时才生效）
    # 例如：VO/DTO/Entity 类的 get/set 方法才过滤，业务类的 get 方法不过滤
    original_count = len(method_nodes)
    
    # 构建类名→是否需要过滤 getter/setter 的映射
    class_needs_method_filter = set()
    for cn in exclude_class_patterns:
        class_needs_method_filter.add(cn)
    
    # 统计被过滤的方法，用于日志输出
    filtered_methods_log = []
    kept_methods_log = []
    
    def should_filter_method(node):
        """判断方法是否应该被过滤"""
        method_name = node.get("methodName", "")
        class_name = node.get("className", "")
        
        # 第一优先级：所属类匹配类过滤模式 → 直接过滤该类所有方法
        class_matches = any(p in class_name for p in exclude_class_patterns)
        if class_matches:
            filtered_methods_log.append(f"[类过滤] {class_name}.{method_name}")
            return True
        
        # 第二优先级：hashCode/equals/toString 等始终过滤
        always_filter = ["hashCode", "equals", "toString", "clone", "finalize"]
        if method_name in always_filter:
            filtered_methods_log.append(f"[始终过滤] {class_name}.{method_name}")
            return True
        
        # 第三优先级：setter 方法全局过滤
        if method_name.startswith("set"):
            filtered_methods_log.append(f"[setter过滤] {class_name}.{method_name}")
            return True
            
        # 第四优先级：getter/is 方法逻辑
        if method_name.startswith("get") or method_name.startswith("is"):
            # 计算行数
            line_start = node.get("lineStart", 0)
            line_end = node.get("lineEnd", 0)
            line_count = line_end - line_start + 1 if line_end >= line_start else 1
            
            # 如果行数很少（<=3行），视为简单 getter，过滤
            # 简单的属性访问通常只有 1-3 行
            if line_count <= 3:
                filtered_methods_log.append(f"[短getter过滤] {class_name}.{method_name} ({line_count}行)")
                return True
            
            # 行数较多的 get/is 方法，可能包含业务逻辑，保留
            kept_methods_log.append(f"[保留-复杂getter] {class_name}.{method_name} ({line_count}行)")
            return False
        
        # 保留
        kept_methods_log.append(f"{class_name}.{method_name}")
        return False
    
    method_nodes = [
        n for n in method_nodes 
        if not should_filter_method(n)
    ]
    filtered_count = original_count - len(method_nodes)
    
    # 打印过滤日志
    logger.info(f"类节点: {len(class_nodes)} (过滤掉 {class_filtered_count} 个)")
    logger.info(f"方法节点: {len(method_nodes)} (过滤掉 {filtered_count} 个)")
    logger.info(f"过滤的类模式: {exclude_class_patterns}")
    logger.info(f"过滤的方法模式: {exclude_patterns}")
    
    # 打印被过滤的方法详情
    if filtered_methods_log:
        logger.info(f"方法过滤详情 (共 {len(filtered_methods_log)} 条记录):")
        for log_entry in filtered_methods_log[:50]:
            logger.info(f"  {log_entry}")
        if len(filtered_methods_log) > 50:
            logger.info(f"  ... 还有 {len(filtered_methods_log) - 50} 条")
    
    # 打印保留的方法（方便审查）
    if kept_methods_log:
        logger.info(f"保留的方法 (共 {len(kept_methods_log)} 个):")
        for log_entry in kept_methods_log[:30]:
            logger.info(f"  [保留] {log_entry}")
        if len(kept_methods_log) > 30:
            logger.info(f"  ... 还有 {len(kept_methods_log) - 30} 个")
    
    # 处理类节点
    class_semantics = {}
    for node in class_nodes:
        class_name = node.get("className", "")
        file_path = node.get("file", "")
        
        if file_path:
            source = builder.read_source_code(node)
            if source:
                fields = builder.extract_class_fields(source, class_name)
                class_semantics[node["id"]] = {
                    "fields": fields,
                    "source": source[:5000]  # 限制源码长度
                }
    
    # 处理方法节点
    semantic_nodes = []
    semantic_edges = []
    processed_ids = []
    failed_ids = []
    
    processed = 0
    for node in method_nodes:
        node_id = node["id"]
        class_name = node.get("className", "")
        method_name = node.get("methodName", "")
        
        logger.info(f"[处理中] {class_name}.{method_name} ({processed+1}/{len(method_nodes)})")
        
        # 读取源码
        source = builder.read_source_code(node)
        method_body = builder.extract_method_body(source, node)
        
        # 获取所在类的属性
        class_id = node_id.split("#")[0] if "#" in node_id else node_id
        class_fields = class_semantics.get(class_id, {}).get("fields", [])
        
        # 构建提示词
        prompt = builder.build_semantic_prompt(node, source, method_body, class_fields)
        
        # 调用 LLM
        if args.dry_run:
            response = '{"description": "dry-run", "input": [], "output": {}, "flow": ""}'
            logger.info(f"[Dry-Run] {node_id}")
        else:
            response = call_llm(prompt, args.api_key, args.model)
            # 打印 LLM 原始输出
            logger.info(f"[LLM原始输出] {node_id}:\n{response[:500]}...")
            if "API调用失败" in response or "API返回异常" in response:
                failed_ids.append(node_id)
                logger.warning(f"[LLM失败] {node_id}")
            else:
                logger.info(f"[LLM成功] {node_id}")
        
        # 解析响应
        semantic = builder.parse_llm_response(response, "METHOD")
        
        # 构建语义节点
        semantic_node = {
            "id": node_id,
            "kind": node.get("kind"),
            "original": node,
            "semantic": semantic
        }
        semantic_nodes.append(semantic_node)
        
        processed_ids.append(node_id)
        processed += 1
        logger.info(f"[进度] {processed}/{len(method_nodes)} ({processed*100//len(method_nodes)}%)")
        
        # 避免 API 限流
        if not args.dry_run and processed % 20 == 0:
            time.sleep(1)
    
    logger.info(f"[完成] 共处理 {len(processed_ids)} 个方法节点")
    if failed_ids:
        logger.warning(f"[失败] {len(failed_ids)} 个节点: {failed_ids[:5]}...")
    
    # 添加类节点
    for node in class_nodes:
        class_id = node["id"]
        class_info = class_semantics.get(class_id, {})
        
        semantic_node = {
            "id": class_id,
            "kind": node.get("kind"),
            "original": node,
            "semantic": {
                "fields": class_info.get("fields", [])
            }
        }
        semantic_nodes.append(semantic_node)
    
    # 复制边
    semantic_edges = edges
    
    # 构建输出
    output = {
        "meta": {
            "target": args.target,
            "depth": args.depth,
            "total_nodes": len(semantic_nodes),
            "total_edges": len(semantic_edges)
        },
        "nodes": semantic_nodes,
        "edges": semantic_edges
    }
    
    # 写入文件
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"语义图已保存到: {args.output}")
    
    # 生成 HTML 可视化
    output_dir = os.path.dirname(args.output) or "."
    try:
        from src.code_graph.output.semantic_html_generator import SemanticHtmlGenerator
        html_path = SemanticHtmlGenerator(output_dir).generate(output)
        logger.info(f"语义图 HTML 已生成: {html_path}")
    except ImportError:
        logger.warning("未找到 SemanticHtmlGenerator，跳过 HTML 生成")


if __name__ == "__main__":
    main()
