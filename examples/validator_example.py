"""
Quality Validation Examples

This script demonstrates how to use the AnalysisValidator to ensure
data quality, consistency, and detect anomalies in privacy policy analyses.

Examples:
1. Validate a single analysis
2. Validate a directory of analyses
3. Detect anomalies across multiple apps
4. Generate validation reports
5. Use strict mode
6. Integrate with research workflow
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.validator import AnalysisValidator, load_and_validate_directory


def example_1_validate_single_analysis():
    """Example 1: Validate a single analysis result"""
    print("\n" + "=" * 80)
    print("Example 1: Validate Single Analysis")
    print("=" * 80)

    # Load a sample analysis (replace with actual path)
    analysis_path = "outputs/reports/sample_app_analysis.json"

    if not Path(analysis_path).exists():
        print(f"File not found: {analysis_path}")
        print("Skipping example 1...")
        return

    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    # Create validator
    validator = AnalysisValidator(strict_mode=False)

    # Validate
    result = validator.validate_single_analysis(analysis)

    # Display results
    print(f"\nApp: {result['app_name']}")
    print(f"Valid: {result['is_valid']}")

    if result['errors']:
        print(f"\n❌ Errors ({len(result['errors'])}):")
        for error in result['errors']:
            print(f"  - {error}")

    if result['warnings']:
        print(f"\n⚠ Warnings ({len(result['warnings'])}):")
        for warning in result['warnings']:
            print(f"  - {warning}")

    if result['info']:
        print(f"\nℹ Info:")
        for info in result['info']:
            print(f"  - {info}")


def example_2_validate_directory():
    """Example 2: Validate all analyses in a directory"""
    print("\n" + "=" * 80)
    print("Example 2: Validate Directory of Analyses")
    print("=" * 80)

    reports_dir = "outputs/reports/"

    if not Path(reports_dir).exists():
        print(f"Directory not found: {reports_dir}")
        print("Skipping example 2...")
        return

    # Validate all analyses in directory
    results = load_and_validate_directory(
        directory=reports_dir,
        strict_mode=False,
        output_report="outputs/validation_report.txt"
    )

    # Display summary
    summary = results['summary']
    print(f"\nValidation Summary:")
    print(f"  Total analyses:      {summary['total_analyses']}")
    print(f"  Valid:               {summary['valid_analyses']}")
    print(f"  Invalid:             {summary['invalid_analyses']}")
    print(f"  Validation rate:     {summary['validation_rate']:.1f}%")
    print(f"  Total errors:        {summary['total_errors']}")
    print(f"  Total warnings:      {summary['total_warnings']}")

    print(f"\nDetailed report saved to: outputs/validation_report.txt")


def example_3_detect_anomalies():
    """Example 3: Detect statistical anomalies"""
    print("\n" + "=" * 80)
    print("Example 3: Detect Anomalies")
    print("=" * 80)

    reports_dir = "outputs/reports/"

    if not Path(reports_dir).exists():
        print(f"Directory not found: {reports_dir}")
        print("Skipping example 3...")
        return

    # Load analyses
    analyses = []
    for json_file in Path(reports_dir).glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            analyses.append(json.load(f))

    if len(analyses) < 3:
        print("Need at least 3 analyses for anomaly detection")
        print("Skipping example 3...")
        return

    # Validate with anomaly detection
    validator = AnalysisValidator()
    results = validator.validate_batch(analyses, detect_anomalies=True)

    # Display anomalies
    if 'anomalies' in results:
        anomalies = results['anomalies']

        print("\n🔍 Detected Anomalies:")

        # Overall risk score anomalies
        if anomalies['overall_risk_score']:
            print("\n  Overall Risk Score:")
            for outlier in anomalies['overall_risk_score']:
                print(f"    - {outlier['app_name']}: {outlier['value']:.1f} "
                      f"(z-score: {outlier['z_score']:.2f}, "
                      f"{outlier['deviation']} deviation)")

        # Red flag count anomalies
        if anomalies['red_flag_count']:
            print("\n  Red Flag Count:")
            for outlier in anomalies['red_flag_count']:
                print(f"    - {outlier['app_name']}: {outlier['value']:.0f} flags "
                      f"(z-score: {outlier['z_score']:.2f}, "
                      f"{outlier['deviation']} deviation)")

        # Category anomalies
        if anomalies['category_scores']:
            print("\n  Category Scores:")
            for category, outliers in anomalies['category_scores'].items():
                print(f"\n    {category}:")
                for outlier in outliers:
                    print(f"      - {outlier['app_name']}: {outlier['value']:.1f} "
                          f"(z-score: {outlier['z_score']:.2f})")

        # Check if no anomalies
        total_anomalies = (
            len(anomalies['overall_risk_score']) +
            len(anomalies['overall_transparency_score']) +
            len(anomalies['confidence_score']) +
            len(anomalies['red_flag_count']) +
            sum(len(v) for v in anomalies['category_scores'].values())
        )

        if total_anomalies == 0:
            print("\n  ✓ No anomalies detected - all values within normal range")


def example_4_generate_report():
    """Example 4: Generate detailed validation report"""
    print("\n" + "=" * 80)
    print("Example 4: Generate Validation Report")
    print("=" * 80)

    reports_dir = "outputs/reports/"

    if not Path(reports_dir).exists():
        print(f"Directory not found: {reports_dir}")
        print("Skipping example 4...")
        return

    # Load analyses
    analyses = []
    for json_file in Path(reports_dir).glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            analyses.append(json.load(f))

    if not analyses:
        print("No analyses found")
        print("Skipping example 4...")
        return

    # Validate
    validator = AnalysisValidator()
    results = validator.validate_batch(analyses, detect_anomalies=True)

    # Generate report
    report_path = "outputs/validation_report_detailed.txt"
    report = validator.generate_validation_report(results, output_path=report_path)

    print(f"\nValidation report generated: {report_path}")
    print("\nReport preview (first 1500 characters):")
    print("-" * 80)
    print(report[:1500])
    if len(report) > 1500:
        print("\n... (truncated)")
    print("-" * 80)


def example_5_strict_mode():
    """Example 5: Use strict validation mode"""
    print("\n" + "=" * 80)
    print("Example 5: Strict Validation Mode")
    print("=" * 80)

    reports_dir = "outputs/reports/"

    if not Path(reports_dir).exists():
        print(f"Directory not found: {reports_dir}")
        print("Skipping example 5...")
        return

    # Validate with strict mode (warnings treated as errors)
    results_normal = load_and_validate_directory(
        directory=reports_dir,
        strict_mode=False
    )

    results_strict = load_and_validate_directory(
        directory=reports_dir,
        strict_mode=True
    )

    print("\nNormal Mode:")
    print(f"  Valid: {results_normal['summary']['valid_analyses']}")
    print(f"  Invalid: {results_normal['summary']['invalid_analyses']}")

    print("\nStrict Mode:")
    print(f"  Valid: {results_strict['summary']['valid_analyses']}")
    print(f"  Invalid: {results_strict['summary']['invalid_analyses']}")

    print("\nNote: Strict mode treats warnings as errors, resulting in more failures.")


def example_6_workflow_integration():
    """Example 6: Integrate validation with research workflow"""
    print("\n" + "=" * 80)
    print("Example 6: Research Workflow Integration")
    print("=" * 80)

    print("\nValidation is now integrated into the ResearchWorkflow class.")
    print("\nExample usage:")
    print("""
