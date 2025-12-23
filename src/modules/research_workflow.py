"""
Research Workflow Orchestrator
End-to-end automation for privacy policy research studies
"""

import csv
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import concurrent.futures
from tqdm import tqdm

from src.modules.scraper import PolicyScraper
from src.modules.analyzer import PolicyAnalyzer
from src.modules.scorer import RiskScorer
from src.modules.reporter import ReportGenerator
from src.modules.comparative_analyzer import ComparativeAnalyzer, load_analyses_from_directory
from src.utils.logger import get_logger
from src.utils.file_handler import FileHandler
from src.utils.validator import AnalysisValidator

logger = get_logger()


class ResearchWorkflow:
    """
    End-to-end research workflow orchestrator
    Automates the complete analysis pipeline from CSV to publication-ready outputs
    """

    def __init__(self,
                 input_csv: Optional[str] = None,
                 output_dir: str = 'research_output/',
                 config_path: str = 'config/config.yaml',
                 model: str = 'auto',
                 depth: str = 'standard',
                 max_concurrent: int = 3,
                 checkpoint_interval: int = 5):
        """
        Initialize research workflow

        Args:
            input_csv: Path to CSV with apps to analyze (optional)
            output_dir: Base output directory
            config_path: Path to configuration file
            model: Model to use ('claude', 'gpt4', 'auto')
            depth: Analysis depth ('quick', 'standard', 'deep')
            max_concurrent: Maximum concurrent analyses
            checkpoint_interval: Save checkpoint every N apps
        """
        self.input_csv = input_csv
        self.output_dir = Path(output_dir)
        self.config_path = config_path
        self.model = model
        self.depth = depth
        self.max_concurrent = max_concurrent
        self.checkpoint_interval = checkpoint_interval

        # Create output directories
        self.reports_dir = self.output_dir / 'reports'
        self.viz_dir = self.output_dir / 'visualizations'
        self.stats_dir = self.output_dir / 'statistics'
        self.dashboard_dir = self.output_dir / 'dashboard'
        self.checkpoints_dir = self.output_dir / 'checkpoints'

        for dir_path in [self.reports_dir, self.viz_dir, self.stats_dir,
                        self.dashboard_dir, self.checkpoints_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.file_handler = FileHandler()
        self.config = self.file_handler.load_yaml(config_path)

        # Initialize components
        self.scraper = PolicyScraper(self.config.get('scraping', {}))
        self.analyzer = PolicyAnalyzer(
            self.config,
            model_override=model,
            analysis_depth=depth,
            use_cache=True
        )
        self.scorer = RiskScorer(self.config)
        self.reporter = ReportGenerator(self.config)
        self.validator = AnalysisValidator(strict_mode=False)

        # Workflow state
        self.apps_to_analyze = []
        self.completed_apps = []
        self.failed_apps = []
        self.analyses = []

        logger.info(f"Research workflow initialized: {output_dir}")

    def load_apps_from_csv(self, csv_path: Optional[str] = None) -> List[Dict]:
        """
        Load apps from CSV file

        CSV Format:
            app_name,url,category,notes
            Zocdoc,https://...,telehealth,appointment booking

        Args:
            csv_path: Path to CSV file (uses self.input_csv if not specified)

        Returns:
            List of app dictionaries
        """
        csv_path = csv_path or self.input_csv
        if not csv_path:
            raise ValueError("No CSV file specified")

        logger.info(f"Loading apps from {csv_path}")

        apps = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            apps = list(reader)

        # Validate required fields
        for app in apps:
            if 'app_name' not in app or 'url' not in app:
                raise ValueError(f"CSV must have 'app_name' and 'url' columns")

        self.apps_to_analyze = apps
        logger.info(f"Loaded {len(apps)} apps from CSV")

        return apps

    def save_checkpoint(self):
        """Save workflow checkpoint"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'completed': [app['app_name'] for app in self.completed_apps],
            'failed': [app['app_name'] for app in self.failed_apps],
            'total': len(self.apps_to_analyze),
            'progress': len(self.completed_apps) / len(self.apps_to_analyze) * 100 if self.apps_to_analyze else 0
        }

        checkpoint_path = self.checkpoints_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.file_handler.save_json(checkpoint, str(checkpoint_path))
        logger.info(f"Checkpoint saved: {checkpoint_path}")

    def load_checkpoint(self, checkpoint_path: str) -> Dict:
        """Load workflow checkpoint"""
        checkpoint = self.file_handler.load_json(checkpoint_path)
        logger.info(f"Loaded checkpoint: {len(checkpoint['completed'])} completed, {len(checkpoint['failed'])} failed")
        return checkpoint

    def analyze_single_app(self, app: Dict, use_selenium: bool = False) -> Optional[Dict]:
        """
        Analyze a single app

        Args:
            app: App dictionary with 'app_name' and 'url'
            use_selenium: Whether to use Selenium for scraping

        Returns:
            Analysis result or None if failed
        """
        app_name = app['app_name']
        url = app['url']

        logger.info(f"Analyzing: {app_name}")

        try:
            # Step 1: Scrape
            scraped_data = self.scraper.scrape_policy(url, use_selenium)
            if not scraped_data['success']:
                logger.error(f"Scraping failed for {app_name}")
                return None

            # Step 2: Analyze
            analysis = self.analyzer.analyze_policy(scraped_data['text'])
            if 'error' in analysis:
                logger.error(f"Analysis failed for {app_name}: {analysis['error']}")
                return None

            # Step 3: Score
            scoring = self.scorer.calculate_risk_score(analysis)

            # Step 4: Generate reports
            visualizations = []
            try:
                visualizations = self.reporter.create_visualizations(app_name, scoring)
                # Move visualizations to workflow viz directory
                for viz_path in visualizations:
                    viz_file = Path(viz_path)
                    if viz_file.exists():
                        new_path = self.viz_dir / viz_file.name
                        viz_file.rename(new_path)
            except Exception as e:
                logger.warning(f"Visualization failed for {app_name}: {e}")

            # Generate JSON report in workflow directory
            json_path = self.reports_dir / f"{app_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_data = {
                'app_name': app_name,
                'url': url,
                'category': app.get('category', ''),
                'notes': app.get('notes', ''),
                'analysis': analysis,
                'scoring': scoring,
                'timestamp': datetime.now().isoformat()
            }
            self.file_handler.save_json(report_data, str(json_path))

            logger.info(f"Successfully analyzed {app_name}")
            return report_data

        except Exception as e:
            logger.error(f"Error analyzing {app_name}: {e}")
            return None

    def batch_analyze(self,
                     apps: Optional[List[Dict]] = None,
                     use_selenium: bool = False,
                     resume_from_checkpoint: Optional[str] = None) -> List[Dict]:
        """
        Batch analyze multiple apps with parallel processing

        Args:
            apps: List of apps (uses loaded apps if not specified)
            use_selenium: Whether to use Selenium
            resume_from_checkpoint: Path to checkpoint file to resume from

        Returns:
            List of successful analysis results
        """
        apps = apps or self.apps_to_analyze
        if not apps:
            raise ValueError("No apps to analyze. Load from CSV first.")

        # Handle checkpoint resume
        completed_names = set()
        if resume_from_checkpoint:
            checkpoint = self.load_checkpoint(resume_from_checkpoint)
            completed_names = set(checkpoint['completed'])
            logger.info(f"Resuming from checkpoint: skipping {len(completed_names)} completed apps")

        # Filter out already completed apps
        apps_to_process = [app for app in apps if app['app_name'] not in completed_names]

        logger.info(f"Batch analyzing {len(apps_to_process)} apps (max {self.max_concurrent} concurrent)")

        results = []
        failed = []

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit all tasks
            future_to_app = {
                executor.submit(self.analyze_single_app, app, use_selenium): app
                for app in apps_to_process
            }

            # Process with progress bar
            with tqdm(total=len(apps_to_process), desc="Analyzing apps") as pbar:
                for future in concurrent.futures.as_completed(future_to_app):
                    app = future_to_app[future]
                    app_name = app['app_name']

                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            self.completed_apps.append(app)
                            logger.info(f"✓ {app_name}")
                        else:
                            failed.append(app)
                            self.failed_apps.append(app)
                            logger.warning(f"✗ {app_name}")

                    except Exception as e:
                        logger.error(f"Exception for {app_name}: {e}")
                        failed.append(app)
                        self.failed_apps.append(app)

                    pbar.update(1)
                    pbar.set_postfix({'success': len(results), 'failed': len(failed)})

                    # Save checkpoint periodically
                    if len(results) % self.checkpoint_interval == 0:
                        self.save_checkpoint()

        # Final checkpoint
        self.save_checkpoint()

        # Save summary
        summary = {
            'total_apps': len(apps_to_process),
            'successful': len(results),
            'failed': len(failed),
            'failed_apps': [app['app_name'] for app in failed],
            'timestamp': datetime.now().isoformat()
        }
        self.file_handler.save_json(summary, str(self.output_dir / 'batch_summary.json'))

        self.analyses = results
        logger.info(f"Batch analysis complete: {len(results)}/{len(apps_to_process)} successful")

        return results

    def comparative_analysis(self, analyses: Optional[List[Dict]] = None) -> Dict:
        """
        Run comparative analysis on all completed analyses

        Args:
            analyses: List of analyses (uses self.analyses if not specified)

        Returns:
            Comparative analysis report
        """
        analyses = analyses or self.analyses

        if not analyses:
            # Try loading from reports directory
            logger.info("No analyses in memory, loading from reports directory")
            analyses = load_analyses_from_directory(str(self.reports_dir))

        if len(analyses) < 2:
            raise ValueError("Need at least 2 analyses for comparison")

        logger.info(f"Running comparative analysis on {len(analyses)} apps")

        analyzer = ComparativeAnalyzer(analyses)
        report = analyzer.generate_comparative_report()

        # Save report
        report_path = self.stats_dir / f"comparative_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.file_handler.save_json(report, str(report_path))
        logger.info(f"Comparative report saved: {report_path}")

        return report

    def generate_summary_markdown(self, comparative_report: Dict) -> str:
        """
        Generate research summary in Markdown format

        Args:
            comparative_report: Comparative analysis report

        Returns:
            Path to generated markdown file
        """
        logger.info("Generating research summary markdown")

        stats = comparative_report['statistics']
        metadata = comparative_report['metadata']

        # Build markdown content
        md_content = f"""# Privacy Policy Research Summary

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Apps Analyzed**: {metadata['num_apps_analyzed']}
**Analysis Period**: {stats['summary']['analysis_date_range']['earliest']} to {stats['summary']['analysis_date_range']['latest']}

---

## Executive Summary

This study analyzed {metadata['num_apps_analyzed']} healthcare application privacy policies using AI-powered analysis with {self.depth} depth mode.

### Key Findings

**Overall Privacy Risk**:
- Mean score: {stats['overall_risk']['mean']:.2f}/100
- Median: {stats['overall_risk']['median']:.2f}/100
- Range: {stats['overall_risk']['min']:.2f} - {stats['overall_risk']['max']:.2f}

**Compliance Landscape**:
- HIPAA mentioned: {stats['compliance_stats']['hipaa_mentioned']['percentage']:.1f}% of apps
- Retention period specified: {stats['compliance_stats']['retention_period_specified']['percentage']:.1f}% of apps
- Business Associate Agreements: {stats['compliance_stats']['business_associate_agreement']['percentage']:.1f}% of apps

**Red Flags Identified**:
- Total red flags: {stats['red_flag_stats']['total_flags']}
- Average per app: {stats['red_flag_stats']['avg_per_app']:.1f}
- Unique concerns: {stats['red_flag_stats']['unique_flags']}

---

## Detailed Findings

### Most Common Privacy Concerns

"""

        # Add top red flags
        for i, flag in enumerate(stats['red_flag_stats']['most_common'][:10], 1):
            md_content += f"{i}. **{flag['flag']}** - Found in {flag['count']} apps ({flag['percentage']:.1f}%)\n"

        md_content += "\n### Category Analysis\n\n"

        # Add category stats
        for category, category_stats in stats['category_stats'].items():
            md_content += f"#### {category.replace('_', ' ').title()}\n"
            md_content += f"- Mean: {category_stats['mean']:.2f}\n"
            md_content += f"- Median: {category_stats['median']:.2f}\n"
            md_content += f"- Best: {category_stats['max']:.2f}\n"
            md_content += f"- Worst: {category_stats['min']:.2f}\n\n"

        # Add recommendations
        md_content += "\n## Recommendations\n\n"
        for i, rec in enumerate(comparative_report.get('recommendations', []), 1):
            md_content += f"{i}. {rec}\n\n"

        # Add research quotes section
        quotes = comparative_report.get('research_quotes', {})
        if quotes:
            md_content += "\n## Research Quotes\n\n"
            for category, findings in list(quotes.items())[:3]:
                md_content += f"### {category}\n\n"
                for finding in findings[:2]:
                    md_content += f"**{finding['app']}**: {finding['finding']}\n\n"
                    if finding.get('quote'):
                        md_content += f"> \"{finding['quote']}\"\n\n"

        # Add methodology
        md_content += f"""
---

## Methodology

### Analysis Approach
- **Tool**: Privacy Policy Analyzer for Healthcare Apps v2.0
- **Model**: {self.model} (with automatic fallback)
- **Analysis Depth**: {self.depth}
- **Caching**: Enabled for efficiency

### Categories Analyzed
"""
        for category in self.config.get('analysis', {}).get('categories', []):
            md_content += f"- {category}\n"

        md_content += f"""

### Red Flags Monitored
"""
        for flag in self.config.get('analysis', {}).get('red_flags', [])[:10]:
            md_content += f"- {flag}\n"

        md_content += "\n### Statistical Tests\n"
        md_content += "- Descriptive statistics (mean, median, std dev)\n"
        md_content += "- Percentile analysis\n"
        md_content += "- Correlation analysis (Pearson, point-biserial)\n"
        md_content += "- K-means clustering\n"

        # Add app list
        md_content += "\n## Appendix: Apps Analyzed\n\n"
        md_content += "| # | App Name | Category |\n"
        md_content += "|---|----------|----------|\n"

        for i, app_name in enumerate(metadata['app_names'], 1):
            # Try to get category from original analyses
            category = "N/A"
            for analysis in self.analyses:
                if analysis.get('app_name') == app_name:
                    category = analysis.get('category', 'N/A')
                    break
            md_content += f"| {i} | {app_name} | {category} |\n"

        # Save markdown
        md_path = self.output_dir / f"research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.file_handler.save_text(md_content, str(md_path))
        logger.info(f"Research summary saved: {md_path}")

        return str(md_path)

    def export_statistics(self, formats: List[str] = ['csv', 'excel']) -> Dict[str, str]:
        """
        Export statistics in multiple formats

        Args:
            formats: List of formats to export ('csv', 'excel', 'latex')

        Returns:
            Dictionary mapping format to file path
        """
        logger.info(f"Exporting statistics in formats: {formats}")

        exports = {}

        # Load analyses if not in memory
        if not self.analyses:
            self.analyses = load_analyses_from_directory(str(self.reports_dir))

        if not self.analyses:
            raise ValueError("No analyses available for export")

        # CSV Export (wide format)
        if 'csv' in formats:
            csv_path = self.stats_dir / f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                # Determine all columns
                fieldnames = ['app_name', 'url', 'category', 'overall_score', 'transparency_score',
                            'confidence_score', 'red_flag_count']

                # Add category columns
                categories = ['data_collection', 'data_usage', 'third_party_sharing',
                            'data_retention', 'user_rights', 'security_measures',
                            'compliance', 'older_adult_considerations']
                fieldnames.extend(categories)

                # Add compliance flags
                fieldnames.extend(['hipaa_mentioned', 'gdpr_mentioned', 'retention_specified'])

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for analysis in self.analyses:
                    row = {
                        'app_name': analysis.get('app_name', ''),
                        'url': analysis.get('url', ''),
                        'category': analysis.get('category', ''),
                        'overall_score': analysis.get('scoring', {}).get('overall_score', 0),
                        'transparency_score': analysis.get('analysis', {}).get('overall_transparency_score', 0),
                        'confidence_score': analysis.get('analysis', {}).get('confidence_score', 0),
                        'red_flag_count': len(analysis.get('scoring', {}).get('red_flags', []))
                    }

                    # Add category scores
                    analysis_data = analysis.get('analysis', {})
                    for cat in categories:
                        row[cat] = analysis_data.get(cat, {}).get('score', 0)

                    # Add compliance flags
                    compliance = analysis_data.get('compliance', {})
                    row['hipaa_mentioned'] = 1 if compliance.get('hipaa_mentioned') else 0
                    row['gdpr_mentioned'] = 1 if compliance.get('gdpr_mentioned') else 0

                    retention = analysis_data.get('data_retention', {})
                    row['retention_specified'] = 1 if retention.get('duration_specified') else 0

                    writer.writerow(row)

            exports['csv'] = str(csv_path)
            logger.info(f"CSV exported: {csv_path}")

        # Excel Export
        if 'excel' in formats:
            try:
                import pandas as pd

                excel_path = self.stats_dir / f"analysis_workbook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
                    # Sheet 1: Summary data (same as CSV)
                    df_data = []
                    for analysis in self.analyses:
                        row = {
                            'App Name': analysis.get('app_name', ''),
                            'URL': analysis.get('url', ''),
                            'Category': analysis.get('category', ''),
                            'Overall Score': analysis.get('scoring', {}).get('overall_score', 0),
                            'Transparency': analysis.get('analysis', {}).get('overall_transparency_score', 0),
                            'Red Flags': len(analysis.get('scoring', {}).get('red_flags', []))
                        }

                        # Add category scores
                        analysis_data = analysis.get('analysis', {})
                        for cat in categories:
                            col_name = cat.replace('_', ' ').title()
                            row[col_name] = analysis_data.get(cat, {}).get('score', 0)

                        df_data.append(row)

                    df_summary = pd.DataFrame(df_data)
                    df_summary.to_excel(writer, sheet_name='Summary', index=False)

                    # Sheet 2: Red Flags
                    red_flag_data = []
                    for analysis in self.analyses:
                        app_name = analysis.get('app_name', '')
                        for flag in analysis.get('scoring', {}).get('red_flags', []):
                            if isinstance(flag, dict):
                                red_flag_data.append({
                                    'App': app_name,
                                    'Category': flag.get('category', ''),
                                    'Severity': flag.get('severity', ''),
                                    'Description': flag.get('description', '')
                                })

                    if red_flag_data:
                        df_flags = pd.DataFrame(red_flag_data)
                        df_flags.to_excel(writer, sheet_name='Red Flags', index=False)

                exports['excel'] = str(excel_path)
                logger.info(f"Excel exported: {excel_path}")

            except ImportError:
                logger.warning("pandas not available, skipping Excel export")

        return exports

    def validate_analyses(self,
                         strict_mode: bool = False,
                         save_report: bool = True) -> Dict:
        """
        Validate all completed analyses for quality and consistency

        Args:
            strict_mode: If True, treat warnings as errors
            save_report: Whether to save validation report

        Returns:
            Validation results dictionary
        """
        logger.info("Validating analyses for quality and consistency...")

        if not self.analyses:
            logger.warning("No analyses to validate")
            return {
                'summary': {
                    'total_analyses': 0,
                    'valid_analyses': 0,
                    'invalid_analyses': 0,
                    'validation_rate': 0
                }
            }

        # Update validator strict mode
        self.validator.strict_mode = strict_mode

        # Run batch validation with anomaly detection
        validation_results = self.validator.validate_batch(
            self.analyses,
            detect_anomalies=True
        )

        # Generate and save report if requested
        if save_report:
            report_path = self.stats_dir / 'validation_report.txt'
            report = self.validator.generate_validation_report(
                validation_results,
                output_path=str(report_path)
            )
            logger.info(f"Validation report saved to: {report_path}")

            # Also save JSON version for programmatic access
            json_path = self.stats_dir / 'validation_results.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2)
            logger.info(f"Validation results (JSON) saved to: {json_path}")

        # Log summary
        summary = validation_results['summary']
        logger.info(f"Validation complete:")
        logger.info(f"  Total: {summary['total_analyses']}")
        logger.info(f"  Valid: {summary['valid_analyses']}")
        logger.info(f"  Invalid: {summary['invalid_analyses']}")
        logger.info(f"  Validation rate: {summary['validation_rate']:.1f}%")

        if summary['invalid_analyses'] > 0:
            logger.warning(
                f"{summary['invalid_analyses']} analyses failed validation. "
                "Check validation_report.txt for details."
            )

        return validation_results

    def run_complete_workflow(self,
                             csv_path: Optional[str] = None,
                             generate_dashboard: bool = True,
                             validate: bool = True,
                             strict_validation: bool = False) -> Dict:
        """
        Run complete end-to-end workflow

        Args:
            csv_path: Path to CSV file (uses self.input_csv if not specified)
            generate_dashboard: Whether to generate dashboard (requires implementation)
            validate: Whether to run quality validation
            strict_validation: If True, treat validation warnings as errors

        Returns:
            Dictionary with paths to all outputs
        """
        logger.info("=" * 70)
        logger.info("STARTING COMPLETE RESEARCH WORKFLOW")
        logger.info("=" * 70)

        workflow_start = time.time()
        outputs = {}

        # Step 1: Load apps
        logger.info("\n[Step 1/6] Loading apps from CSV...")
        self.load_apps_from_csv(csv_path)

        # Step 2: Batch analyze
        logger.info(f"\n[Step 2/6] Analyzing {len(self.apps_to_analyze)} apps...")
        self.batch_analyze()
        outputs['analyses_count'] = len(self.analyses)

        # Step 3: Validate analyses (NEW)
        if validate:
            logger.info("\n[Step 3/6] Validating analyses...")
            validation_results = self.validate_analyses(
                strict_mode=strict_validation,
                save_report=True
            )
            outputs['validation_report'] = str(self.stats_dir / 'validation_report.txt')
            outputs['validation_results'] = str(self.stats_dir / 'validation_results.json')

            # Check if validation passed
            if validation_results['summary']['invalid_analyses'] > 0:
                if strict_validation:
                    logger.error("Validation failed in strict mode. Aborting workflow.")
                    return {
                        'status': 'failed',
                        'reason': 'validation_failed',
                        'validation_results': validation_results,
                        'outputs': outputs
                    }
                else:
                    logger.warning(
                        "Some analyses failed validation but continuing in non-strict mode."
                    )
        else:
            logger.info("\n[Step 3/6] Skipping validation (validate=False)")

        # Step 4: Comparative analysis
        logger.info("\n[Step 4/6] Running comparative analysis...")
        comparative_report = self.comparative_analysis()
        outputs['comparative_report'] = str(self.stats_dir / 'comparative_report.json')

        # Step 5: Export statistics
        logger.info("\n[Step 5/6] Exporting statistics...")
        exports = self.export_statistics(formats=['csv', 'excel'])
        outputs.update(exports)

        # Step 6: Generate research summary
        logger.info("\n[Step 6/6] Generating research summary...")
        summary_path = self.generate_summary_markdown(comparative_report)
        outputs['research_summary'] = summary_path

        workflow_duration = time.time() - workflow_start

        logger.info("\n" + "=" * 70)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Duration: {workflow_duration/60:.1f} minutes")
        logger.info(f"Apps analyzed: {len(self.analyses)}/{len(self.apps_to_analyze)}")
        logger.info(f"Outputs saved to: {self.output_dir}")
        logger.info(f"\nKey outputs:")
        for key, path in outputs.items():
            logger.info(f"  {key}: {path}")

        outputs['status'] = 'success'
        return outputs
