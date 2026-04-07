"""业务能力图 HTML 生成器"""

import json
from typing import Dict


def generate_html(biz_graph_data: Dict, output_path: str):
    """生成业务能力图 HTML"""
    
    data_json = json.dumps({
        "nodes": biz_graph_data.get('nodes', []),
        "edges": biz_graph_data.get('edges', [])
    }, ensure_ascii=False, indent=2)
    
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Business Capability Graph</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

var _mermaidRendered = false;
function renderAllMermaid() {
    if (_mermaidRendered) return;
    _mermaidRendered = true;
    
    document.querySelectorAll('pre.mermaid').forEach(function(pre) {
        var graphText = pre.textContent;
        var div = document.createElement('div');
        div.className = 'mermaid-render';
        pre.parentNode.replaceChild(div, pre);
        
        mermaid.render('mermaid-' + Math.random().toString(36).substr(2, 9), graphText).then(function(result) {
            div.innerHTML = result.svg;
        }).catch(function(err) {
            div.innerHTML = '<pre style="color:red">' + err.message + '</pre><pre>' + graphText + '</pre>';
        });
    });
}
</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:#0d1117;color:#c9d1d9;height:100vh;display:flex;flex-direction:column;overflow:hidden}
#header{background:#161b22;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;gap:12px;border-bottom:1px solid #30363d}
#header .left{display:flex;align-items:center;gap:12px}
#header h1{font-size:15px;font-weight:500;color:#58a6ff;white-space:nowrap}
#header .stats{font-size:12px;color:#8b949e}
#header .stats span{color:#c9d1d9;font-weight:bold}
#search-box{display:flex;align-items:center;gap:4px}
#search-box input{padding:4px 8px;background:#0d1117;border:1px solid #30363d;border-radius:4px;font-size:12px;width:180px;outline:none;color:#c9d1d9}
#search-box input:focus{border-color:#58a6ff}
#search-box button{padding:4px 8px;background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:4px;cursor:pointer;font-size:11px}
#search-box button:hover{background:#58a6ff;border-color:#58a6ff}
#main{display:flex;flex:1;overflow:hidden}
#sidebar{width:200px;background:#161b22;border-right:1px solid #30363d;padding:12px;overflow-y:auto;flex-shrink:0}
#sidebar h3{font-size:12px;color:#58a6ff;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #30363d;text-transform:uppercase;letter-spacing:0.5px}
#sidebar .filter-group{margin-bottom:12px}
#sidebar .filter-group label{display:flex;align-items:center;gap:4px;font-size:11px;color:#8b949e;padding:2px 0;cursor:pointer}
#sidebar .filter-group input[type=checkbox]{accent-color:#58a6ff}
#sidebar .color-dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}
#chart{flex:1;background:#0d1117}
#detail{width:420px;background:#161b22;border-left:1px solid #30363d;padding:12px;overflow-y:auto;flex-shrink:0;display:none}
#detail.visible{display:block}
#detail h3{font-size:13px;color:#58a6ff;margin-bottom:8px;word-break:break-all;line-height:1.4}
#detail .detail-section{margin-bottom:10px}
#detail .detail-section h4{font-size:11px;color:#8b949e;margin-bottom:3px;font-weight:600;text-transform:uppercase}
#detail .detail-section p,#detail .detail-section div{font-size:12px;color:#c9d1d9;line-height:1.5}
#detail .tag{display:inline-block;background:#1a3a6e;color:#58a6ff;padding:1px 6px;border-radius:8px;font-size:10px;margin:1px 2px 1px 0}
#detail .tag.L3{background:#1a2a4a;color:#58a6ff}
#detail .tag.L4{background:#1a3a2a;color:#4ecca3}
#detail .tag.L5{background:#3d2e00;color:#d29922}
#detail .tag.L6{background:#2a1a3d;color:#a371f7}
#detail .close-btn{float:right;background:none;border:none;font-size:16px;cursor:pointer;color:#8b949e}
#detail .close-btn:hover{color:#f85149}
#detail .param-item{background:#0d1117;padding:4px 8px;margin:2px 0;border-radius:4px;font-size:11px}
#detail .param-item .param-name{color:#4ecca3;font-weight:bold}
#detail .param-item .param-type{color:#d29922}
#detail .flow-text{background:#0d1117;padding:6px 8px;border-radius:4px;font-size:11px;white-space:pre-wrap;max-height:150px;overflow-y:auto}
#detail .rule-item{background:#1a2a1a;padding:2px 6px;margin:2px 0;border-radius:4px;font-size:11px;border-left:2px solid #4ecca3}
#detail .mermaid-code{background:#0d1117;padding:6px 8px;border-radius:4px;font-family:monospace;font-size:10px;max-height:200px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
#detail .mermaid-chart{background:#0d1117;padding:8px;border-radius:4px;min-height:100px}
#detail .mermaid-render{background:#0d1117;padding:8px;border-radius:4px;min-height:150px}
#detail .mermaid-render svg{max-width:100%;height:auto}
#loading{position:fixed;top:0;left:0;right:0;bottom:0;background:#0d1117;display:flex;align-items:center;justify-content:center;z-index:9999;flex-direction:column}
#loading .spinner{width:36px;height:36px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin 0.8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#loading p{margin-top:12px;color:#8b949e;font-size:13px}
</style>
</head>
<body>
<div id="loading"><div class="spinner"></div><p>正在加载业务能力图...</p></div>
<div id="header">
  <div class="left">
    <h1>Business Capability Graph</h1>
    <div class="stats" id="stats"></div>
  </div>
  <div id="search-box">
    <input type="text" id="search-input" placeholder="搜索节点..." onkeydown="if(event.key==='Enter')searchNode()">
    <button onclick="searchNode()">聚焦</button>
    <button onclick="resetHighlight()">重置</button>
  </div>
