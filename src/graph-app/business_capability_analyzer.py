"""
业务能力分析器 - 聚合语义图生成业务分析报告
"""
import json
import os
import sys
from collections import defaultdict
import requests


def call_llm(prompt: str, api_key: str = None, model: str = "qwen3-coder-plus") -> str:
    """调用 LLM API - 千问"""
    if not api_key:
        api_key = os.environ.get("QWQ_API_KEY", "")
    if not api_key:
        api_key = "sk-3c4f02367af44ee28f081f495a80c8d5"
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "max_tokens": 4000,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=180)
        response.raise_for_status()
        result = response.json()
        
        if "output" in result and "text" in result["output"]:
            return result["output"]["text"]
        elif "output" in result and "choices" in result["output"]:
            if result["output"].get("choices"):
                return result["output"]["choices"][0]["message"]["content"]
        elif "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            print(f"Warning: API response format unexpected: {result}")
            return ""
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return ""


def load_semantic_graph(filepath: str) -> dict:
    """加载语义图"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_call_chain(graph: dict) -> dict:
    """构建调用链"""
    call_edges = [e for e in graph['edges'] if e.get('type') == 'CALL']
    adj = defaultdict(list)
    for e in call_edges:
        adj[e['from']].append(e['to'])
    return adj


def get_entry_method(graph: dict) -> dict:
    """获取入口方法"""
    for n in graph['nodes']:
        if n.get('original', {}).get('isEntry'):
            return n
    return graph['nodes'][0] if graph['nodes'] else None


def generate_aggregate_prompt(nodes: list) -> str:
    """生成聚合提示词"""
    
    # 整理所有方法的语义信息
    methods_info = []
    for n in nodes:
        sem = n.get('semantic', {})
        orig = n.get('original', {})
        methods_info.append({
            'method': n['id'].split('#')[-1],
            'class': orig.get('className', ''),
            'description': sem.get('description', ''),
            'flow': sem.get('flow', ''),
            'flow_chart': sem.get('flow_chart', ''),
            'business_rules': sem.get('business_rules', []),
            'input': sem.get('input', []),
            'output': sem.get('output', {})
        })
    
    methods_json = json.dumps(methods_info, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个业务分析师和架构师。请根据以下27个方法的语义信息，生成一个完整的业务能力分析报告。

## 方法列表（JSON格式）:
{methods_json}

## 要求:

1. **汇总流程图**: 汇总所有方法的flow_chart，生成一个完整的业务主流程图（Mermaid格式）

2. **业务规则列表**: 汇总所有方法的business_rules，去重并按类别分组

3. **关联实体列表**: 从input/output中提取所有关联的业务实体（Entity），列出实体名称和含义

请生成以下格式的报告（Markdown）:

# 业务能力分析报告

## 一、业务概述
（用100字以内描述这个入口方法所在的业务领域）

## 二、汇总流程图
```mermaid
graph TD
    ... (完整的业务流程图)
```

## 三、业务规则汇总
### 3.1 参数校验规则
- ...

### 3.2 安全验证规则
- ...

### 3.3 交易处理规则
- ...

### 3.4 其他规则
- ...

## 四、关联实体列表
| 实体 | 类型 | 含义 |
|------|------|------|
| ... | ... | ... |

## 五、输入输出语义
### 输入
...

### 输出
...

请直接输出报告，不要添加额外解释。"""
    
    return prompt.replace('_methods_json', methods_json)


def generate_report(graph: dict) -> str:
    """生成分析报告"""
    nodes = graph['nodes']
    
    print(f"开始生成报告，共 {len(nodes)} 个方法...")
    
    prompt = generate_aggregate_prompt(nodes)
    
    print("调用 LLM 生成报告...")
    report = call_llm(prompt)
    
    if not report:
        return "LLM 调用失败，请检查网络和 API Key"
    
    return report


def main():
    input_file = "F:/code/python/code-graph/output/semantic-graph.json"
    output_file = "F:/code/python/code-graph/output/业务能力分析报告.md"
    
    print(f"读取语义图: {input_file}")
    graph = load_semantic_graph(input_file)
    
    print(f"入口方法: {graph['meta']['target']}")
    print(f"节点数: {len(graph['nodes'])}")
    print(f"边数: {len(graph['edges'])}")
    
    report = generate_report(graph)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已生成: {output_file}")
    print(f"报告长度: {len(report)} 字符")


if __name__ == "__main__":
    main()