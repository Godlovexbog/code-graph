import json
import os
from typing import Dict


class JsonExporter:
    """将图数据输出为标准 JSON 格式。"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def export(self, graph_data: Dict) -> str:
        """导出 JSON 文件，返回文件路径。"""
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "graph.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        return output_path