</div>
<div id="main">
  <div id="sidebar">
    <div class="filter-group"><h3>层级</h3><div id="level-filters"></div></div>
    <div class="filter-group"><h3>边类型</h3><div id="edge-filters"></div></div>
    <div class="filter-group"><h3>Controller</h3><div id="controller-filters"></div></div>
  </div>
  <div id="chart"></div>
  <div id="detail"><button class="close-btn" onclick="closeDetail()">&times;</button><div id="detail-content"></div></div>
</div>
<script>
var GRAPH_DATA = ''' + data_json + ''';

var _initDone = false;
function doInit() {
    if (_initDone || typeof echarts === 'undefined') return;
    _initDone = true;
    document.getElementById('loading').style.display = 'none';

    var graphData = GRAPH_DATA;
    document.getElementById('stats').innerHTML = '节点: <span>' + graphData.nodes.length + '</span> &nbsp; 边: <span>' + graphData.edges.length + '</span>';

    var levelConfig = {
        '3': { label: 'L3 流程', color: '#58a6ff', symbolSize: 50 },
        '4': { label: 'L4 活动', color: '#4ecca3', symbolSize: 35 },
        '5': { label: 'L5 规则', color: '#d29922', symbolSize: 20 },
        '6': { label: 'L6 类', color: '#a371f7', symbolSize: 25 },
    };
    var edgeTypeConfig = {
        'contains': { label: '包含', color: '#484f58' },
        'references': { label: '引用', color: '#06b6d4' },
        'calls': { label: '调用', color: '#f0883e' },
    };

    var levelCounts = {};
    var edgeTypeCounts = {};
    graphData.nodes.forEach(function(n) {
        var level = '' + n.level;
        levelCounts[level] = (levelCounts[level] || 0) + 1;
    });
    graphData.edges.forEach(function(e) {
        edgeTypeCounts[e.type] = (edgeTypeCounts[e.type] || 0) + 1;
    });

    var levelVisibility = {};
    var edgeVisibility = {};
    Object.keys(levelConfig).forEach(function(k) { levelVisibility[k] = true; });
    Object.keys(edgeTypeConfig).forEach(function(k) { edgeVisibility[k] = true; });

    var levelFilterHtml = '';
    Object.keys(levelConfig).forEach(function(k) {
        var cfg = levelConfig[k];
        var count = levelCounts[k] || 0;
        if (count > 0) {
            levelFilterHtml += '<label><input type="checkbox" data-level="' + k + '" checked><span class="color-dot" style="background:' + cfg.color + '"></span>' + cfg.label + ' (' + count + ')</label>';
        }
    });
    document.getElementById('level-filters').innerHTML = levelFilterHtml;

    var edgeFilterHtml = '';
    Object.keys(edgeTypeConfig).forEach(function(k) {
        var cfg = edgeTypeConfig[k];
        var count = edgeTypeCounts[k] || 0;
        if (count > 0) {
            edgeFilterHtml += '<label><input type="checkbox" data-edge="' + k + '" checked><span class="color-dot" style="background:' + cfg.color + '"></span>' + cfg.label + ' (' + count + ')</label>';
        }
    });
    document.getElementById('edge-filters').innerHTML = edgeFilterHtml;

    var controllerCounts = {};
    graphData.nodes.forEach(function(n) {
        if (n.level == 3) {
            var name = n.name || '';
            var parts = name.split('.');
            var controller = parts[0] || 'Other';
            controllerCounts[controller] = (controllerCounts[controller] || 0) + 1;
        }
    });

    var controllerVisibility = {};
    var controllers = Object.keys(controllerCounts).sort();
    controllers.forEach(function(c) { controllerVisibility[c] = false; });
    controllers.forEach(function(c) { controllerVisibility[c] = true; });

    var controllerFilterHtml = '';
    controllers.forEach(function(c) {
        var count = controllerCounts[c];
        controllerFilterHtml += '<label><input type="checkbox" data-controller="' + c + '" checked>' + c + ' (' + count + ')</label>';
    });
    document.getElementById('controller-filters').innerHTML = controllerFilterHtml;

    var allNodes = [];
    var nodeSet = new Set();
    graphData.nodes.forEach(function(node) {
        var level = '' + node.level;
        var cfg = levelConfig[level] || levelConfig['4'];
        nodeSet.add(node.id);
        
        var nodeController = '';
        if (level == '3') {
            var parts = (node.name || '').split('.');
            nodeController = parts[0] || 'Other';
        }
        
        allNodes.push({
            id: node.id,
            name: node.name,
            category: level,
            symbolSize: cfg.symbolSize,
            itemStyle: { color: cfg.color, borderColor: '#0d1117', borderWidth: 1 },
            _level: level, _data: node, _controller: nodeController,
            draggable: true
        });
    });

    var allEdges = [];
    graphData.edges.forEach(function(edge) {
        if (nodeSet.has(edge.from) && nodeSet.has(edge.to)) {
            var cfg = edgeTypeConfig[edge.type] || edgeTypeConfig['references'];
            allEdges.push({
                source: edge.from,
                target: edge.to,
                name: edge.type,
                lineStyle: { color: cfg.color, width: 1, curveness: 0.1 }
            });
        }
    });

    var chartDom = document.getElementById('chart');
    var myChart = echarts.init(chartDom, 'dark');
    var option = {
        tooltip: {
            trigger: 'item',
            backgroundColor: '#161b22',
            borderColor: '#30363d',
            textStyle: { color: '#c9d1d9', fontSize: 11 },
            formatter: function(params) {
                if (params.dataType === 'node') {
                    return '<b>' + params.name + '</b><br/>' + 
                           '<span class="tag tag-L' + params.data._level + '">L' + params.data._level + '</span> ' +
                           (params.data._data.description || '').substring(0, 50);
                }
                return params.data.name;
            }
        },
        series: [{
            type: 'graph',
            layout: 'force',
            data: allNodes,
            links: allEdges,
            roam: true,
            draggable: true,
            label: { show: true, position: 'right', formatter: '{b}', fontSize: 9, color: '#8b949e' },
            edgeSymbol: ['circle', 'arrow'],
            edgeSymbolSize: [4, 6],
            force: { repulsion: 150, edgeLength: 60, gravity: 0.1 },
            lineStyle: { color: '#999', width: 1, curveness: 0.1 },
            emphasis: { focus: 'adjacency', lineStyle: { width: 3 } }
        }]
    };
    myChart.setOption(option);

    myChart.on('click', function(params) {
        if (params.dataType === 'node') {
            showDetail(params.data._data);
        }
    });

    window.addEventListener('resize', function() { myChart.resize(); });

    document.querySelectorAll('#level-filters input').forEach(function(cb) {
        cb.addEventListener('change', function() {
            levelVisibility[this.dataset.level] = this.checked;
            updateChart();
        });
    });
    document.querySelectorAll('#edge-filters input').forEach(function(cb) {
        cb.addEventListener('change', function() {
            edgeVisibility[this.dataset.edge] = this.checked;
            updateChart();
        });
    });
    document.querySelectorAll('#controller-filters input').forEach(function(cb) {
        cb.addEventListener('change', function() {
            controllerVisibility[this.dataset.controller] = this.checked;
            updateChart();
        });
    });

    function updateChart() {
        var visibleLevels = Object.keys(levelConfig).filter(function(k) { return levelVisibility[k]; });
        var visibleEdges = Object.keys(edgeTypeConfig).filter(function(k) { return edgeVisibility[k]; });
        var visibleControllers = controllers.filter(function(c) { return controllerVisibility[c]; });

        var filteredNodes = allNodes.filter(function(n) {
            if (visibleLevels.indexOf(n._level) < 0) return false;
            
            if (n._level == '3') {
                return visibleControllers.indexOf(n._controller) >= 0;
            }
            
            if (n._level == '4') {
                var nameParts = (n.name || '').split('.');
                var nodeController = nameParts[0];
                return visibleControllers.indexOf(nodeController) >= 0 || visibleControllers.length == controllers.length;
            }
            
            return true;
        });
        
        var filteredNodeSet = new Set(filteredNodes.map(function(n) { return n.id; }));
        var filteredEdges = allEdges.filter(function(e) { 
            return filteredNodeSet.has(e.source) && filteredNodeSet.has(e.target) && visibleEdges.indexOf(e.name) >= 0;
        });

        myChart.setOption({
            series: [{ data: filteredNodes, links: filteredEdges }]
        });
    }

    window.showDetail = function(node) {
        var detail = document.getElementById('detail');
        var content = document.getElementById('detail-content');
        detail.classList.add('visible');

        var html = '<h3>' + node.name + '</h3>';
        html += '<span class="tag tag-L' + node.level + '">L' + node.level + ' ' + (node.type || 'node') + '</span>';

        if (node.description) {
            html += '<div class="detail-section"><h4>描述</h4><p>' + node.description + '</p></div>';
        }
        if (node.level === 4 && node.flow) {
            html += '<div class="detail-section"><h4>流程</h4><p class="flow-text">' + node.flow + '</p></div>';
        }
        if (node.level === 4 && node.input && node.input.length > 0) {
            html += '<div class="detail-section"><h4>输入参数</h4>';
            node.input.forEach(function(inp) {
                html += '<div class="param-item"><span class="param-name">' + inp.param + '</span> <span class="param-type">' + inp.type + '</span> ' + (inp.meaning || '') + '</div>';
            });
            html += '</div>';
        }
        if (node.level === 4 && node.output && node.output.type) {
            html += '<div class="detail-section"><h4>输出</h4><div class="param-item"><span class="param-name">' + node.output.type + '</span> ' + (node.output.meaning || '') + '</div></div>';
        }
        if (node.level === 5 && node.content) {
            html += '<div class="detail-section"><h4>规则内容</h4><p>' + node.content + '</p></div>';
            if (node.rule_type) {
                html += '<div class="detail-section"><h4>规则类型</h4><p>' + node.rule_type + '</p></div>';
            }
        }
        if (node.level === 6 && node.class_type) {
            html += '<div class="detail-section"><h4>类类型</h4><p>' + node.class_type + '</p></div>';
        }
        if (node.level === 6 && node.package) {
            html += '<div class="detail-section"><h4>包路径</h4><p>' + node.package + '</p></div>';
        }
        if (node.flow_chart) {
            html += '<div class="detail-section"><h4>流程图</h4><pre class="mermaid">' + node.flow_chart + '</pre></div>';
        }
        if (node.contains && node.contains.length > 0) {
            html += '<div class="detail-section"><h4>包含</h4>';
            node.contains.forEach(function(c) {
                var child = graphData.nodes.find(function(n) { return n.id === c; });
                if (child) html += '<div class="rule-item"><a href="javascript:showDetail(' + JSON.stringify(child).replace(/"/g, '&quot;') + ');void(0)">' + child.name + '</a></div>';
            });
            html += '</div>';
        }
        if (node.references && node.references.length > 0) {
            html += '<div class="detail-section"><h4>引用</h4>';
            node.references.forEach(function(r) {
                var ref = graphData.nodes.find(function(n) { return n.id === r; });
                if (ref) html += '<div class="rule-item"><a href="javascript:showDetail(' + JSON.stringify(ref).replace(/"/g, '&quot;') + ');void(0)">' + ref.name + '</a></div>';
            });
            html += '</div>';
        }
        if (node.calls && node.calls.length > 0) {
            html += '<div class="detail-section"><h4>调用</h4>';
            node.calls.forEach(function(c) {
                var call = graphData.nodes.find(function(n) { return n.id === c; });
                if (call) html += '<div class="rule-item"><a href="javascript:showDetail(' + JSON.stringify(call).replace(/"/g, '&quot;') + ');void(0)">' + call.name + '</a></div>';
            });
            html += '</div>';
        }

        content.innerHTML = html;
        
        if (typeof mermaid !== 'undefined') {
            renderAllMermaid();
        }
    };

    window.closeDetail = function() {
        document.getElementById('detail').classList.remove('visible');
    };

    window.searchNode = function() {
        var keyword = document.getElementById('search-input').value.trim().toLowerCase();
        if (!keyword) return;
        var found = graphData.nodes.find(function(n) { return n.name.toLowerCase().indexOf(keyword) >= 0; });
        if (found) {
            showDetail(found);
            myChart.dispatchAction({ type: 'highlight', name: found.name });
        }
    };

    window.resetHighlight = function() {
        document.getElementById('search-input').value = '';
        myChart.dispatchAction({ type: 'downplay' });
        closeDetail();
    };
}

if (typeof echarts !== 'undefined') {
    doInit();
} else {
    window.addEventListener('load', function() {
        setTimeout(doInit, 500);
    });
}
</script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
