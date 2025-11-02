"""
测试报告生成模块
生成包含统计数据、饼图和失败截图的 HTML 报告

Author: Dongxiang.Zhang
Email: dongxiang699@163.com
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ReportGenerator:
    """测试报告生成器
    
    Author: Dongxiang.Zhang
    Email: dongxiang699@163.com
    """
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, test_results: List[Dict[str, Any]]):
        """
        生成测试报告
        
        Args:
            test_results: 测试结果列表
            
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        if not test_results:
            print("⚠️ 没有测试结果可生成报告")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成饼图
        pie_chart_path = self._generate_pie_chart(test_results, timestamp)

        # 保存本次运行的摘要（用于历史趋势对比）
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("success", False))
        failed = total - passed
        total_duration = sum(r.get("duration", 0) for r in test_results)
        self._save_summary(timestamp, total, passed, failed, total_duration)

        # 生成趋势图（从历史摘要中读取）和增长趋势图（总用例数随时间变化）
        bar_chart_path, time_chart_path = self._generate_trend_chart(timestamp)
        growth_chart_path = self._generate_growth_chart(timestamp)

        # 生成 HTML 报告（传入柱状图、时间曲线与增长曲线）
        html_path = self._generate_html_report(test_results, bar_chart_path, time_chart_path, growth_chart_path, pie_chart_path, timestamp)

        print(f"📊 测试报告已生成: {html_path}")

        return html_path
    
    def _generate_pie_chart(
        self, 
        test_results: List[Dict[str, Any]], 
        timestamp: str
    ) -> str:
        """
        生成饼图
        
        Args:
            test_results: 测试结果列表
            timestamp: 时间戳
            
        Returns:
            饼图文件路径（相对于 reports 目录）
            
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        # 统计数据
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("success", False))
        failed = total - passed
        
        # 如果没有测试结果，创建一个空的图表
        if total == 0:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, '暂无测试数据', 
                   horizontalalignment='center', 
                   verticalalignment='center',
                   fontsize=16)
            ax.axis('off')
        else:
            # 创建饼图（改小尺寸），使用更柔和、略暗的配色
            labels = ['通过', '失败']
            sizes = [passed, failed]
            colors = ['#2E7D32', '#C62828']  # 深绿色、暗红色
            explode = (0.05, 0.05) if failed > 0 else (0.05, 0)
            
            # 将饼图生成得更宽以适应页面拉伸显示
            fig, ax = plt.subplots(figsize=(10, 6))
            
            wedges, texts, autotexts = ax.pie(
                sizes, 
                explode=explode, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                shadow=True, 
                startangle=90,
                textprops={'fontsize': 11, 'weight': 'bold'}
            )
            
            # 设置标题（改小字体）
            ax.set_title(
                f'测试结果统计\n总计: {total} | 通过: {passed} | 失败: {failed}',
                fontsize=12,
                fontweight='bold',
                pad=15
            )
            
            # 美化文本
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
        
        # 保存图表
        chart_filename = f"test_chart_{timestamp}.png"
        chart_path = self.reports_dir / chart_filename
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_filename

    def _save_summary(self, timestamp: str, total: int, passed: int, failed: int, duration: float):
        """
        保存当前运行的摘要到 reports 目录，供历史趋势图使用
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        summary = {
            'timestamp': timestamp,
            'total': total,
            'passed': passed,
            'failed': failed,
            'duration': duration
        }
        summary_filename = f"test_summary_{timestamp}.json"
        summary_path = self.reports_dir / summary_filename
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception:
            # 写失败不影响主流程
            pass

    def _generate_trend_chart(self, timestamp: str) -> tuple:
        """
        从 reports 目录读取所有 summary json，生成一个包含柱状图（通过/失败/总计）和曲线图（耗时）的合并图片。

        返回生成的图片文件名（相对于 reports 目录）
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        summaries = []
        for p in sorted(self.reports_dir.glob('test_summary_*.json')):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    summaries.append(data)
            except Exception:
                continue

        if not summaries:
            return ''

        labels = []
        passed = []
        failed = []
        totals = []
        durations = []

        for s in summaries:
            ts = s.get('timestamp', '')
            parts = ts.split('_') if '_' in ts else [ts]
            short_label = parts[0][-6:]
            if len(parts) > 1:
                short_label += '\n' + parts[1][:4]
            labels.append(short_label)
            passed.append(s.get('passed', 0))
            failed.append(s.get('failed', 0))
            totals.append(s.get('total', 0))
            durations.append(s.get('duration', 0))

        # 绘制柱状图（用例数量对比）并保存为独立图片
        x = list(range(len(labels)))
        width = 0.25

        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.bar([i - width for i in x], passed, width, label='通过', color='#4CAF50')
        ax1.bar(x, failed, width, label='失败', color='#F44336')
        ax1.bar([i + width for i in x], totals, width, label='总计', color='#667eea')
        ax1.set_title('用例数量对比')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.legend()
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        bar_filename = f"test_trend_bar_{timestamp}.png"
        bar_path = self.reports_dir / bar_filename
        plt.savefig(bar_path, dpi=150, bbox_inches='tight')
        plt.close()

        # 绘制时间曲线（执行耗时趋势）并保存为独立图片
        fig2, ax2 = plt.subplots(figsize=(10, 3))
        ax2.plot(x, durations, marker='o', linestyle='-', color='#FF9800')
        ax2.set_title('执行耗时趋势 (秒)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        time_filename = f"test_trend_time_{timestamp}.png"
        time_path = self.reports_dir / time_filename
        plt.savefig(time_path, dpi=150, bbox_inches='tight')
        plt.close()

        return bar_filename, time_filename

    def _generate_growth_chart(self, timestamp: str) -> str:
        """
        生成一个简单的增长趋势折线图，显示每次执行的总用例数量随时间的变化。
        返回生成的图片文件名。
        
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        summaries = []
        for p in sorted(self.reports_dir.glob('test_summary_*.json')):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    summaries.append(data)
            except Exception:
                continue

        if not summaries:
            return ''

        labels = []
        totals = []
        for s in summaries:
            ts = s.get('timestamp', '')
            # 使用日期时间简短标识
            label = ts
            labels.append(label)
            totals.append(s.get('total', 0))

        # 绘制折线图
        fig, ax = plt.subplots(figsize=(6, 3))
        x = list(range(len(labels)))
        ax.plot(x, totals, marker='o', linestyle='-', color='#2E7D32')
        ax.set_title('用例总数增长趋势')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()

        growth_filename = f"test_growth_{timestamp}.png"
        growth_path = self.reports_dir / growth_filename
        plt.savefig(growth_path, dpi=150, bbox_inches='tight')
        plt.close()

        return growth_filename
    
    def _generate_html_report(
        self,
        test_results: List[Dict[str, Any]],
        bar_chart_path: str,
        time_chart_path: str,
        growth_chart_path: str,
        pie_chart_path: str,
        timestamp: str
    ) -> Path:
        """
        生成 HTML 报告
        
        Args:
            test_results: 测试结果列表
            pie_chart_path: 饼图文件路径
            timestamp: 时间戳
            
        Returns:
            HTML 报告文件路径
            
        Author: Dongxiang.Zhang
        Email: dongxiang699@163.com
        """
        # 统计数据
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("success", False))
        failed = total - passed
        total_duration = sum(r.get("duration", 0) for r in test_results)
        avg_duration = total_duration / total if total > 0 else 0
        
        # 生成 HTML
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI 自动化测试报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2f3b45 0%, #263238 100%); /* 更柔和、偏暗的页眉色 */
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
    .stat-card.total .value {{ color: #455A64; }}
    .stat-card.passed .value {{ color: #2E7D32; }}
    .stat-card.failed .value {{ color: #C62828; }}
    .stat-card.duration .value {{ color: #E65100; }}
        .stat-card .label {{
            font-size: 1.1em;
            color: #666;
        }}
        .content-wrapper {{
            padding: 20px 30px;
            background: white;
        }}
        /* 田字格布局：2 列 2 行，用于展示四个主要图表 */
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
            align-items: start;
            padding: 10px 0;
        }}
        .grid-item .chart-section {{
            height: 100%;
            min-height: 240px;
        }}
        /* 图表行：左侧主图（饼图+趋势），右侧为增长曲线 */
        .chart-row {{
            display: flex;
            gap: 18px;
            align-items: flex-start;
            justify-content: center;
            padding: 18px 0;
        }}
        .chart-main {{
            flex: 1 1 0;
            max-width: calc(100% - 300px);
        }}
        .chart-side {{
            flex: 0 0 280px; /* 放置小型增长曲线 */
            text-align: center;
            padding: 12px;
            background: #f3f4f6;
            border-radius: 10px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.04);
            height: fit-content;
        }}
        .chart-section {{
            width: 100%;
            margin: 0 auto;
            text-align: center;
            /* 使用 flex 布局以便图片可以填充剩余空间 */
            display: flex;
            flex-direction: column;
            padding: 0; /* 移除内边距以便图片平铺 */
            background: #f3f4f6; /* 更柔和的浅灰背景 */
            border-radius: 10px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.04);
            overflow: hidden;
        }}
        /* 图片延伸到容器左右对齐 */
        /* 图片平铺：占满格子剩余空间 */
        .chart-section img, .trend-under img, .chart-side img {{
            width: 100%;
            height: 100%;
            flex: 1 1 auto;
            object-fit: cover; /* 填充格子，可能裁剪以保持视觉一致 */
            display: block;
        }}
        /* 将饼图缩小为当前尺寸的 2/3，居中显示且不被裁剪 */
        .chart-section .pie-image {{
            width: 45%;
            height: 45%;
            margin: auto;
            object-fit: contain; /* 保持完整图像，不裁剪 */
            display: block;
        }}
        .trend-under {{
            margin-top: 18px;
            padding-top: 8px;
            border-top: 1px solid rgba(0,0,0,0.05);
        }}
        .trend-under h3 {{
            margin-top: 6px;
            margin-bottom: 8px;
            color: #333;
            font-size: 1.15em;
        }}
        .chart-section img {{
            max-width: 100%;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .chart-section h3 {{
            margin-bottom: 15px;
            color: #333;
            font-size: 1.3em;
        }}
        .test-cases {{
            padding: 16px 20px;
            max-height: 380px; /* 默认显示约5条，用滚动查看其余 */
            overflow-y: auto;
            margin: 18px 30px;
            scrollbar-width: thin; /* Firefox */
            scrollbar-color: rgba(0,0,0,0.16) transparent;
        }}

        .test-cases::-webkit-scrollbar {{
            width: 10px;
        }}
        .test-cases::-webkit-scrollbar-track {{
            background: transparent;
        }}
        .test-cases::-webkit-scrollbar-thumb {{
            background: rgba(0,0,0,0.12);
            border-radius: 10px;
        }}

        .test-cases h2 {{
            font-size: 1.6em;
            margin-bottom: 12px;
            color: #333;
            border-bottom: 3px solid #455A64;
            padding-bottom: 8px;
        }}
        /* 缩小每条测试用例的高度/内边距以便在列表中显示更多条目 */
        .test-case {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 10px 12px; /* 缩小内边距 */
            margin-bottom: 8px;  /* 缩短条目间距 */
            border-left: 5px solid #ddd;
            transition: all 0.18s;
            line-height: 1.25; /* 更紧凑的文本 */
            font-size: 0.95em;
        }}
        .test-case:hover {{
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .test-case.collapsed .test-case-content {{
            display: none;
        }}
        .test-case-toggle {{
            background: none;
            border: none;
            font-size: 1em; /* 略小的折叠图标 */
            cursor: pointer;
            color: #667eea;
            padding: 3px 6px; /* 更紧凑 */
            margin-right: 8px;
            transition: transform 0.18s;
            vertical-align: middle;
            line-height: 1;
        }}
        .test-case-toggle:hover {{
            color: #5568d3;
        }}
        .test-case-toggle.expanded {{
            transform: rotate(90deg);
        }}
        .test-case-header-clickable {{
            cursor: pointer;
            display: flex;
            align-items: center;
            user-select: none;
        }}
        .test-case.passed {{
            border-left-color: #4CAF50;
        }}
        .test-case.failed {{
            border-left-color: #F44336;
        }}
        .test-case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px; /* 缩短标题下间距 */
        }}
        .test-case-header h3 {{
            font-size: 1.05em; /* 更小的标题，使单条高度更低 */
            color: #333;
            margin: 0;
        }}
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .test-status.passed {{
            background: #4CAF50;
            color: white;
        }}
        .test-status.failed {{
            background: #F44336;
            color: white;
        }}
        .test-description {{
            color: #666;
            margin-bottom: 10px;
            font-size: 0.95em;
        }}
        .test-steps {{
            margin-top: 15px;
        }}
        .test-step {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            background: white;
            display: flex;
            align-items: center;
        }}
        .test-step.success {{
            border-left: 3px solid #4CAF50;
        }}
        .test-step.failure {{
            border-left: 3px solid #F44336;
        }}
        .test-step .step-icon {{
            margin-right: 10px;
            font-size: 1.2em;
        }}
        .screenshot {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }}
        .screenshot img {{
            max-width: 100%;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.3s;
        }}
        .screenshot img:hover {{
            transform: scale(1.02);
        }}
        .error-message {{
            background: #ffebee;
            border-left: 4px solid #F44336;
            padding: 15px;
            margin-top: 10px;
            border-radius: 5px;
            color: #c62828;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            border-top: 1px solid #ddd;
        }}
        /* 历史趋势模块 */
        .trend-module {{
            background: #ffffff;
            border-radius: 10px;
            padding: 18px;
            margin: 20px 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        }}
        .trend-module h2 {{
            font-size: 1.15em;
            margin-bottom: 12px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .trend-charts {{
            display: flex;
            gap: 18px;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .trend-charts img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}
        .expand-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .expand-btn:hover {{
            background: #5568d3;
        }}
        .steps-container {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .steps-container.expanded {{
            max-height: 2000px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 UI 自动化测试报告</h1>
            <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="stats">
            <div class="stat-card total">
                <div class="value">{total}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="stat-card passed">
                <div class="value">{passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="stat-card failed">
                <div class="value">{failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="stat-card duration">
                <div class="value">{total_duration:.1f}s</div>
                <div class="label">总耗时</div>
            </div>
        </div>
        
        <div class="content-wrapper">
            <div class="grid-container">
                <!-- 左上：用例数量对比（柱状图） -->
                <div class="grid-item">
                    <div class="chart-section">
                        <h3>用例数量对比（通过/失败/总计）</h3>
                        <img src="{bar_chart_path}" alt="用例数量对比">
                    </div>
                </div>

                <!-- 右上：测试结果分布（饼图） -->
                <div class="grid-item">
                    <div class="chart-section">
                            <h3>测试结果分布</h3>
                            <img class="pie-image" src="{pie_chart_path}" alt="测试结果分布">
                        </div>
                </div>

                <!-- 左下：执行耗时趋势（曲线图） -->
                <div class="grid-item">
                    <div class="chart-section">
                        <h3>执行耗时趋势（秒）</h3>
                        <img src="{time_chart_path}" alt="执行耗时趋势">
                    </div>
                </div>

                <!-- 右下：用例总数增长趋势 -->
                <div class="grid-item">
                    <div class="chart-section">
                        <h3>用例总数增长趋势</h3>
                        <img src="{growth_chart_path}" alt="用例增长曲线">
                    </div>
                </div>
            </div>
        </div>
"""

        # 为了将测试用例列表放到页面底部，先在单独变量中构建 HTML
        test_cases_html = f"""
        <div class=\"test-cases\">\n
            <h2>测试用例列表</h2>
"""

        # 添加测试用例详情到 test_cases_html
        for idx, result in enumerate(test_results):
            status_class = "passed" if result.get("success") else "failed"
            status_text = "✅ 通过" if result.get("success") else "❌ 失败"
            status_bg = "passed" if result.get("success") else "failed"
            case_id = f"test-case-{idx}"

            # 将所有测试用例默认全部展开，确保页面底部显示完整列表
            collapsed_class = ""
            toggle_text = '▼'
            toggle_expanded_cls = 'expanded'

            test_cases_html += f"""
            <div class="test-case {status_class} {collapsed_class}" id="{case_id}">
                <div class="test-case-header-clickable" onclick="toggleTestCase('{case_id}')">
                    <button class="test-case-toggle {toggle_expanded_cls}" id="toggle-{case_id}">{toggle_text}</button>
                    <div class="test-case-header" style="flex: 1;">
                        <h3 style="display: inline;">{result.get('name', '未命名测试')} <span style="color: #999; font-size: 0.8em;">({result.get('id', 'N/A')})</span></h3>
                        <span class="test-status {status_bg}" style="float: right;">{status_text}</span>
                    </div>
                </div>
                <div class="test-case-content">
                    <div class="test-description">
                        📝 {result.get('description', '无描述')}
                    </div>
                    <div style="margin-top: 10px; color: #666;">
                        ⏱️ 耗时: {result.get('duration', 0):.2f} 秒
                    </div>
"""
            
            # 错误信息
            if result.get("error"):
                test_cases_html += f"""
                    <div class="error-message">
                        <strong>错误信息:</strong><br>
                        {result.get('error')}
                    </div>
"""
            
            # 测试步骤
            steps = result.get("steps", [])
            if steps:
                test_cases_html += """
                    <button class="expand-btn" onclick="toggleSteps(this); event.stopPropagation();">展开/收起详细步骤</button>
                    <div class="steps-container">
                        <div class="test-steps">
"""
                for step in steps:
                    step_class = "success" if step.get("success") else "failure"
                    step_icon = "✅" if step.get("success") else "❌"
                    test_cases_html += f"""
                            <div class="test-step {step_class}">
                                <span class="step-icon">{step_icon}</span>
                                <div>
                                    <strong>步骤 {step.get('step', 'N/A')}:</strong> {step.get('description', 'N/A')}<br>
                                    <small style="color: #666;">{step.get('message', '')}</small>
"""
                    if step.get("error"):
                        test_cases_html += f"""
                                    <div style="color: #F44336; margin-top: 5px;">
                                        ⚠️ {step.get('error')}
                                    </div>
"""
                        test_cases_html += """
                                </div>
                            </div>
"""
                test_cases_html += """
                        </div>
                    </div>
"""
            
            # 失败截图
            screenshot = result.get("screenshot")
            # 失败截图
            screenshot = result.get("screenshot")
            if screenshot and not result.get("success"):
                screenshot_full_path = f"screenshots/{Path(screenshot).name}" if not screenshot.startswith("screenshots/") else screenshot
                test_cases_html += f"""
                    <div class=\"screenshot\">
                        <h4 style=\"margin-bottom: 10px; color: #C62828;\">失败截图:</h4>
                        <img src=\"{screenshot_full_path}\" alt=\"失败截图\" onclick=\"window.open(this.src, '_blank')\">
                    </div>
"""
            
            test_cases_html += """
                </div>
            </div>
"""

        # 追加测试用例列表到底部
        test_cases_html += """
        </div>
"""

        html_content += test_cases_html

        html_content += """
        <div class=\"footer\">
            <p>由 Playwright MCP + DeepSeek 自动生成</p>
        </div>
    </div>
    
    <script>
        function toggleSteps(btn) {
            const container = btn.nextElementSibling;
            container.classList.toggle('expanded');
        }
        
        function toggleTestCase(caseId) {
            const testCase = document.getElementById(caseId);
            const toggle = document.getElementById('toggle-' + caseId);
            
            if (testCase.classList.contains('collapsed')) {
                testCase.classList.remove('collapsed');
                toggle.classList.add('expanded');
                toggle.textContent = '▼';
            } else {
                testCase.classList.add('collapsed');
                toggle.classList.remove('expanded');
                toggle.textContent = '▶';
            }
        }
    </script>
</body>
</html>
"""
        
        # 保存 HTML 文件
        html_filename = f"test_report_{timestamp}.html"
        html_path = self.reports_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path