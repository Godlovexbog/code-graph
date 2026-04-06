#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Java Code Graph - 入口脚本

用法:
    python main.py [--config CONFIG_PATH]

示例:
    python main.py
    python main.py --config ./config.yaml
"""

import argparse
import logging
import os
import sys
import time

# 确保 src 模块可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.code_graph.scanner.config_loader import ConfigLoader
from src.code_graph.scanner.file_scanner import FileScanner
from src.code_graph.scanner.entry_discovery import discover_from_source
from src.code_graph.parser.java_parser import JavaParser
from src.code_graph.graph.builder import GraphBuilder
from src.code_graph.output.json_exporter import JsonExporter
from src.code_graph.output.html_generator import HtmlGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser_arg = argparse.ArgumentParser(description="Java Code Graph Generator")
    parser_arg.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"),
        help="Path to config.yaml (default: ./config.yaml)",
    )
    args = parser_arg.parse_args()

    start_time = time.time()

    # 1. 加载配置
    logger.info("加载配置: %s", args.config)
    config = ConfigLoader(args.config).load()
    logger.info("目标项目: %s", config.target_project)
    logger.info("扫描包: %s", config.scan_packages)
    logger.info("入口包: %s", config.entry_packages)
    logger.info("入口方法: %s", config.entry_points)

    # Discover entry points from entry_packages
    if config.entry_packages:
        logger.info("自动发现入口方法...")
        discovered = discover_from_source(
            config.entry_packages,
            config.scan_packages,
            config.target_project
        )
        logger.info("发现 %d 个入口方法", len(discovered))
        config.entry_points.extend(discovered)

    # 2. 扫描 Java 文件
    logger.info("开始扫描 Java 文件...")
    scanner = FileScanner(config.target_project, config.scan_packages)
    java_files = scanner.scan()
    logger.info("扫描完成，找到 %d 个目标文件", len(java_files))

    if not java_files:
        logger.warning("没有找到匹配的 Java 文件，请检查 target_project 和 scan_packages 配置")
        sys.exit(1)

    # 3. 解析 AST
    logger.info("开始解析 AST...")
    java_parser = JavaParser()
    all_classes = []
    parsed_count = 0
    skipped_count = 0

    for i, file_path in enumerate(java_files, 1):
        if i % 50 == 0 or i == len(java_files):
            logger.info("解析进度: %d/%d", i, len(java_files))
        classes = java_parser.parse_file(file_path)
        if classes:
            all_classes.extend(classes)
            parsed_count += 1
        else:
            skipped_count += 1

    logger.info("解析完成: %d 个文件成功, %d 个文件跳过", parsed_count, skipped_count)
    logger.info("提取到 %d 个类/接口", len(all_classes))

    # 4. 构建图
    logger.info("开始构建调用图...")
    builder = GraphBuilder(java_parser, config.scan_packages, config.entry_points)
    graph_data = builder.build(all_classes, len(java_files))

    stats = graph_data["meta"]["stats"]
    logger.info("图构建完成: %d 个节点, %d 条边", stats["totalNodes"], stats["totalEdges"])

    # 5. 输出
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    logger.info("输出到: %s", output_dir)

    json_path = JsonExporter(output_dir).export(graph_data)
    logger.info("JSON 已导出: %s", json_path)

    html_path = HtmlGenerator(output_dir).generate(graph_data)
    logger.info("HTML 已生成: %s", html_path)

    elapsed = time.time() - start_time
    logger.info("========================================")
    logger.info("统计信息:")
    logger.info("  扫描文件数: %d", stats["filesScanned"])
    logger.info("  解析文件数: %d", stats["filesParsed"])
    logger.info("  跳过文件数: %d", skipped_count)
    logger.info("  节点数: %d", stats["totalNodes"])
    logger.info("  边数: %d", stats["totalEdges"])
    logger.info("  耗时: %.2f 秒", elapsed)
    logger.info("========================================")
    logger.info("打开 %s 查看可视化结果", html_path)


if __name__ == "__main__":
    main()
