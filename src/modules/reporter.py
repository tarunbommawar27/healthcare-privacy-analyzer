"""Report generation module with multiple output formats"""

import json
from typing import Dict, List
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
from src.utils.logger import get_logger
from src.utils.file_handler import FileHandler

logger = get_logger()


class ReportGenerator:
    """Generate comprehensive reports in multiple formats"""

    def __init__(self, config: Dict):
        """
        Initialize report generator

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_config = config.get('output', {})
        self.paths = config.get('paths', {})
        self.file_handler = FileHandler()

        # Ensure output directories exist
        self.file_handler.ensure_dir(self.paths.get('reports', 'outputs/reports'))
        self.file_handler.ensure_dir(self.paths.get('visualizations', 'outputs/visualizations'))

    def generate_summary(self, app_name: str, analysis: Dict, scoring: Dict) -> str:
        """
        Generate text summary of analysis

        Args:
            app_name: Application name
            analysis: Analysis results
            scoring: Risk scoring results

        Returns:
            Summary text
        """
        summary_parts = [
            f"PRIVACY POLICY ANALYSIS REPORT",
            f"=" * 50,
            f"App/Service: {app_name}",
            f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"RISK ASSESSMENT",
            f"-" * 50,
            f"Overall Risk Score: {scoring['overall_score']:.2f}/1.00",
            f"Risk Level: {scoring['risk_level']}",
            f"Red Flags Detected: {scoring['red_flags_count']}",
            f"",
            f"EXECUTIVE SUMMARY",
            f"-" * 50,
            f"{analysis.get('summary', 'No summary available')}",
            f"",
            f"CATEGORY SCORES",
            f"-" * 50,
        ]

        for category, score in scoring.get('category_scores', {}).items():
            summary_parts.append(f"{category}: {score:.2f}")

        if scoring.get('red_flags'):
            summary_parts.extend([
                f"",
                f"RED FLAGS IDENTIFIED",
                f"-" * 50,
            ])
            for flag in scoring['red_flags']:
                summary_parts.append(f"- {flag}")

        summary_parts.extend([
            f"",
            f"RECOMMENDATIONS",
            f"-" * 50,
        ])
        for rec in analysis.get('recommendations', []):
            summary_parts.append(f"- {rec}")

        return "\n".join(summary_parts)

    def create_visualizations(self, app_name: str, scoring: Dict) -> List[str]:
        """
        Create visualization charts

        Args:
            app_name: Application name
            scoring: Risk scoring results

        Returns:
            List of created file paths
        """
        logger.info("Creating visualizations")
        viz_dir = self.paths.get('visualizations', 'outputs/visualizations')
        created_files = []

        # Set style
        sns.set_style("whitegrid")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Category Scores Bar Chart
        fig, ax = plt.subplots(figsize=(10, 8))

        # Extract and validate category scores
        category_scores_raw = scoring.get('category_scores', {})

        # Debug logging
        logger.debug(f"Raw category_scores: {category_scores_raw}")

        # Create readable category names and ensure we have valid scores
        category_mapping = {
            'data_collection': 'Data Collection',
            'data_usage': 'Data Usage',
            'third_party_sharing': 'Third-Party Sharing',
            'data_retention': 'Data Retention',
            'user_rights': 'User Rights',
            'security_measures': 'Security Measures',
            'compliance': 'HIPAA Compliance',
            'older_adult_considerations': 'Older Adult Considerations'
        }

        # Build clean category data
        categories = []
        scores = []

        for key, display_name in category_mapping.items():
            if key in category_scores_raw:
                score = category_scores_raw[key]
                # Ensure score is numeric and not None
                if score is not None and isinstance(score, (int, float)):
                    categories.append(display_name)
                    scores.append(float(score))
                    logger.debug(f"  {display_name}: {score}")
                else:
                    logger.warning(f"Invalid score for {key}: {score}")
                    categories.append(display_name)
                    scores.append(0.5)  # Default middle score
            else:
                logger.warning(f"Missing category: {key}")
                categories.append(display_name)
                scores.append(0.5)  # Default middle score

        # If no scores at all, use defaults
        if not scores:
            logger.warning("No category scores found, using defaults")
            categories = list(category_mapping.values())
            scores = [0.5] * len(categories)

        # Color based on risk (0-1 scale, where higher = more risk)
        colors = ['#F44336' if s > 0.7 else '#FF9800' if s > 0.5 else '#FFC107' if s > 0.3 else '#4CAF50' for s in scores]

        ax.barh(categories, scores, color=colors)
        ax.set_xlabel('Risk Score (0=Low Risk, 1=High Risk)', fontsize=12)
        ax.set_title(f'Privacy Risk by Category - {app_name}', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1)

        # Add score labels
        for i, v in enumerate(scores):
            ax.text(v + 0.02, i, f'{v:.2f}', va='center', fontsize=10)

        plt.tight_layout()
        bar_chart_path = f"{viz_dir}/{app_name}_category_scores_{timestamp}.png"
        plt.savefig(bar_chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(bar_chart_path)
        logger.info(f"Created bar chart: {bar_chart_path}")

        # 2. Risk Score Gauge
        fig, ax = plt.subplots(figsize=(8, 6))
        overall_score = scoring['overall_score']

        # Create gauge
        colors_gauge = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
        bounds = [0, 0.3, 0.6, 0.8, 1.0]

        for i in range(len(colors_gauge)):
            ax.barh(0, bounds[i+1] - bounds[i], left=bounds[i], height=0.3,
                   color=colors_gauge[i], alpha=0.7)

        # Add score indicator
        ax.barh(0, 0.02, left=overall_score - 0.01, height=0.4,
               color='black', label=f'Score: {overall_score:.2f}')

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel('Risk Score', fontsize=12)
        ax.set_title(f'Overall Privacy Risk Score - {app_name}', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.set_yticks([])

        plt.tight_layout()
        gauge_path = f"{viz_dir}/{app_name}_risk_gauge_{timestamp}.png"
        plt.savefig(gauge_path, dpi=300, bbox_inches='tight')
        plt.close()
        created_files.append(gauge_path)
        logger.info(f"Created gauge chart: {gauge_path}")

        return created_files

    def generate_html_report(self, app_name: str, url: str, analysis: Dict,
                           scoring: Dict, visualizations: List[str]) -> str:
        """
        Generate HTML report

        Args:
            app_name: Application name
            url: Privacy policy URL
            analysis: Analysis results
            scoring: Risk scoring results
            visualizations: List of visualization file paths

        Returns:
            Path to generated HTML file
        """
        logger.info("Generating HTML report")

        risk_color = scoring.get('risk_color', '#9E9E9E')

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy Analysis - {app_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 1.2em;
            background-color: {risk_color};
            color: white;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .category {{
            margin-bottom: 20px;
            padding: 15px;
            border-left: 4px solid #667eea;
            background-color: #f9f9f9;
        }}
        .concern {{
            color: #d32f2f;
            margin: 5px 0;
        }}
        .positive {{
            color: #388e3c;
            margin: 5px 0;
        }}
        .red-flag {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            padding: 10px;
            margin: 5px 0;
        }}
        .visualization {{
            text-align: center;
            margin: 20px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Privacy Policy Analysis Report</h1>
        <h2>{app_name}</h2>
        <p><strong>Policy URL:</strong> <a href="{url}" style="color: white;">{url}</a></p>
        <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Risk Assessment</h2>
        <p><strong>Overall Risk Score:</strong> {scoring['overall_score']:.2f}/1.00</p>
        <p><strong>Risk Level:</strong> <span class="risk-badge">{scoring['risk_level']}</span></p>
        <p><strong>Red Flags Detected:</strong> {scoring['red_flags_count']}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{analysis.get('summary', 'No summary available')}</p>
    </div>
"""

        # Add visualizations
        if visualizations:
            html_content += '    <div class="section">\n        <h2>Visualizations</h2>\n'
            for viz_path in visualizations:
                # Convert to relative path for HTML
                viz_filename = Path(viz_path).name
                html_content += f'        <div class="visualization">\n'
                html_content += f'            <img src="../visualizations/{viz_filename}" alt="Visualization">\n'
                html_content += f'        </div>\n'
            html_content += '    </div>\n'

        # Category Analysis
        html_content += '    <div class="section">\n        <h2>Detailed Category Analysis</h2>\n'

        categories = analysis.get('categories', {})
        for category, findings in categories.items():
            score = scoring['category_scores'].get(category, 0)
            html_content += f'        <div class="category">\n'
            html_content += f'            <h3>{category} (Score: {score:.2f})</h3>\n'
            html_content += f'            <p><strong>Findings:</strong> {findings.get("findings", "N/A")}</p>\n'

            concerns = findings.get('concerns', [])
            if concerns:
                html_content += '            <p><strong>Concerns:</strong></p>\n            <ul>\n'
                for concern in concerns:
                    html_content += f'                <li class="concern">⚠️ {concern}</li>\n'
                html_content += '            </ul>\n'

            positives = findings.get('positive_aspects', [])
            if positives:
                html_content += '            <p><strong>Positive Aspects:</strong></p>\n            <ul>\n'
                for positive in positives:
                    html_content += f'                <li class="positive">✓ {positive}</li>\n'
                html_content += '            </ul>\n'

            html_content += '        </div>\n'

        html_content += '    </div>\n'

        # Red Flags
        if scoring.get('red_flags'):
            html_content += '    <div class="section">\n        <h2>Red Flags Identified</h2>\n'
            for flag in scoring['red_flags']:
                html_content += f'        <div class="red-flag">🚩 {flag}</div>\n'
            html_content += '    </div>\n'

        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            html_content += '    <div class="section">\n        <h2>Recommendations</h2>\n        <ul>\n'
            for rec in recommendations:
                html_content += f'            <li>{rec}</li>\n'
            html_content += '        </ul>\n    </div>\n'

        html_content += """
    <div class="footer">
        <p>Generated by Privacy Policy Analyzer for Healthcare Apps</p>
        <p>This analysis is for informational purposes only and should not be considered legal advice.</p>
    </div>
</body>
</html>
"""

        # Save HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.paths.get('reports', 'outputs/reports')
        html_path = f"{report_dir}/{app_name}_report_{timestamp}.html"
        self.file_handler.save_text(html_content, html_path)
        logger.info(f"Generated HTML report: {html_path}")

        return html_path

    def generate_json_report(self, app_name: str, url: str, analysis: Dict,
                           scoring: Dict) -> str:
        """
        Generate JSON report

        Args:
            app_name: Application name
            url: Privacy policy URL
            analysis: Analysis results
            scoring: Risk scoring results

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON report")

        report_data = {
            'app_name': app_name,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'scoring': scoring
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.paths.get('reports', 'outputs/reports')
        json_path = f"{report_dir}/{app_name}_report_{timestamp}.json"

        self.file_handler.save_json(report_data, json_path)
        logger.info(f"Generated JSON report: {json_path}")

        return json_path

    def generate_comparison_report(self, results: List[Dict]) -> str:
        """
        Generate comparison report across multiple apps

        Args:
            results: List of analysis results for different apps

        Returns:
            Path to comparison report
        """
        logger.info(f"Generating comparison report for {len(results)} apps")

        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy Comparison Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th {
            background-color: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .risk-low { background-color: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px; }
        .risk-medium { background-color: #FFC107; color: black; padding: 5px 10px; border-radius: 3px; }
        .risk-high { background-color: #FF9800; color: white; padding: 5px 10px; border-radius: 3px; }
        .risk-critical { background-color: #F44336; color: white; padding: 5px 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Privacy Policy Comparison Report</h1>
        <p><strong>Generated:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p><strong>Apps Compared:</strong> """ + str(len(results)) + """</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>App Name</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Red Flags</th>
                <th>Healthcare Compliance</th>
            </tr>
        </thead>
        <tbody>
"""

        for result in results:
            app_name = result.get('app_name', 'Unknown')
            scoring = result.get('scoring', {})
            analysis = result.get('analysis', {})

            score = scoring.get('overall_score', 0)
            level = scoring.get('risk_level', 'UNKNOWN')
            red_flags = scoring.get('red_flags_count', 0)

            # Get healthcare compliance info
            categories = analysis.get('categories', {})
            healthcare = categories.get('Healthcare Compliance', {})
            healthcare_summary = healthcare.get('findings', 'N/A')[:100] + '...'

            risk_class = f"risk-{level.lower()}"

            html_content += f"""
            <tr>
                <td><strong>{app_name}</strong></td>
                <td>{score:.2f}</td>
                <td><span class="{risk_class}">{level}</span></td>
                <td>{red_flags}</td>
                <td>{healthcare_summary}</td>
            </tr>
"""

        html_content += """
        </tbody>
    </table>
</body>
</html>
"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.paths.get('reports', 'outputs/reports')
        comparison_path = f"{report_dir}/comparison_report_{timestamp}.html"

        self.file_handler.save_text(html_content, comparison_path)
        logger.info(f"Generated comparison report: {comparison_path}")

        return comparison_path
