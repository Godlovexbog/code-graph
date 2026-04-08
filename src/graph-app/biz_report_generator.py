"""
业务能力报告生成器 - 从 biz-graph.json 生成业务文档
"""
import json
import os
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


def load_biz_graph(filepath: str) -> dict:
    """加载业务能力图"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_l3_nodes(biz_graph: dict) -> list:
    """获取所有 L3 节点"""
    return [n for n in biz_graph.get('nodes', []) if n.get('level') == 3]


def get_node_by_id(biz_graph: dict, node_id: str) -> dict:
    """根据 ID 获取节点"""
    for n in biz_graph.get('nodes', []):
        if n.get('id') == node_id:
            return n
    return None


def generate_report_prompt(l3_node: dict, biz_graph: dict) -> str:
    """生成报告提示词"""
    
    # 获取规则列表内容
    rules_content = []
    for rule_id in l3_node.get('rules', []):
        rule_node = get_node_by_id(biz_graph, rule_id)
        if rule_node:
            rules_content.append({
                'id': rule_id,
                'name': rule_node.get('name', ''),
                'content': rule_node.get('content', ''),
                'type': rule_node.get('rule_type', '')
            })
    
    # 获取实体列表内容
    entities_content = []
    for entity_id in l3_node.get('entities', []):
        entity_node = get_node_by_id(biz_graph, entity_id)
        if entity_node:
            entities_content.append({
                'id': entity_id,
                'name': entity_node.get('name', ''),
                'type': entity_node.get('class_type', '')
            })
    
    # 获取活动列表内容
    activities_content = []
    for activity_id in l3_node.get('activities', []):
        activity_node = get_node_by_id(biz_graph, activity_id)
        if activity_node:
            activities_content.append({
                'id': activity_id,
                'name': activity_node.get('name', ''),
                'description': activity_node.get('description', '')[:100]
            })
    
    rules_json = json.dumps(rules_content, ensure_ascii=False, indent=2)
    entities_json = json.dumps(entities_content, ensure_ascii=False, indent=2)
    activities_json = json.dumps(activities_content, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个业务分析师和架构师。请根据以下业务能力图信息，生成一份完整的业务能力说明文档。

## 业务能力图信息

### 1. 流程图 (Mermaid格式)
{l3_node.get('flow_chart', '')}

### 2. 活动列表 (共 {len(activities_content)} 个)
{activities_json}

### 3. 规则列表 (共 {len(rules_content)} 条)
{rules_json}

### 4. 关联实体列表 (共 {len(entities_content)} 个)
{entities_json}

## 要求

请生成以下格式的业务说明文档，使用Markdown格式：

# {l3_node.get('name', '业务能力报告')}

## 一、业务概述
（用100字以内描述这个业务流程的核心功能）

## 二、活动列表
（列出所有活动节点，包含ID、名称、描述）

## 三、业务流程图
（展示Mermaid流程图）

## 四、业务规则汇总
### 4.1 验证规则
（列出所有验证类型的业务规则）

### 4.2 安全规则
（列出所有安全类型的业务规则）

### 4.3 业务规则
（列出其他业务规则）

## 五、关联实体
### 5.1 实体列表
（列出所有关联的实体及其类型）

## 六、总结
（描述该业务流程的重要性和业务价值）

请直接输出完整的业务说明文档，使用Markdown格式。"""
    
    return prompt


def generate_report(l3_node: dict, biz_graph: dict) -> str:
    """生成业务报告"""
    
    print(f"正在为 {l3_node.get('name')} 生成业务报告...")
    
    prompt = generate_report_prompt(l3_node, biz_graph)
    
    print("调用 LLM 生成报告...")
    report = call_llm(prompt)
    
    if not report:
        return "LLM 调用失败，请检查网络和 API Key"
    
    return report


def main():
    input_file = "F:/code/python/code-graph/output/biz-graph.json"
    output_dir = "F:/code/python/code-graph/output"
    
    print(f"读取业务能力图: {input_file}")
    biz_graph = load_biz_graph(input_file)
    
    # 获取所有 L3 节点
    l3_nodes = get_l3_nodes(biz_graph)
    print(f"找到 {len(l3_nodes)} 个 L3 流程节点")
    
    for l3 in l3_nodes:
        l3_name = l3.get('name', 'unknown')
        # 生成文件名
        safe_name = l3_name.replace('/', '_').replace('#', '_')
        output_file = os.path.join(output_dir, f"biz-report-{safe_name}.md")
        
        # 生成报告
        report = generate_report(l3, biz_graph)
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"报告已生成: {output_file}")
    
    print(f"\n完成! 共生成 {len(l3_nodes)} 份业务报告")


if __name__ == "__main__":
    main()
