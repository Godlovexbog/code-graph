import json
import os
from typing import Dict


class SemanticHtmlGenerator:
    """生成基于 ECharts 的语义图 HTML 可视化页面。"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate(self, graph_data: Dict) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "semantic-graph.html")
        graph_json = json.dumps(graph_data, ensure_ascii=False)
        html_content = self._build_html(graph_json)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    def _build_html(self, graph_json: str) -> str:
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Semantic Graph Visualizer</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#0d1117;color:#c9d1d9;height:100vh;display:flex;flex-direction:column;overflow:hidden}}
#header{{background:#161b22;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;gap:12px;border-bottom:1px solid #30363d}}
#header .left{{display:flex;align-items:center;gap:12px}}
#header h1{{font-size:15px;font-weight:500;color:#58a6ff;white-space:nowrap}}
#header .stats{{font-size:12px;color:#8b949e}}
#header .stats span{{color:#c9d1d9;font-weight:bold}}
#search-box{{display:flex;align-items:center;gap:4px}}
#search-box input{{padding:4px 8px;background:#0d1117;border:1px solid #30363d;border-radius:4px;font-size:12px;width:180px;outline:none;color:#c9d1d9}}
#search-box input:focus{{border-color:#58a6ff}}
#search-box button{{padding:4px 8px;background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:4px;cursor:pointer;font-size:11px}}
#search-box button:hover{{background:#58a6ff;border-color:#58a6ff}}
#main{{display:flex;flex:1;overflow:hidden}}
#sidebar{{width:200px;background:#161b22;border-right:1px solid #30363d;padding:12px;overflow-y:auto;flex-shrink:0}}
#sidebar h3{{font-size:12px;color:#58a6ff;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #30363d;text-transform:uppercase;letter-spacing:0.5px}}
#sidebar .filter-group{{margin-bottom:12px}}
#sidebar .filter-group label{{display:flex;align-items:center;gap:4px;font-size:11px;color:#8b949e;padding:2px 0;cursor:pointer}}
#sidebar .filter-group input[type=checkbox]{{accent-color:#58a6ff}}
#sidebar .color-dot{{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}}
#chart{{flex:1;background:#0d1117}}
#detail{{width:420px;background:#161b22;border-left:1px solid #30363d;padding:12px;overflow-y:auto;flex-shrink:0;display:none}}
#detail.visible{{display:block}}
#detail h3{{font-size:13px;color:#58a6ff;margin-bottom:8px;word-break:break-all;line-height:1.4}}
#detail .detail-section{{margin-bottom:10px}}
#detail .detail-section h4{{font-size:11px;color:#8b949e;margin-bottom:3px;font-weight:600;text-transform:uppercase}}
#detail .detail-section p,#detail .detail-section div{{font-size:12px;color:#c9d1d9;line-height:1.5}}
#detail .tag{{display:inline-block;background:#1a3a6e;color:#58a6ff;padding:1px 6px;border-radius:8px;font-size:10px;margin:1px 2px 1px 0}}
#detail .tag.entry{{background:#3d1a1a;color:#f85149}}
#detail .tag.interface{{background:#3d2e00;color:#d29922}}
#detail .tag.method{{background:#0d2e1a;color:#4ecca3}}
#detail .tag.class-tag{{background:#0d1a3d;color:#58a6ff}}
#detail .close-btn{{float:right;background:none;border:none;font-size:16px;cursor:pointer;color:#8b949e}}
#detail .close-btn:hover{{color:#f85149}}
#detail .semantic-desc{{background:#0d1117;padding:8px;border-radius:4px;border-left:3px solid #58a6ff;margin-bottom:8px}}
#detail .param-item{{background:#0d1117;padding:4px 8px;margin:2px 0;border-radius:4px;font-size:11px}}
#detail .param-item .param-name{{color:#4ecca3;font-weight:bold}}
#detail .param-item .param-type{{color:#d29922}}
#detail .flow-text{{background:#0d1117;padding:6px 8px;border-radius:4px;font-size:11px;white-space:pre-wrap;max-height:150px;overflow-y:auto}}
#detail .rule-item{{background:#1a2a1a;padding:2px 6px;margin:2px 0;border-radius:4px;font-size:11px;border-left:2px solid #4ecca3}}
#detail .mermaid-container{{background:#0d1117;padding:8px;border-radius:4px;overflow-x:auto}}
#detail .mermaid-container svg{{max-width:100%;height:auto}}
#detail .mermaid-code{{background:#0d1117;padding:6px 8px;border-radius:4px;font-family:monospace;font-size:10px;max-height:200px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}}
#detail .tab-bar{{display:flex;gap:4px;margin-bottom:8px;border-bottom:1px solid #30363d;padding-bottom:4px}}
#detail .tab-btn{{background:none;border:none;color:#8b949e;padding:4px 8px;cursor:pointer;font-size:11px;border-radius:4px}}
#detail .tab-btn.active{{background:#21262d;color:#c9d1d9}}
#detail .tab-content{{display:none}}
#detail .tab-content.active{{display:block}}
#loading{{position:fixed;top:0;left:0;right:0;bottom:0;background:#0d1117;display:flex;align-items:center;justify-content:center;z-index:9999;flex-direction:column}}
#loading .spinner{{width:36px;height:36px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin 0.8s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
#loading p{{margin-top:12px;color:#8b949e;font-size:13px}}
</style>
</head>
<body>
<div id="loading"><div class="spinner"></div><p>正在加载语义图...</p></div>
<div id="header">
  <div class="left">
    <h1>Semantic Graph</h1>
    <div class="stats" id="stats"></div>
  </div>
  <div id="search-box">
    <input type="text" id="search-input" placeholder="搜索方法/类..." onkeydown="if(event.key==='Enter')searchNode()">
    <button onclick="searchNode()">聚焦</button>
    <button onclick="resetHighlight()">重置</button>
  </div>
</div>
<div id="main">
  <div id="sidebar">
    <div class="filter-group"><h3>节点类型</h3><div id="node-filters"></div></div>
    <div class="filter-group"><h3>边类型</h3><div id="edge-filters"></div></div>
  </div>
  <div id="chart"></div>
  <div id="detail"><button class="close-btn" onclick="closeDetail()">&times;</button><div id="detail-content"></div></div>
</div>
<script>
var _initDone = false;
function doInit() {{
    if (_initDone || typeof echarts === 'undefined') return;
    _initDone = true;
    document.getElementById('loading').style.display = 'none';

    var graphData = {graph_json};
    var stats = graphData.meta;
    document.getElementById('stats').innerHTML =
        '节点: <span>' + stats.total_nodes + '</span> &nbsp; 边: <span>' + stats.total_edges + '</span>';

    var nodeTypeConfig = {{
        'ENTRY': {{ label: '入口方法', color: '#f85149', symbolSize: 50 }},
        'METHOD': {{ label: '方法', color: '#4ecca3', symbolSize: 35 }},
        'CLASS': {{ label: '类', color: '#58a6ff', symbolSize: 45 }},
        'INTERFACE': {{ label: '接口', color: '#d29922', symbolSize: 45 }},
    }};
    var edgeTypeConfig = {{
        'CALL': {{ label: '调用', color: '#f0883e' }},
        'REFERENCES': {{ label: '引用', color: '#06b6d4' }},
        'IMPLEMENTS': {{ label: '实现', color: '#d29922' }},
        'OVERRIDE': {{ label: '重写', color: '#ec4899' }},
        'EXTENDS': {{ label: '继承', color: '#a371f7' }},
        'CONTAINS': {{ label: '包含', color: '#484f58' }},
    }};

    var nodeTypeCounts = {{}};
    var edgeTypeCounts = {{}};
    graphData.nodes.forEach(function(n) {{
        var raw = n.original || n;
        var key = raw.kind;
        if (key === 'CLASS' && raw.isInterface) key = 'INTERFACE';
        if (key === 'METHOD' && raw.isEntry) key = 'ENTRY';
        nodeTypeCounts[key] = (nodeTypeCounts[key] || 0) + 1;
    }});
    graphData.edges.forEach(function(e) {{
        edgeTypeCounts[e.type] = (edgeTypeCounts[e.type] || 0) + 1;
    }});

    var nodeVisibility = {{}};
    var edgeVisibility = {{}};
    Object.keys(nodeTypeConfig).forEach(function(k) {{ nodeVisibility[k] = true; }});
    Object.keys(edgeTypeConfig).forEach(function(k) {{ edgeVisibility[k] = (k === 'CALL' || k === 'EXTENDS' || k === 'IMPLEMENTS'); }});

    var allNodes = [];
    var nodeSet = new Set();
    graphData.nodes.forEach(function(node) {{
        var raw = node.original || node;
        var kind = raw.kind;
        if (kind === 'CLASS' && raw.isInterface) kind = 'INTERFACE';
        if (kind === 'METHOD' && raw.isEntry) kind = 'ENTRY';
        var cfg = nodeTypeConfig[kind] || nodeTypeConfig['METHOD'];
        nodeSet.add(node.id);
        allNodes.push({{
            id: node.id,
            name: raw.kind === 'CLASS' || raw.kind === 'INTERFACE' ? raw.className : (raw.className + '#' + raw.methodName),
            category: kind,
            symbolSize: cfg.symbolSize,
            itemStyle: {{ color: cfg.color, borderColor: '#0d1117', borderWidth: 1 }},
            _kind: kind, _rawKind: raw.kind, _data: node, _raw: raw, _semantic: node.semantic || {{}}
        }});
    }});

    var allEdges = [];
    graphData.edges.forEach(function(edge) {{
        if (nodeSet.has(edge.from) && nodeSet.has(edge.to)) {{
            var cfg = edgeTypeConfig[edge.type] || {{ color: '#666' }};
            allEdges.push({{
                source: edge.from, target: edge.to,
                lineStyle: {{ color: cfg.color, width: edge.type === 'CALL' ? 2.5 : 1.5, curveness: 0.15 }},
                _type: edge.type, _data: edge
            }});
        }}
    }});

    var categories = Object.keys(nodeTypeConfig).map(function(k) {{
        return {{ name: k, itemStyle: {{ color: nodeTypeConfig[k].color }} }};
    }});

    var currentNodes = allNodes.slice();
    var currentEdges = allEdges.slice();
    var chart = echarts.init(document.getElementById('chart'));

    var nodeFiltersDiv = document.getElementById('node-filters');
    Object.keys(nodeTypeConfig).forEach(function(key) {{
        var cfg = nodeTypeConfig[key];
        var count = nodeTypeCounts[key] || 0;
        var lbl = document.createElement('label');
        lbl.innerHTML = '<input type="checkbox" checked data-node-type="' + key + '" onchange="toggleNodeType(this)">' +
            '<span class="color-dot" style="background:' + cfg.color + '"></span>' +
            cfg.label + ' <span style="color:#484f58">(' + count + ')</span>';
        nodeFiltersDiv.appendChild(lbl);
    }});

    var edgeFiltersDiv = document.getElementById('edge-filters');
    Object.keys(edgeTypeConfig).forEach(function(key) {{
        var cfg = edgeTypeConfig[key];
        var count = edgeTypeCounts[key] || 0;
        var checked = edgeVisibility[key] ? 'checked' : '';
        var lbl = document.createElement('label');
        lbl.innerHTML = '<input type="checkbox" ' + checked + ' data-edge-type="' + key + '" onchange="toggleEdgeType(this)">' +
            '<span class="color-dot" style="background:' + cfg.color + '"></span>' +
            cfg.label + ' <span style="color:#484f58">(' + count + ')</span>';
        edgeFiltersDiv.appendChild(lbl);
    }});

    function renderChart(nodes, edges) {{
        chart.setOption({{
            tooltip: {{
                formatter: function(p) {{
                    if (p.dataType === 'node') {{
                        var sem = p.data._semantic;
                        var desc = sem.description || '';
                        return '<b>' + p.name + '</b><br/>类型: ' + p.data._kind + (desc ? '<br/>' + desc.substring(0, 50) + '...' : '');
                    }}
                    if (p.dataType === 'edge') return '<b>' + p.data._type + '</b><br/>' + p.data.source + ' → ' + p.data.target;
                    return '';
                }}
            }},
            categories: categories,
            series: [{{
                type: 'graph', layout: 'force', roam: true, draggable: true,
                data: nodes, links: edges, categories: categories,
                label: {{ show: true, position: 'bottom', formatter: '{{b}}', fontSize: 9, color: '#c9d1d9', overflow: 'break' }},
                force: {{ repulsion: 2000, gravity: 0.02, edgeLength: [120, 400], layoutAnimation: true, friction: 0.4 }},
                lineStyle: {{ curveness: 0.1, width: 1 }},
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 12],
                emphasis: {{ focus: 'adjacency', lineStyle: {{ width: 3 }}, label: {{ fontSize: 11, fontWeight: 'bold' }}, itemStyle: {{ borderColor: '#fff', borderWidth: 2 }} }},
                select: {{ itemStyle: {{ borderWidth: 3, borderColor: '#fff' }}, label: {{ fontSize: 12, fontWeight: 'bold' }} }}
            }}]
        }}, false);
    }}

    function applyFilters() {{
        var typeVisible = allNodes.filter(function(n) {{ return nodeVisibility[n._kind]; }});
        var typeVisibleIds = new Set(typeVisible.map(function(n) {{ return n.id; }}));

        var typeVisibleEdges = allEdges.filter(function(e) {{
            return edgeVisibility[e._type] && typeVisibleIds.has(e.source) && typeVisibleIds.has(e.target);
        }});

        var connectionTypes = new Set(['CALL', 'REFERENCES', 'IMPLEMENTS', 'OVERRIDE', 'EXTENDS', 'CONTAINS']);
        var connectedIds = new Set();
        typeVisibleEdges.forEach(function(e) {{
            if (connectionTypes.has(e._type)) {{
                connectedIds.add(e.source);
                connectedIds.add(e.target);
            }}
        }});

        var entryIds = new Set();
        typeVisible.forEach(function(n) {{ if (n._raw.isEntry) entryIds.add(n.id); }});

        var finalNodes = typeVisible.filter(function(n) {{
            return connectedIds.has(n.id) || entryIds.has(n.id);
        }});
        var finalNodeIds = new Set(finalNodes.map(function(n) {{ return n.id; }}));
        var finalEdges = typeVisibleEdges.filter(function(e) {{
            return finalNodeIds.has(e.source) && finalNodeIds.has(e.target);
        }});

        currentNodes = finalNodes;
        currentEdges = finalEdges;

        document.getElementById('stats').innerHTML =
            '节点: <span>' + finalNodes.length + '</span> &nbsp; 边: <span>' + finalEdges.length +
            '</span> &nbsp; <span style="color:#484f58">(隐藏 ' + (stats.total_nodes - finalNodes.length) + ' 个孤立节点)</span>';

        renderChart(finalNodes, finalEdges);
    }}

    chart.on('click', function(params) {{
        if (params.dataType === 'node') {{
            showNodeDetail(params.data);
        }} else if (params.dataType === 'edge') {{
            showEdgeDetail(params.data);
        }}
    }});

    chart.on('dblclick', function(params) {{
        if (params.dataType === 'node') resetHighlight();
    }});

    window.toggleNodeType = function(cb) {{
        nodeVisibility[cb.dataset.nodeType] = cb.checked;
        if (window._focusedTarget) {{
            applyFocusFilter(window._focusedTarget);
        }} else {{
            applyFilters();
        }}
    }};
    window.toggleEdgeType = function(cb) {{
        edgeVisibility[cb.dataset.edgeType] = cb.checked;
        if (window._focusedTarget) {{
            applyFocusFilter(window._focusedTarget);
        }} else {{
            applyFilters();
        }}
    }};
    
    function applyFocusFilter(target) {{
        var activeAdj = {{}};
        allEdges.forEach(function(e) {{
            if (edgeVisibility[e._type]) {{
                if (!activeAdj[e.source]) activeAdj[e.source] = new Set();
                activeAdj[e.source].add(e.target);
            }}
        }});
        
        var visited = new Set();
        var queue = [target.id];
        visited.add(target.id);
        while (queue.length > 0) {{
            var curr = queue.shift();
            var neighbors = activeAdj[curr] || new Set();
            neighbors.forEach(function(n) {{
                if (!visited.has(n)) {{
                    visited.add(n);
                    queue.push(n);
                }}
            }});
        }}
        
        var classId = target.id.split('#')[0];
        visited.add(classId);
        
        var focusNodes = allNodes.filter(function(n) {{ 
            return visited.has(n.id) && nodeVisibility[n._kind]; 
        }});
        var focusNodeIds = new Set(focusNodes.map(function(n) {{ return n.id; }}));
        
        var focusEdges = allEdges.filter(function(e) {{
            return edgeVisibility[e._type] && focusNodeIds.has(e.source) && focusNodeIds.has(e.target);
        }});
        
        document.getElementById('stats').innerHTML =
            '节点: <span>' + focusNodes.length + '</span> &nbsp; 边: <span>' + focusEdges.length +
            '</span> &nbsp; <span style="color:#484f58">(入口: ' + target.name + ')</span>';
        
        renderChart(focusNodes, focusEdges);
    }}

    window.resetHighlight = function() {{
        document.getElementById('detail').classList.remove('visible');
        applyFilters();
    }};

    window.closeDetail = function() {{
        document.getElementById('detail').classList.remove('visible');
        resetHighlight();
    }};

    function showNodeDetail(data) {{
        var raw = data._raw;
        var sem = data._semantic;
        var c = document.getElementById('detail-content');
        var h = '<h3>' + data.name + '</h3>';
        h += '<div style="margin-bottom:8px">';
        if (raw.isEntry) h += '<span class="tag entry">入口方法</span>';
        if (raw.isInterface) h += '<span class="tag interface">接口</span>';
        h += '<span class="tag ' + (raw.kind === 'CLASS' ? 'class-tag' : 'method') + '">' + raw.kind + '</span>';
        h += '</div>';

        // Tab bar
        var hasSemantic = sem && (sem.description || sem.input || sem.output || sem.flow || sem.business_rules || sem.flow_chart);
        if (hasSemantic) {{
            h += '<div class="tab-bar">';
            h += '<button class="tab-btn active" data-tab="tab-code" onclick="switchTab(this)">代码信息</button>';
            h += '<button class="tab-btn" data-tab="tab-semantic" onclick="switchTab(this)">语义分析</button>';
            h += '</div>';
        }}

        // Tab 1: Code Info (ALL fields)
        h += '<div id="tab-code" class="tab-content active">';
        if (raw.kind === 'METHOD') {{
            if (raw.className) h += '<div class="detail-section"><h4>类名</h4><p>' + raw.className + '</p></div>';
            if (raw.methodName) h += '<div class="detail-section"><h4>方法名</h4><p>' + raw.methodName + '</p></div>';
            if (raw.returnType) h += '<div class="detail-section"><h4>返回类型</h4><p>' + raw.returnType + '</p></div>';
            if (raw.parameters && raw.parameters.length) {{
                h += '<div class="detail-section"><h4>参数</h4><div>';
                raw.parameters.forEach(function(p) {{ h += '<span class="tag">' + p.type + ' ' + p.name + '</span>'; }});
                h += '</div></div>';
            }}
            if (raw.annotations && raw.annotations.length) {{
                h += '<div class="detail-section"><h4>注解</h4><div>';
                raw.annotations.forEach(function(a) {{ h += '<span class="tag">' + a + '</span>'; }});
                h += '</div></div>';
            }}
            if (raw.modifiers && raw.modifiers.length) h += '<div class="detail-section"><h4>修饰符</h4><p>' + raw.modifiers.join(', ') + '</p></div>';
            if (raw.file) {{
                h += '<div class="detail-section"><h4>文件</h4><p style="font-size:11px;word-break:break-all">' + raw.file;
                if (raw.lineStart) h += ':' + raw.lineStart + '-' + (raw.lineEnd || raw.lineStart);
                h += '</p></div>';
            }}
            h += '<div class="detail-section"><h4>节点ID</h4><p style="font-size:10px;word-break:break-all;color:#8b949e">' + (raw.id || data.id) + '</p></div>';
            h += '<div class="detail-section"><h4>是否入口</h4><p>' + (raw.isEntry ? '是' : '否') + '</p></div>';
        }} else {{
            if (raw.package) h += '<div class="detail-section"><h4>包</h4><p>' + raw.package + '</p></div>';
            if (raw.className) h += '<div class="detail-section"><h4>类名</h4><p>' + raw.className + '</p></div>';
            if (raw.modifiers && raw.modifiers.length) h += '<div class="detail-section"><h4>修饰符</h4><p>' + raw.modifiers.join(', ') + '</p></div>';
            if (raw.superClass) h += '<div class="detail-section"><h4>父类</h4><p>' + raw.superClass + '</p></div>';
            if (raw.interfaces && raw.interfaces.length) {{
                h += '<div class="detail-section"><h4>实现接口</h4><div>';
                raw.interfaces.forEach(function(i) {{ h += '<span class="tag">' + i + '</span>'; }});
                h += '</div></div>';
            }}
            if (raw.annotations && raw.annotations.length) {{
                h += '<div class="detail-section"><h4>注解</h4><div>';
                raw.annotations.forEach(function(a) {{ h += '<span class="tag">' + a + '</span>'; }});
                h += '</div></div>';
            }}
            if (raw.file) h += '<div class="detail-section"><h4>文件</h4><p style="font-size:11px;word-break:break-all">' + raw.file + '</p></div>';
            h += '<div class="detail-section"><h4>节点ID</h4><p style="font-size:10px;word-break:break-all;color:#8b949e">' + (raw.id || data.id) + '</p></div>';
        }}
        h += '</div>';

        // Tab 2: Semantic Info (ALL fields + rendered Mermaid)
        if (hasSemantic) {{
            h += '<div id="tab-semantic" class="tab-content">';
            if (sem.description) {{
                h += '<div class="detail-section"><h4>方法描述</h4><div class="semantic-desc">' + sem.description + '</div></div>';
            }}
            if (sem.input && sem.input.length) {{
                h += '<div class="detail-section"><h4>输入参数</h4>';
                sem.input.forEach(function(inp) {{
                    h += '<div class="param-item"><span class="param-name">' + inp.param + '</span> <span class="param-type">(' + inp.type + ')</span>: ' + (inp.meaning || '') + '</div>';
                }});
                h += '</div>';
            }}
            if (sem.output) {{
                h += '<div class="detail-section"><h4>输出</h4><div class="param-item"><span class="param-type">' + (sem.output.type || '') + '</span>: ' + (sem.output.meaning || '') + '</div></div>';
            }}
            if (sem.flow) {{
                h += '<div class="detail-section"><h4>业务流程</h4><div class="flow-text">' + sem.flow + '</div></div>';
            }}
            if (sem.business_rules && sem.business_rules.length) {{
                h += '<div class="detail-section"><h4>业务规则</h4>';
                sem.business_rules.forEach(function(rule) {{
                    h += '<div class="rule-item">' + rule + '</div>';
                }});
                h += '</div>';
            }}
            if (sem.flow_chart) {{
                var mermaidId = 'mermaid_' + raw.id.replace(/[^a-zA-Z0-9]/g, '_');
                h += '<div class="detail-section"><h4>流程图</h4>';
                h += '<div class="mermaid-container">';
                h += '<div class="mermaid" id="' + mermaidId + '">' + sem.flow_chart + '</div>';
                h += '</div></div>';
            }}
            // Show all other semantic fields
            var knownKeys = ['description', 'input', 'output', 'flow', 'business_rules', 'flow_chart', 'fields', 'responsibilities', 'dependencies'];
            Object.keys(sem).forEach(function(key) {{
                if (knownKeys.indexOf(key) === -1 && sem[key]) {{
                    h += '<div class="detail-section"><h4>' + key + '</h4>';
                    if (typeof sem[key] === 'object') {{
                        h += '<pre style="font-size:10px;background:#0d1117;padding:6px;border-radius:4px;overflow-x:auto">' + JSON.stringify(sem[key], null, 2) + '</pre>';
                    }} else {{
                        h += '<p>' + sem[key] + '</p>';
                    }}
                    h += '</div>';
                }}
            }});
            h += '</div>';
        }}

        c.innerHTML = h;
        document.getElementById('detail').classList.add('visible');

        // 如果语义 Tab 是默认激活的且有流程图，立即渲染
        if (hasSemantic && sem.flow_chart) {{
            setTimeout(function() {{
                if (typeof mermaid !== 'undefined') {{
                    var activeTab = document.getElementById('tab-semantic');
                    if (activeTab && activeTab.classList.contains('active')) {{
                        var mermaids = activeTab.querySelectorAll('.mermaid:not([data-processed])');
                        mermaids.forEach(function(el) {{
                            el.setAttribute('data-processed', 'true');
                            try {{
                                mermaid.render('msvg_' + Date.now() + '_' + Math.random().toString(36).substr(2,5), el.textContent).then(function(result) {{
                                    el.innerHTML = result.svg;
                                }});
                            }} catch(e) {{
                                console.error('Mermaid error:', e);
                            }}
                        }});
                    }}
                }}
            }}, 200);
        }}
    }}

    window.switchTab = function(btn) {{
        var tabId = btn.dataset.tab;
        var tabBar = btn.parentElement;
        tabBar.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
        btn.classList.add('active');
        var parent = tabBar.parentElement;
        parent.querySelectorAll('.tab-content').forEach(function(tc) {{ tc.classList.remove('active'); }});
        document.getElementById(tabId).classList.add('active');
        
        // 切换到语义 Tab 时渲染 Mermaid
        if (tabId === 'tab-semantic' && typeof mermaid !== 'undefined') {{
            setTimeout(function() {{
                var activeTab = document.getElementById(tabId);
                var mermaids = activeTab.querySelectorAll('.mermaid:not([data-processed])');
                mermaids.forEach(function(el) {{
                    el.setAttribute('data-processed', 'true');
                    try {{
                        mermaid.render('msvg_' + Date.now() + '_' + Math.random().toString(36).substr(2,5), el.textContent).then(function(result) {{
                            el.innerHTML = result.svg;
                        }});
                    }} catch(e) {{
                        console.error('Mermaid error:', e);
                    }}
                }});
            }}, 100);
        }}
    }};

    function showEdgeDetail(data) {{
        var d = data._data;
        var c = document.getElementById('detail-content');
        var h = '<h3>' + data._type + '</h3>';
        h += '<div class="detail-section"><h4>源</h4><p style="font-size:11px;word-break:break-all">' + data.source + '</p></div>';
        h += '<div class="detail-section"><h4>目标</h4><p style="font-size:11px;word-break:break-all">' + data.target + '</p></div>';
        if (d.callSite) h += '<div class="detail-section"><h4>调用代码</h4><p style="font-family:monospace;font-size:11px;background:#0d1117;padding:4px 6px;border-radius:4px">' + d.callSite + '</p></div>';
        if (d.line) h += '<div class="detail-section"><h4>行号</h4><p>' + d.line + '</p></div>';
        if (d.usage) h += '<div class="detail-section"><h4>引用方式</h4><p>' + d.usage + '</p></div>';
        c.innerHTML = h;
        document.getElementById('detail').classList.add('visible');
    }}

    window.searchNode = function() {{
        var q = document.getElementById('search-input').value.trim().toLowerCase();
        if (!q) {{ showAllNodes(); return; }}
        
        var entryMatched = allNodes.filter(function(n) {{
            return n._raw.isEntry && (n.name.toLowerCase().includes(q) || n.id.toLowerCase().includes(q));
        }});
        
        var matched;
        if (entryMatched.length) {{
            matched = entryMatched;
        }} else {{
            matched = allNodes.filter(function(n) {{
                return n.name.toLowerCase().includes(q) || n.id.toLowerCase().includes(q);
            }});
        }}
        
        if (!matched.length) {{
            alert('未找到: ' + q);
            return;
        }}
        var target = matched[0];
        showNodeDetail(target);
        
        window._focusedTarget = target;
        applyFocusFilter(target);
    }};
    
    window.showAllNodes = function() {{
        document.getElementById('search-input').value = '';
        window._focusedTarget = null;
        applyFilters();
    }};
    
    window.addEventListener('resize', function() {{ chart.resize(); }});
    applyFilters();
    
    // 初始化 Mermaid
    if (typeof mermaid !== 'undefined') {{
        mermaid.initialize({{
            startOnLoad: false,
            theme: 'dark',
            securityLevel: 'loose',
            fontFamily: 'monospace',
            fontSize: 12
        }});
    }}
}}

if (typeof echarts === 'undefined') {{
    var s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js';
    s.onload = doInit;
    s.onerror = function() {{ document.getElementById('loading').innerHTML = '<p style="color:#f85149">ECharts 加载失败</p>'; }};
    document.head.appendChild(s);
}} else {{
    doInit();
}}
</script>
</body>
</html>'''
