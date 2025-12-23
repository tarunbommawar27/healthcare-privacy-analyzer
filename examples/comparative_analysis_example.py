"""
Example: Using the Comparative Analyzer for Research

This script demonstrates how to use the comparative analysis features
to analyze multiple healthcare privacy policies and generate insights.
"""

import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.comparative_analyzer import (
    load_analyses_from_directory,
    ComparativeAnalyzer
)


def example_basic_comparison():
    """Basic comparative analysis example"""
    print("="*70)
    print("EXAMPLE 1: Basic Comparative Analysis")
    print("="*70)

    # Load all analyses from reports directory
    analyses = load_analyses_from_directory('outputs/reports/')

    if len(analyses) < 2:
        print("Need at least 2 analyses for comparison")
        print("Run some analyses first:")
        print("  python main.py --url <URL1> --name 'App1'")
        print("  python main.py --url <URL2> --name 'App2'")
        return

    # Create comparative analyzer
    analyzer = ComparativeAnalyzer(analyses)

    # Get basic statistics
    stats = analyzer.calculate_statistics()

    print(f"\nAnalyzing {stats['summary']['total_apps']} apps")
    print(f"\nOverall Risk Statistics:")
    print(f"  Mean: {stats['overall_risk']['mean']:.2f}")
    print(f"  Median: {stats['overall_risk']['median']:.2f}")
    print(f"  Std Dev: {stats['overall_risk']['std']:.2f}")
    print(f"  Range: {stats['overall_risk']['min']:.2f} - {stats['overall_risk']['max']:.2f}")

    print(f"\nCompliance Statistics:")
    hipaa = stats['compliance_stats']['hipaa_mentioned']
    print(f"  HIPAA mentioned: {hipaa['count']}/{analyzer.num_apps} ({hipaa['percentage']:.1f}%)")

    retention = stats['compliance_stats']['retention_period_specified']
    print(f"  Retention specified: {retention['count']}/{analyzer.num_apps} ({retention['percentage']:.1f}%)")


def example_red_flag_analysis():
    """Analyze red flag patterns"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Red Flag Pattern Analysis")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if not analyses:
        return

    analyzer = ComparativeAnalyzer(analyses)
    stats = analyzer.calculate_statistics()

    print(f"\nRed Flag Analysis:")
    print(f"  Total flags: {stats['red_flag_stats']['total_flags']}")
    print(f"  Unique flags: {stats['red_flag_stats']['unique_flags']}")
    print(f"  Avg per app: {stats['red_flag_stats']['avg_per_app']:.1f}")

    print(f"\nMost Common Red Flags:")
    for i, flag in enumerate(stats['red_flag_stats']['most_common'][:5], 1):
        print(f"  {i}. {flag['flag']} - {flag['count']} apps ({flag['percentage']:.1f}%)")

    print(f"\nBy Severity:")
    for severity, count in stats['red_flag_stats']['by_severity'].items():
        print(f"  {severity.upper()}: {count}")


def example_rankings():
    """Show app rankings"""
    print("\n" + "="*70)
    print("EXAMPLE 3: App Rankings")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if not analyses:
        return

    analyzer = ComparativeAnalyzer(analyses)
    stats = analyzer.calculate_statistics()

    print(f"\nOverall Risk Ranking (Higher is Better):")
    for rank in stats['rankings']['overall_risk'][:10]:
        print(f"  {rank['rank']}. {rank['app_name']}: {rank['value']:.2f} "
              f"(Percentile: {rank['percentile']:.1f})")

    # Category-specific ranking
    print(f"\nBest HIPAA Compliance:")
    for rank in stats['rankings']['category_rankings']['compliance'][:5]:
        print(f"  {rank['rank']}. {rank['app_name']}: {rank['value']:.2f}")


def example_best_practices():
    """Identify best practices"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Best Practice Identification")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if not analyses:
        return

    analyzer = ComparativeAnalyzer(analyses)
    best = analyzer.identify_best_practices()

    print(f"\nTop Performers in Data Retention:")
    for app in best.get('data_retention', [])[:3]:
        print(f"\n  {app['app_name']} (Score: {app['score']}/100)")
        for aspect in app.get('positive_aspects', [])[:2]:
            print(f"    ✓ {aspect}")


