#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point discoverer - auto-discovers Controller methods from annotations."""

import javalang
from typing import List, Set


CONTROLLER_ANNOTATIONS = {
    "Controller", "RestController", 
    "org.springframework.stereotype.Controller",
    "org.springframework.web.bind.annotation.RestController"
}

WEB_METHOD_ANNOTATIONS = {
    "RequestMapping", "GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping",
    "org.springframework.web.bind.annotation.RequestMapping",
    "org.springframework.web.bind.annotation.GetMapping",
    "org.springframework.web.bind.annotation.PostMapping",
    "org.springframework.web.bind.annotation.PutMapping",
    "org.springframework.web.bind.annotation.DeleteMapping",
    "org.springframework.web.bind.annotation.PatchMapping"
}


def is_controller(cls: javalang.tree.ClassDeclaration) -> bool:
    """Check if a class has a Controller annotation."""
    for ann in cls.annotations:
        ann_name = ann.name if ann.name else ""
        if ann_name in CONTROLLER_ANNOTATIONS:
            return True
        if hasattr(ann, 'name') and ann.name and 'Controller' in ann.name:
            return True
    return False


def extract_method_path(annotation, method_obj) -> str:
    """Extract path from method annotation."""
    if not annotation:
        return ""
    
    # Get value from annotation
    if hasattr(annotation, 'element') and annotation.element:
        for elem in annotation.element:
            if elem.name == 'value':
                if hasattr(elem, 'value') and elem.value:
                    if hasattr(elem.value, 'value'):
                        return elem.value.value
                    return str(elem.value)
    
    # Alternative: look for literal in annotation
    if hasattr(annotation, 'children'):
        for child in annotation.children:
            if isinstance(child, javalang.tree.Literal):
                return child.value if child.value else ""
    
    return ""


def discover_entry_points(classes: List, entry_packages: List[str]) -> List[str]:
    """Discover all Controller methods in entry_packages."""
    entry_points: Set[str] = set()
    
    for cls in classes:
        if not isinstance(cls, javalang.tree.ClassDeclaration):
            continue
        
        # Check if class is in entry package
        if not cls.package:
            continue
        
        full_name = f"{cls.package}.{cls.name}"
        if not any(full_name.startswith(ep) for ep in entry_packages):
            continue
        
        # Check if it's a Controller
        if not is_controller(cls):
            continue
        
        # Find all public methods with web annotations
        for method in cls.methods:
            if not method.modifiers or "public" not in method.modifiers:
                continue
            
            # Check for web annotations on method
            has_web_ann = False
            for ann in method.annotations:
                ann_name = ann.name if ann.name else ""
                if ann_name in WEB_METHOD_ANNOTATIONS:
                    has_web_ann = True
                    break
            
            if has_web_ann:
                method_fqn = f"{full_name}#{method.name}"
                entry_points.add(method_fqn)
    
    return sorted(entry_points)


def discover_from_source(entry_packages: List[str], scan_packages: List[str], target_project: str) -> List[str]:
    """Discover entry points directly from source files."""
    import os
    import javalang
    from src.code_graph.scanner.file_scanner import FileScanner
    
    # Scan all files in scan_packages
    scanner = FileScanner(target_project, scan_packages)
    java_files = scanner.scan()
    
    entry_points: Set[str] = set()
    
    for file_path in java_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = javalang.parse.parse(source)
            
            # Find package name
            package_name = None
            for path, node in tree:
                if isinstance(node, javalang.tree.PackageDeclaration):
                    package_name = node.name
                    break
            
            if not package_name:
                continue
            
            for path, node in tree:
                if isinstance(node, javalang.tree.ClassDeclaration):
                    full_name = f"{package_name}.{node.name}"
                    if not any(full_name.startswith(ep) for ep in entry_packages):
                        continue
                    
                    if not is_controller(node):
                        continue
                    
                    for method in node.methods:
                        if not method.modifiers or "public" not in method.modifiers:
                            continue
                        
                        has_web_ann = False
                        for ann in method.annotations:
                            ann_name = ann.name if ann.name else ""
                            if ann_name in WEB_METHOD_ANNOTATIONS:
                                has_web_ann = True
                                break
                        
                        if has_web_ann:
                            method_fqn = f"{full_name}#{method.name}"
                            entry_points.add(method_fqn)
                            
        except Exception:
            continue
    
    return sorted(entry_points)