from src.modules.research_workflow import ResearchWorkflow

# Create workflow with validation enabled
workflow = ResearchWorkflow(
    input_csv='data/apps.csv',
    output_dir='research_output/',
    model='claude',
    depth='standard'
)

# Run complete workflow with validation
results = workflow.run_complete_workflow(
    validate=True,              # Enable validation (default: True)
    strict_validation=False     # Use lenient mode (default: False)
)

# Check if validation passed
if results['status'] == 'success':
    print("Workflow completed successfully!")
    print(f"Validation report: {results['validation_report']}")
else:
    print("Workflow failed during validation")

# Or validate separately
validation_results = workflow.validate_analyses(
    strict_mode=False,
    save_report=True
)
""")

    print("\nValidation outputs:")
    print("  - validation_report.txt:    Human-readable report")
    print("  - validation_results.json:  Machine-readable results with anomalies")


def example_7_custom_validation():
    """Example 7: Custom validation checks"""
    print("\n" + "=" * 80)
    print("Example 7: Custom Validation Checks")
    print("=" * 80)

    # Create a sample analysis with intentional issues
    sample_analysis = {
        'app_name': 'Test App',
        'analysis_date': '2025-01-15',
        'overall_risk_score': 75,
        'overall_transparency_score': 45,
        'confidence_score': 85,
        'categories': {
            'Data Collection': {
                'score': 60,
                'explanation': 'Collects extensive health data',
                'key_findings': [
                    'Tracks daily health metrics',
                    'Shares data with third parties'
                ]
            },
            'HIPAA Compliance': {
                'score': 30,
                'explanation': 'Limited HIPAA compliance',
                'key_findings': []  # This will trigger a warning
            }
        },
        'red_flags': [
            {
                'finding': 'Data sold to advertisers',
                'severity': 'critical',
                'quote': 'We may share your health information...',
                'category': 'Data Sharing'
            }
        ],
        'positive_practices': [],
        'metadata': {
            'model_used': 'claude-sonnet-4',
            'analysis_depth': 'standard',
            'policy_length': 5000
        }
    }

    # Validate
    validator = AnalysisValidator(strict_mode=False)
    result = validator.validate_single_analysis(sample_analysis)

    print(f"\nValidation Result for '{sample_analysis['app_name']}':")
    print(f"  Valid: {result['is_valid']}")

    if result['errors']:
        print(f"\n  ❌ Errors:")
        for error in result['errors']:
            print(f"    - {error}")

    if result['warnings']:
        print(f"\n  ⚠ Warnings:")
        for warning in result['warnings']:
            print(f"    - {warning}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("PRIVACY POLICY ANALYZER - QUALITY VALIDATION EXAMPLES")
    print("=" * 80)

    examples = [
        ("Validate Single Analysis", example_1_validate_single_analysis),
        ("Validate Directory", example_2_validate_directory),
        ("Detect Anomalies", example_3_detect_anomalies),
        ("Generate Report", example_4_generate_report),
        ("Strict Mode", example_5_strict_mode),
        ("Workflow Integration", example_6_workflow_integration),
        ("Custom Validation", example_7_custom_validation)
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run validator on your own analyses: python -m src.utils.validator outputs/reports/")
    print("2. Integrate with research workflow for automatic validation")
    print("3. Use strict mode for publication-quality data")
    print("4. Review validation reports to identify data quality issues")


if __name__ == "__main__":
    main()