def example_research_quotes():
    """Extract research quotes"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Research Quote Extraction")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if not analyses:
        return

    analyzer = ComparativeAnalyzer(analyses)
    quotes = analyzer.extract_research_quotes()

    for category, findings in list(quotes.items())[:2]:
        print(f"\n{category}:")
        for finding in findings[:2]:
            print(f"\n  App: {finding['app']}")
            print(f"  Finding: {finding['finding']}")
            if finding.get('quote'):
                print(f"  Quote: \"{finding['quote'][:100]}...\"")
            print(f"  Significance: {finding['significance']}")


def example_clustering():
    """Show clustering results"""
    print("\n" + "="*70)
    print("EXAMPLE 6: App Clustering")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if len(analyses) < 3:
        print("Need at least 3 apps for clustering")
        return

    analyzer = ComparativeAnalyzer(analyses)
    stats = analyzer.calculate_statistics()

    clusters = stats.get('clusters', {}).get('clusters', [])
    if not clusters:
        return

    print(f"\nIdentified {len(clusters)} clusters:")
    for cluster in clusters:
        print(f"\nCluster {cluster['cluster_id']} ({cluster['size']} apps):")
        print(f"  Average score: {cluster['avg_score']:.2f}")
        print(f"  Apps:")
        for app in cluster['apps']:
            print(f"    - {app['app_name']} ({app['overall_score']:.2f})")


def example_full_report():
    """Generate and save full comparative report"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Generate Full Comparative Report")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if not analyses:
        return

    analyzer = ComparativeAnalyzer(analyses)
    report = analyzer.generate_comparative_report()

    # Save to file
    output_path = 'examples/comparative_report_example.json'
    Path('examples').mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"\nFull comparative report saved to: {output_path}")
    print(f"\nReport contains:")
    print(f"  - Statistics for {report['metadata']['num_apps_analyzed']} apps")
    print(f"  - Best practices from top performers")
    print(f"  - Worst practices from bottom performers")
    print(f"  - {len(report.get('recommendations', []))} recommendations")
    print(f"  - Research quotes organized by theme")


def example_correlations():
    """Show correlation analysis"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Correlation Analysis")
    print("="*70)

    analyses = load_analyses_from_directory('outputs/reports/')
    if len(analyses) < 3:
        print("Need at least 3 apps for correlation analysis")
        return

    analyzer = ComparativeAnalyzer(analyses)
    stats = analyzer.calculate_statistics()

    correlations = stats.get('correlations', {})

    if 'hipaa_vs_security' in correlations:
        corr = correlations['hipaa_vs_security']
        print(f"\nHIPAA Mention vs Security Score:")
        print(f"  Correlation: {corr['correlation']:.3f}")
        print(f"  P-value: {corr['p_value']:.4f}")
        print(f"  Significant: {'Yes' if corr['significant'] else 'No'}")

    if 'transparency_vs_risk' in correlations:
        corr = correlations['transparency_vs_risk']
        print(f"\nTransparency vs Overall Risk:")
        print(f"  Correlation: {corr['correlation']:.3f}")
        print(f"  P-value: {corr['p_value']:.4f}")
        print(f"  Significant: {'Yes' if corr['significant'] else 'No'}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("COMPARATIVE ANALYSIS EXAMPLES")
    print("Privacy Policy Analyzer for Healthcare Apps")
    print("="*70)

    # Check if we have any analyses
    analyses = load_analyses_from_directory('outputs/reports/')

    if not analyses:
        print("\n⚠️  No analyses found in outputs/reports/")
        print("\nTo run these examples, first analyze some apps:")
        print("\n  python main.py --url https://www.zocdoc.com/about/privacy/ --name 'Zocdoc'")
        print("  python main.py --url https://www.teladoc.com/privacy-policy/ --name 'Teladoc'")
        print("  python main.py --url https://www.betterhelp.com/privacy/ --name 'BetterHelp'")
        print("\nThen run this script again:")
        print("  python examples/comparative_analysis_example.py")
        return

    # Run examples
    example_basic_comparison()
    example_red_flag_analysis()
    example_rankings()
    example_best_practices()
    example_research_quotes()
    example_clustering()
    example_correlations()
    example_full_report()

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review the comparative_report_example.json file")
    print("  2. Modify the code above for your research needs")
    print("  3. Analyze more apps for richer comparisons")
    print("  4. Export data for statistical software (coming soon)")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
