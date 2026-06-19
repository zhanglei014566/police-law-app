#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成独立的HTML文件，包含所有法条数据，打开即用，无需服务器。
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laws.db')

def load_laws():
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id, law_name, article_number, article_content, category FROM laws ORDER BY id')
    rows = cur.fetchall()
    conn.close()
    laws = []
    for r in rows:
        laws.append({
            'id': r['id'],
            'law_name': r['law_name'],
            'article_number': r['article_number'],
            'article_content': r['article_content'],
            'category': r['category'] or '',
        })
    return laws

def generate_html(laws):
    laws_json = json.dumps(laws, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>执法辅助工具</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f6fa; color: #222; }}
.header {{ background: #1a73e8; color: #fff; padding: 12px 16px; font-size: 18px; font-weight: 600; text-align: center; position: sticky; top: 0; z-index: 100; }}
.search-box {{ padding: 12px; background: #fff; border-bottom: 1px solid #e0e0e0; }}
.search-box input {{ width: 100%; padding: 10px 14px; font-size: 16px; border: 1px solid #ccc; border-radius: 8px; outline: none; }}
.search-box input:focus {{ border-color: #1a73e8; }}
.stats {{ padding: 8px 16px; font-size: 13px; color: #666; background: #f5f6fa; }}
.result-item {{ background: #fff; margin: 8px; padding: 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.result-item .meta {{ font-size: 13px; color: #1a73e8; font-weight: 600; margin-bottom: 6px; }}
.result-item .content {{ font-size: 14px; line-height: 1.6; color: #333; white-space: pre-wrap; }}
.highlight {{ background: #fff3cd; color: #856404; border-radius: 2px; padding: 0 2px; }}
.empty {{ text-align: center; padding: 40px; color: #999; font-size: 15px; }}
.filters {{ padding: 8px 12px; background: #fff; border-bottom: 1px solid #e0e0e0; display: flex; gap: 8px; flex-wrap: wrap; }}
.filters button {{ padding: 6px 14px; border: 1px solid #1a73e8; background: #fff; color: #1a73e8; border-radius: 20px; font-size: 13px; cursor: pointer; }}
.filters button.active {{ background: #1a73e8; color: #fff; }}
</style>
</head>
<body>

<div class="header">⚖️ 执法辅助工具</div>

<div class="search-box">
  <input type="text" id="searchInput" placeholder="输入关键词搜索（如：盗窃、拘传、取保候审）" oninput="doSearch()" />
</div>

<div class="filters" id="filters">
  <button onclick="filterLaw('')" class="active">全部</button>
</div>

<div class="stats" id="stats"></div>
<div id="results"></div>

<script>
var LAWS = {laws_json};

// 构建法律名称筛选按钮
var lawNames = [...new Set(LAWS.map(l => l.law_name))];
var filtersHtml = '<button onclick="filterLaw(\\')" class="active">全部</button>';
lawNames.forEach(function(name) {{
  var safe = name.replace(/'/g, "\\\\'");
  filtersHtml += '<button onclick="filterLaw(\\'' + safe + '\\')">' + name + '</button>';
}});
document.getElementById('filters').innerHTML = filtersHtml;

var currentFilter = '';

function filterLaw(name) {{
  currentFilter = name;
  document.querySelectorAll('.filters button').forEach(function(btn) {{
    btn.classList.toggle('active', btn.textContent === (name || '全部'));
  }});
  doSearch();
}}

function doSearch() {{
  var q = document.getElementById('searchInput').value.trim();
  var results = [];
  
  for (var i = 0; i < LAWS.length; i++) {{
    var law = LAWS[i];
    if (currentFilter && law.law_name !== currentFilter) continue;
    
    var text = law.law_name + ' ' + law.article_number + ' ' + law.article_content;
    var match = true;
    if (q) {{
      var keywords = q.split(/\\s+/);
      for (var k = 0; k < keywords.length; k++) {{
        if (text.indexOf(keywords[k]) === -1) {{ match = false; break; }}
      }}
    }}
    if (match) results.push(law);
  }}
  
  // 按相关性排序：匹配关键词越多越靠前
  if (q) {{
    var keywords = q.split(/\\s+/);
    results.sort(function(a, b) {{
      var scoreA = 0, scoreB = 0;
      var textA = a.law_name + ' ' + a.article_number + ' ' + a.article_content;
      var textB = b.law_name + ' ' + b.article_number + ' ' + b.article_content;
      keywords.forEach(function(kw) {{
        if (textA.indexOf(kw) !== -1) scoreA++;
        if (textB.indexOf(kw) !== -1) scoreB++;
      }});
      // 治安管理处罚法优先
      if (a.law_name.indexOf('治安管理处罚') !== -1) scoreA += 0.5;
      if (b.law_name.indexOf('治安管理处罚') !== -1) scoreB += 0.5;
      return scoreB - scoreA;
    }});
  }}
  
  showResults(results, q);
}}

function highlightText(text, q) {{
  if (!q) return text;
  var keywords = q.split(/\\s+/);
  keywords.forEach(function(kw) {{
    if (!kw) return;
    var regex = new RegExp('(' + kw.replace(/[.*+?^${{}}()|[]\\]\\\\]/g, '\\\\$&') + ')', 'gi');
    text = text.replace(regex, '<span class="highlight">$1</span>');
  }});
  return text;
}}

function showResults(results, q) {{
  var stats = document.getElementById('stats');
  var container = document.getElementById('results');
  
  stats.textContent = '共 ' + results.length + ' 条结果';
  
  if (results.length === 0) {{
    container.innerHTML = '<div class="empty">没有找到匹配的法条<br/>请尝试其他关键词</div>';
    return;
  }}
  
  var html = '';
  results.forEach(function(law) {{
    var displayContent = law.article_content;
    // 截断过长的内容
    if (displayContent.length > 300) {{
      displayContent = displayContent.substring(0, 300) + '...';
    }}
    html += '<div class="result-item">' +
      '<div class="meta">' + highlightText(law.law_name, q) + ' ' + highlightText(law.article_number, q) + '</div>' +
      '<div class="content">' + highlightText(displayContent, q) + '</div>' +
      '</div>';
  }});
  container.innerHTML = html;
}}

// 初始加载显示全部
doSearch();
</script>
</body>
</html>'''
    return html

if __name__ == '__main__':
    print('正在加载法条数据...')
    laws = load_laws()
    print(f'已加载 {len(laws)} 条法条')
    
    html = generate_html(laws)
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'laws_search.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'已生成: {output_path}')
    print(f'文件大小: {len(html)/1024:.1f} KB')
    print('用浏览器打开此文件即可使用！')
