import os
from typing import List, Optional


class FileScanner:
    """递归扫描目标项目目录，收集 .java 文件，按 scan_packages 过滤。"""

    # 标准 Java 源码目录标识
    SRC_MARKERS = [
        os.path.join("src", "main", "java"),
        os.path.join("src", "test", "java"),
        "src",  # 非 Maven 项目可能直接用 src
    ]

    def __init__(self, target_project: str, scan_packages: List[str]):
        self.target_project = os.path.normpath(target_project)
        self.scan_packages = scan_packages

    def scan(self) -> List[str]:
        """返回在 scan_packages 范围内的 .java 文件绝对路径列表。"""
        java_files = []
        for root, _dirs, files in os.walk(self.target_project):
            for fname in files:
                if not fname.endswith(".java"):
                    continue
                full_path = os.path.normpath(os.path.join(root, fname))
                package = self._extract_package(full_path)
                if package and self._matches_scope(package):
                    java_files.append(full_path)
        return java_files

    def _extract_package(self, file_path: str) -> Optional[str]:
        """从文件路径提取 Java 包名。

        对于 Maven 项目: 找到 src/main/java 或 src/test/java 之后的路径段
        对于普通项目: 尝试找到 src 之后的路径段
        """
        rel = os.path.relpath(file_path, self.target_project)
        rel_normalized = rel.replace(os.sep, "/")  # 统一用 / 匹配

        for marker in self.SRC_MARKERS:
            marker_normalized = marker.replace(os.sep, "/")
            idx = rel_normalized.find(marker_normalized + "/")
            if idx >= 0:
                # 取 marker 之后的路径部分
                pkg_path = rel_normalized[idx + len(marker_normalized) + 1:]
                # 路径转包名: com/roncoo/pay/MyClass.java -> com.roncoo.pay.MyClass
                package = pkg_path.replace("/", ".")
                if package.endswith(".java"):
                    package = package[:-5]
                return package

        # 兜底: 如果没找到源码目录标识，直接用相对路径
        package = rel.replace(os.sep, ".").replace("/", ".")
        if package.endswith(".java"):
            package = package[:-5]
        return package

    def _matches_scope(self, package: str) -> bool:
        """检查包名是否匹配任意 scan_packages 前缀。"""
        for pkg in self.scan_packages:
            if package == pkg or package.startswith(pkg + "."):
                return True
        return False
