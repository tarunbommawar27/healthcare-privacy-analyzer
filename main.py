"""
Privacy Policy Analyzer for Healthcare Apps - Enhanced Version
Main entry point with advanced CLI interface
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.modules.scraper import PolicyScraper
from src.modules.analyzer import PolicyAnalyzer
from src.modules.scorer import RiskScorer
from src.modules.reporter import ReportGenerator
from src.utils.logger import setup_logger, get_logger
from src.utils.file_handler import FileHandler

# Initialize colorama for colored terminal output
init(autoreset=True)

# Load environment variables
load_dotenv()


def validate_api_keys():
    """Validate that at least one LLM API key is available"""
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    has_openai = openai_key and openai_key.startswith('sk-')
    has_anthropic = anthropic_key and anthropic_key.startswith('sk-ant-')

    if not has_openai and not has_anthropic:
        print(f"\n{Fore.RED}{'=' * 70}")
        print(f"{Fore.RED}ERROR: No valid API keys found!")
        print(f"{Fore.RED}{'=' * 70}\n")
        print(f"{Fore.YELLOW}You need to configure at least one LLM provider:")
        print(f"\n{Fore.CYAN}Option 1: OpenAI")
        print(f"  1. Get API key from: https://platform.openai.com/api-keys")
        print(f"  2. Add to .env file: OPENAI_API_KEY=sk-...")
        print(f"\n{Fore.CYAN}Option 2: Anthropic Claude")
        print(f"  1. Get API key from: https://console.anthropic.com/")
        print(f"  2. Add to .env file: ANTHROPIC_API_KEY=sk-ant-...")
        print(f"\n{Fore.GREEN}Recommended: Configure both for automatic fallback support\n")
        return False

    # Show available providers
    providers = []
    if has_openai:
        providers.append("OpenAI")
    if has_anthropic:
        providers.append("Anthropic Claude")

    print(f"{Fore.GREEN}✓ Available LLM providers: {', '.join(providers)}")
    return True


class PrivacyPolicyAnalyzer:
    """Main application class with enhanced features"""

    def __init__(self, config_path: str = "config/config.yaml",
                 model_override: str = None, analysis_depth: str = None,
                 use_cache: bool = True):
        """
        Initialize the analyzer

        Args:
            config_path: Path to configuration file
            model_override: Override model selection
            analysis_depth: Analysis depth (quick/standard/deep)
            use_cache: Whether to use response caching
        """
        self.file_handler = FileHandler()
        self.config = self.file_handler.load_yaml(config_path)

        # Setup logging
        log_config = self.config.get('logging', {})
        self.logger = setup_logger(
            log_file=log_config.get('file', 'logs/analyzer.log'),
            level=log_config.get('level', 'INFO')
        )

        # Get analysis depth
        if analysis_depth is None:
            analysis_depth = self.config.get('analysis', {}).get('default_depth', 'standard')

        # Initialize modules
        self.scraper = PolicyScraper(self.config.get('scraping', {}))

        # Initialize analyzer with correct parameters
        self.analyzer = PolicyAnalyzer(
            config=self.config,
            model_override=model_override,
            analysis_depth=analysis_depth,
            use_cache=use_cache
        )
        self.scorer = RiskScorer(self.config)
        self.reporter = ReportGenerator(self.config)

        self.logger.info(f"Privacy Policy Analyzer initialized (depth: {analysis_depth}, cache: {use_cache})")

    def show_cost_estimate(self, policy_text: str):
        """Display cost estimate before analysis"""
        print(f"\n{Fore.CYAN}Cost Estimation:")
        print(f"{Fore.CYAN}{'-' * 50}")

        cost_info = self.analyzer.estimate_cost(policy_text)

        if 'error' not in cost_info:
            print(f"  Model: {cost_info['model']}")
            print(f"  Input tokens: {cost_info['input_tokens']:,}")
            print(f"  Estimated output tokens: {cost_info['estimated_output_tokens']:,}")
            print(f"  Total tokens: {cost_info['total_tokens']:,}")
            print(f"  {Fore.YELLOW}Estimated cost: ${cost_info['estimated_cost_usd']:.4f} USD")
        else:
            print(f"  {Fore.YELLOW}Cost estimation unavailable")

        print()

    def analyze_single_policy(self, app_name: str, url: str,
                             use_selenium: bool = False,
                             show_cost: bool = True,
                             force_reanalyze: bool = False) -> dict:
        """
        Analyze a single privacy policy

        Args:
            app_name: Application/service name
            url: Privacy policy URL
            use_selenium: Whether to use Selenium for scraping
            show_cost: Whether to show cost estimate
            force_reanalyze: Force re-analysis bypassing cache

        Returns:
            Complete analysis results
        """
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}Analyzing Privacy Policy for: {Fore.YELLOW}{app_name}")
        print(f"{Fore.CYAN}{'=' * 70}\n")

        # Step 1: Scrape policy
        print(f"{Fore.GREEN}[1/4] Scraping privacy policy...")
        scraped_data = self.scraper.scrape_policy(url, use_selenium)

        if not scraped_data['success']:
            print(f"{Fore.RED}✗ Failed to scrape policy from {url}")
            return None

        print(f"{Fore.GREEN}✓ Successfully scraped {scraped_data['length']:,} characters")

        # Save raw data
        if self.config.get('output', {}).get('save_raw_data', True):
            raw_dir = self.config.get('paths', {}).get('raw_data', 'data/raw')
            self.file_handler.ensure_dir(raw_dir)
            raw_filename = self.file_handler.generate_filename(f"{app_name}_raw", "txt")
            raw_path = f"{raw_dir}/{raw_filename}"
            self.file_handler.save_text(scraped_data['text'], raw_path)
            self.logger.info(f"Saved raw data to {raw_path}")

        # Show cost estimate
        if show_cost and self.config.get('cost_estimation', {}).get('enabled', True):
            self.show_cost_estimate(scraped_data['text'])

        # Step 2: Analyze with LLM
        print(f"{Fore.GREEN}[2/4] Analyzing policy with LLM...")
        print(f"{Fore.YELLOW}   Provider: {self.analyzer.primary_provider}")
        print(f"{Fore.YELLOW}   Model: {self.analyzer.primary_model}")
        print(f"{Fore.YELLOW}   Depth: {self.analyzer.analysis_depth}")
        print(f"{Fore.YELLOW}   Cache: {'enabled' if self.analyzer.use_cache else 'disabled'}")

        if force_reanalyze:
            print(f"{Fore.YELLOW}   Force re-analyze: bypassing cache")

        with tqdm(total=100, desc="   Analysis progress", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            analysis = self.analyzer.analyze_policy(scraped_data['text'], force_reanalyze=force_reanalyze)
            pbar.update(100)

        if 'error' in analysis:
            print(f"{Fore.RED}✗ Analysis failed: {analysis['error']}")
            return None

        # Show analysis metadata
        metadata = analysis.get('metadata', {})
        if 'analysis_time_seconds' in metadata:
            print(f"{Fore.GREEN}✓ Analysis complete ({metadata['analysis_time_seconds']}s)")
        else:
            print(f"{Fore.GREEN}✓ Analysis complete")

        if 'model_used' in metadata:
            print(f"{Fore.CYAN}   Model used: {metadata['model_used']}")
        if 'tokens_used' in metadata and metadata['tokens_used']:
            print(f"{Fore.CYAN}   Tokens used: {metadata['tokens_used']:,}")

        # Step 3: Calculate risk score
        print(f"\n{Fore.GREEN}[3/4] Calculating risk scores...")
        scoring = self.scorer.calculate_risk_score(analysis)

        # Display scores
        overall_score = scoring.get('overall_score', 0)
        risk_level = scoring.get('risk_level', 'UNKNOWN')
        risk_color = {
            'LOW': Fore.GREEN,
            'MEDIUM': Fore.YELLOW,
            'HIGH': Fore.MAGENTA,
            'CRITICAL': Fore.RED
        }.get(risk_level, Fore.WHITE)

        print(f"{Fore.GREEN}✓ Overall Risk Score: {risk_color}{overall_score}/100 ({risk_level})")

        # Show transparency and confidence scores
        if 'overall_transparency_score' in analysis:
            transp_score = analysis['overall_transparency_score']
            print(f"{Fore.GREEN}✓ Transparency Score: {Fore.CYAN}{transp_score}/100")

        if 'confidence_score' in analysis:
            conf_score = analysis['confidence_score']
            print(f"{Fore.GREEN}✓ Confidence Score: {Fore.CYAN}{conf_score}/100")

        red_flags_count = len(scoring.get('red_flags', []))
        print(f"{Fore.GREEN}✓ Red Flags Detected: {Fore.RED}{red_flags_count}")

        # Step 4: Generate reports
        print(f"\n{Fore.GREEN}[4/4] Generating reports and visualizations...")

        # Create visualizations
        visualizations = []
        if self.config.get('output', {}).get('include_visualizations', True):
            try:
                visualizations = self.reporter.create_visualizations(app_name, scoring)
                print(f"{Fore.GREEN}✓ Created {len(visualizations)} visualizations")
            except Exception as e:
                self.logger.warning(f"Visualization creation failed: {str(e)}")
                print(f"{Fore.YELLOW}⚠ Visualization creation failed: {str(e)}")

        # Generate reports
        report_formats = self.config.get('output', {}).get('report_format', ['html', 'json'])
        generated_reports = []

        if 'html' in report_formats:
            html_path = self.reporter.generate_html_report(app_name, url, analysis, scoring, visualizations)
            generated_reports.append(html_path)
            print(f"{Fore.GREEN}✓ HTML report: {Fore.CYAN}{html_path}")

        if 'json' in report_formats:
            json_path = self.reporter.generate_json_report(app_name, url, analysis, scoring)
            generated_reports.append(json_path)
            print(f"{Fore.GREEN}✓ JSON report: {Fore.CYAN}{json_path}")

        # Print enhanced summary
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}ANALYSIS SUMMARY")
        print(f"{Fore.CYAN}{'=' * 70}")
        print(f"\n{analysis.get('summary', 'No summary available')}\n")

        # Show category scores
        print(f"{Fore.CYAN}Category Scores:")
        for category, score in scoring.get('category_scores', {}).items():
            score_val = score if isinstance(score, (int, float)) else 50
            score_color = Fore.GREEN if score_val > 70 else Fore.YELLOW if score_val > 50 else Fore.RED
            print(f"  {category:.<30} {score_color}{score_val}/100")

        # Show red flags
        if scoring.get('red_flags'):
            print(f"\n{Fore.RED}🚩 Red Flags Detected:")
            for i, flag in enumerate(scoring['red_flags'][:5], 1):  # Show first 5
                if isinstance(flag, dict):
                    severity = flag.get('severity', 'unknown')
                    desc = flag.get('description', str(flag))
                    sev_color = Fore.RED if severity == 'high' else Fore.YELLOW if severity == 'medium' else Fore.WHITE
                    print(f"  {i}. [{sev_color}{severity.upper()}{Fore.RESET}] {desc}")
                else:
                    print(f"  {i}. {flag}")

            if len(scoring['red_flags']) > 5:
                print(f"  ... and {len(scoring['red_flags']) - 5} more (see full report)")

        # Show positive practices
        positive_practices = analysis.get('positive_practices', [])
        if positive_practices:
            print(f"\n{Fore.GREEN}✓ Positive Practices:")
            for i, practice in enumerate(positive_practices[:3], 1):
                if isinstance(practice, dict):
                    desc = practice.get('description', str(practice))
                    print(f"  {i}. {desc}")
                else:
                    print(f"  {i}. {practice}")

        # Show quotable findings for research
        quotable = analysis.get('quotable_findings', [])
        if quotable:
            print(f"\n{Fore.MAGENTA}📝 Quotable Research Findings:")
            for i, finding in enumerate(quotable[:2], 1):
                if isinstance(finding, dict):
                    print(f"  {i}. {finding.get('finding', '')}")
                    if 'quote' in finding:
                        print(f"     \"{finding['quote'][:100]}...\"")

        # Show cache statistics
        cache_stats = self.analyzer.get_cache_stats()
        if cache_stats['total_requests'] > 0:
            print(f"\n{Fore.CYAN}Cache Statistics:")
            print(f"  Hit rate: {cache_stats['hit_rate_percent']}% ({cache_stats['cache_hits']}/{cache_stats['total_requests']})")

        return {
            'app_name': app_name,
            'url': url,
            'scraped_data': scraped_data,
            'analysis': analysis,
            'scoring': scoring,
            'reports': generated_reports,
            'visualizations': visualizations
        }

    def analyze_multiple_policies(self, use_selenium: bool = False,
                                  show_cost: bool = True,
                                  force_reanalyze: bool = False):
        """
        Analyze multiple policies from config file

        Args:
            use_selenium: Whether to use Selenium for scraping
            show_cost: Whether to show cost estimates
            force_reanalyze: Force re-analysis bypassing cache
        """
        targets = self.config.get('targets', [])

        if not targets:
            print(f"{Fore.RED}No targets configured in config.yaml")
            return

        print(f"\n{Fore.CYAN}Analyzing {len(targets)} privacy policies...")

        results = []
        for i, target in enumerate(targets, 1):
            app_name = target.get('name', f'App_{i}')
            url = target.get('url')

            if not url:
                print(f"{Fore.RED}Skipping {app_name}: No URL provided")
                continue

            result = self.analyze_single_policy(
                app_name, url, use_selenium, show_cost, force_reanalyze
            )
            if result:
                results.append(result)

            print("\n")

        # Generate comparison report
        if len(results) > 1:
            print(f"\n{Fore.GREEN}Generating comparison report...")
            comparison_path = self.reporter.generate_comparison_report(results)
            print(f"{Fore.GREEN}✓ Comparison report: {Fore.CYAN}{comparison_path}")

        print(f"\n{Fore.GREEN}{'=' * 70}")
        print(f"{Fore.GREEN}Analysis complete! Processed {len(results)}/{len(targets)} policies")
        print(f"{Fore.GREEN}{'=' * 70}\n")

        # Show cache statistics
        cache_stats = self.analyzer.get_cache_stats()
        if cache_stats['cache_enabled']:
            print(f"{Fore.CYAN}Session Cache Statistics:")
            print(f"  Total requests: {cache_stats['total_requests']}")
            print(f"  Cache hits: {cache_stats['cache_hits']}")
            print(f"  Cache misses: {cache_stats['cache_misses']}")
            print(f"  Hit rate: {cache_stats['hit_rate_percent']}%\n")


def main():
    """Main CLI entry point with enhanced argument parsing"""
    parser = argparse.ArgumentParser(
        description='Privacy Policy Analyzer for Healthcare Apps - Enhanced Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single policy with default settings
  python main.py --url https://example.com/privacy --name "Example App"

  # Use Claude Sonnet 4 with deep analysis
  python main.py --url https://example.com/privacy --name "App" --model claude --depth deep

  # Use GPT-4 with caching disabled
  python main.py --url https://example.com/privacy --name "App" --model gpt4 --no-cache

  # Auto-select model based on available API keys
  python main.py --url https://example.com/privacy --name "App" --model auto

  # Analyze all policies from config
  python main.py --analyze-all

  # Quick analysis with cost estimation
  python main.py --url https://example.com/privacy --name "App" --depth quick --show-cost

  # Force re-analysis (bypass cache)
  python main.py --url https://example.com/privacy --name "App" --force-reanalyze

  # Use Selenium for dynamic content
  python main.py --url https://example.com/privacy --name "App" --selenium

  # Custom config file
  python main.py --analyze-all --config custom_config.yaml
        """
    )

    # Required/optional arguments
    parser.add_argument(
        '--url',
        type=str,
        help='Privacy policy URL to analyze'
    )

    parser.add_argument(
        '--name',
        type=str,
        help='Application/service name'
    )

    parser.add_argument(
        '--analyze-all',
        action='store_true',
        help='Analyze all targets from config file'
    )

    # Model selection
    parser.add_argument(
        '--model',
        type=str,
        choices=['claude', 'gpt4', 'auto'],
        help='LLM model to use (claude=Claude Sonnet 4, gpt4=GPT-4, auto=auto-select)'
    )

    # Analysis depth
    parser.add_argument(
        '--depth',
        type=str,
        choices=['quick', 'standard', 'deep'],
        help='Analysis depth (quick=fast/high-level, standard=comprehensive, deep=in-depth with chain-of-thought)'
    )

    # Caching
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching'
    )

    parser.add_argument(
        '--force-reanalyze',
        action='store_true',
        help='Force re-analysis, bypassing cache'
    )

    # Cost estimation
    parser.add_argument(
        '--show-cost',
        action='store_true',
        default=True,
        help='Show cost estimate before analysis (default: enabled)'
    )

    parser.add_argument(
        '--no-cost-estimate',
        action='store_true',
        help='Hide cost estimate'
    )

    # Scraping
    parser.add_argument(
        '--selenium',
        action='store_true',
        help='Use Selenium for scraping (for dynamic content)'
    )

    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    args = parser.parse_args()

    # Print banner
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}  Privacy Policy Analyzer for Healthcare Apps")
    print(f"{Fore.CYAN}  Enhanced Version 2.0 with Advanced LLM Analysis")
    print(f"{Fore.CYAN}{'=' * 70}\n")

    # Validate arguments
    if not args.analyze_all and not args.url:
        parser.print_help()
        print(f"\n{Fore.RED}Error: Either --url or --analyze-all must be specified")
        sys.exit(1)

    if args.url and not args.name:
        parser.print_help()
        print(f"\n{Fore.RED}Error: --name is required when using --url")
        sys.exit(1)

    # Validate API keys
    if not validate_api_keys():
        sys.exit(1)

    try:
        # Initialize analyzer with options
        use_cache = not args.no_cache
        show_cost = args.show_cost and not args.no_cost_estimate

        analyzer = PrivacyPolicyAnalyzer(
            config_path=args.config,
            model_override=args.model,
            analysis_depth=args.depth,
            use_cache=use_cache
        )

        # Run analysis
        if args.analyze_all:
            analyzer.analyze_multiple_policies(
                use_selenium=args.selenium,
                show_cost=show_cost,
                force_reanalyze=args.force_reanalyze
            )
        else:
            analyzer.analyze_single_policy(
                args.name,
                args.url,
                use_selenium=args.selenium,
                show_cost=show_cost,
                force_reanalyze=args.force_reanalyze
            )

        print(f"\n{Fore.GREEN}✓ All operations completed successfully!")

    except FileNotFoundError as e:
        print(f"{Fore.RED}Error: Configuration file not found: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
