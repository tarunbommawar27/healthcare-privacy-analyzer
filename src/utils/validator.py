"""
Quality Validation System for Privacy Policy Analyses

This module provides comprehensive data quality checks, validation, and
anomaly detection for privacy policy analysis results.

Features:
- Analysis completeness checking
- Score validation and range checking
- Consistency validation (overall vs category scores)
- Anomaly detection (statistical outliers)
- Quality report generation
- Batch validation for comparative studies

Author: Privacy Policy Analyzer Team
Version: 2.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from scipy import stats
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)


class AnalysisValidator:
    """Validates privacy policy analysis results for quality and consistency"""

    # Required fields in analysis output
    REQUIRED_FIELDS = {
        'app_name': str,
        'analysis_date': str,
        'overall_risk_score': (int, float),
        'overall_transparency_score': (int, float),
        'confidence_score': (int, float),
        'categories': dict,
        'red_flags': list,
        'positive_practices': list,
        'metadata': dict
    }

    # Required category fields
    REQUIRED_CATEGORY_FIELDS = {
        'score': (int, float),
        'explanation': str,
        'key_findings': list
    }

    # Required red flag fields
    REQUIRED_RED_FLAG_FIELDS = {
        'finding': str,
        'severity': str,
        'quote': str,
        'category': str
    }

    # Valid severity levels
    VALID_SEVERITIES = {'critical', 'high', 'medium', 'low'}

    # Score ranges
    SCORE_MIN = 0
    SCORE_MAX = 100

    # Consistency tolerance (percentage points)
    CONSISTENCY_TOLERANCE = 15

    # Outlier detection threshold (z-score)
    OUTLIER_THRESHOLD = 3.0

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator

        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.validation_results = []

    def validate_single_analysis(self, analysis: Dict,
                                 check_consistency: bool = True) -> Dict:
        """
        Validate a single analysis result

        Args:
            analysis: Analysis dictionary to validate
            check_consistency: Whether to check score consistency

        Returns:
            Validation result dictionary with:
                - is_valid: bool
                - errors: List[str]
                - warnings: List[str]
                - info: List[str]
        """
        errors = []
        warnings = []
        info = []

        app_name = analysis.get('app_name', 'Unknown')
        logger.info(f"Validating analysis for: {app_name}")

        # 1. Check required fields
        field_errors = self._check_required_fields(analysis)
        errors.extend(field_errors)

        # 2. Validate scores
        score_errors, score_warnings = self._validate_scores(analysis)
        errors.extend(score_errors)
        warnings.extend(score_warnings)

        # 3. Check categories
        cat_errors, cat_warnings = self._validate_categories(analysis)
        errors.extend(cat_errors)
        warnings.extend(cat_warnings)

        # 4. Validate red flags
        rf_errors, rf_warnings = self._validate_red_flags(analysis)
        errors.extend(rf_errors)
        warnings.extend(rf_warnings)

        # 5. Check consistency (if requested and no critical errors)
        if check_consistency and not errors:
            cons_warnings = self._check_consistency(analysis)
            warnings.extend(cons_warnings)

        # 6. Validate metadata
        meta_warnings = self._validate_metadata(analysis)
        warnings.extend(meta_warnings)

        # 7. Check completeness
        comp_info = self._check_completeness(analysis)
        info.extend(comp_info)

        # Determine if valid
        is_valid = len(errors) == 0
        if self.strict_mode:
            is_valid = is_valid and len(warnings) == 0

        result = {
            'app_name': app_name,
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'info': info,
            'validation_timestamp': datetime.now().isoformat()
        }

        self.validation_results.append(result)
        return result

    def _check_required_fields(self, analysis: Dict) -> List[str]:
        """Check if all required fields are present with correct types"""
        errors = []

        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in analysis:
                errors.append(f"Missing required field: '{field}'")
                continue

            value = analysis[field]
            if value is None:
                errors.append(f"Field '{field}' is None")
                continue

            # Check type (handle multiple allowed types)
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' has incorrect type. "
                        f"Expected {expected_type}, got {type(value)}"
                    )
            else:
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' has incorrect type. "
                        f"Expected {expected_type}, got {type(value)}"
                    )

        return errors

    def _validate_scores(self, analysis: Dict) -> Tuple[List[str], List[str]]:
        """Validate that scores are in valid ranges"""
        errors = []
        warnings = []

        # Check main scores
        score_fields = [
            'overall_risk_score',
            'overall_transparency_score',
            'confidence_score'
        ]

        for field in score_fields:
            if field in analysis:
                score = analysis[field]
                if not isinstance(score, (int, float)):
                    errors.append(f"{field} must be numeric")
                elif score < self.SCORE_MIN or score > self.SCORE_MAX:
                    errors.append(
                        f"{field} ({score}) out of valid range "
                        f"[{self.SCORE_MIN}, {self.SCORE_MAX}]"
                    )
                elif score < 0:
                    errors.append(f"{field} cannot be negative")

        # Check confidence score specifically
        if 'confidence_score' in analysis:
            conf = analysis['confidence_score']
            if isinstance(conf, (int, float)):
                if conf < 50:
                    warnings.append(
                        f"Low confidence score ({conf}). "
                        "Analysis may be unreliable."
                    )

        return errors, warnings

    def _validate_categories(self, analysis: Dict) -> Tuple[List[str], List[str]]:
        """Validate category structure and scores"""
        errors = []
        warnings = []

        if 'categories' not in analysis:
            return errors, warnings

        categories = analysis['categories']

        if not isinstance(categories, dict):
            errors.append("'categories' must be a dictionary")
            return errors, warnings

        if len(categories) == 0:
            warnings.append("No categories found in analysis")

        for cat_name, cat_data in categories.items():
            # Check required fields
            for field, expected_type in self.REQUIRED_CATEGORY_FIELDS.items():
                if field not in cat_data:
                    errors.append(
                        f"Category '{cat_name}' missing field '{field}'"
                    )
                    continue

                value = cat_data[field]
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        errors.append(
                            f"Category '{cat_name}' field '{field}' has "
                            f"incorrect type"
                        )
                else:
                    if not isinstance(value, expected_type):
                        errors.append(
                            f"Category '{cat_name}' field '{field}' has "
                            f"incorrect type"
                        )

            # Validate score
            if 'score' in cat_data:
                score = cat_data['score']
                if isinstance(score, (int, float)):
                    if score < self.SCORE_MIN or score > self.SCORE_MAX:
                        errors.append(
                            f"Category '{cat_name}' score ({score}) out of "
                            f"valid range"
                        )

            # Check for empty findings
            if 'key_findings' in cat_data:
                findings = cat_data['key_findings']
                if isinstance(findings, list) and len(findings) == 0:
                    warnings.append(
                        f"Category '{cat_name}' has no key findings"
                    )

        return errors, warnings

    def _validate_red_flags(self, analysis: Dict) -> Tuple[List[str], List[str]]:
        """Validate red flag structure and content"""
        errors = []
        warnings = []

        if 'red_flags' not in analysis:
            return errors, warnings

        red_flags = analysis['red_flags']

        if not isinstance(red_flags, list):
            errors.append("'red_flags' must be a list")
            return errors, warnings

        if len(red_flags) == 0:
            warnings.append("No red flags identified (unusual for healthcare apps)")

        for i, flag in enumerate(red_flags):
            if not isinstance(flag, dict):
                errors.append(f"Red flag {i} is not a dictionary")
                continue

            # Check required fields
            for field in self.REQUIRED_RED_FLAG_FIELDS:
                if field not in flag:
                    errors.append(
                        f"Red flag {i} missing required field '{field}'"
                    )

            # Validate severity
            if 'severity' in flag:
                severity = flag['severity'].lower()
                if severity not in self.VALID_SEVERITIES:
                    errors.append(
                        f"Red flag {i} has invalid severity '{flag['severity']}'. "
                        f"Must be one of: {self.VALID_SEVERITIES}"
                    )

            # Check for empty quotes
            if 'quote' in flag:
                quote = flag['quote']
                if not quote or (isinstance(quote, str) and len(quote.strip()) == 0):
                    warnings.append(f"Red flag {i} has empty quote")

        # Check severity distribution
        if len(red_flags) > 0:
            severities = [rf.get('severity', '').lower() for rf in red_flags]
            critical_count = severities.count('critical')

            if critical_count > 5:
                warnings.append(
                    f"High number of critical red flags ({critical_count}). "
                    "Verify severity assessment."
                )

        return errors, warnings

    def _check_consistency(self, analysis: Dict) -> List[str]:
        """Check consistency between overall and category scores"""
        warnings = []

        if 'categories' not in analysis:
            return warnings

        # Calculate average of category scores
        category_scores = []
        for cat_data in analysis['categories'].values():
            if 'score' in cat_data and isinstance(cat_data['score'], (int, float)):
                category_scores.append(cat_data['score'])

        if not category_scores:
            warnings.append("No valid category scores found for consistency check")
            return warnings

        avg_category_score = np.mean(category_scores)

        # Check against overall_risk_score
        if 'overall_risk_score' in analysis:
            overall_risk = analysis['overall_risk_score']

            # Overall risk should be inversely related to category scores
            # (high scores = low risk)
            expected_risk = 100 - avg_category_score
            diff = abs(overall_risk - expected_risk)

            if diff > self.CONSISTENCY_TOLERANCE:
                warnings.append(
                    f"Inconsistency detected: overall_risk_score ({overall_risk}) "
                    f"differs significantly from category average "
                    f"(expected ~{expected_risk:.1f}, diff={diff:.1f})"
                )

        # Check against overall_transparency_score
        if 'overall_transparency_score' in analysis:
            overall_transp = analysis['overall_transparency_score']
            diff = abs(overall_transp - avg_category_score)

            if diff > self.CONSISTENCY_TOLERANCE:
                warnings.append(
                    f"Inconsistency detected: overall_transparency_score "
                    f"({overall_transp}) differs from category average "
                    f"({avg_category_score:.1f}, diff={diff:.1f})"
                )

        return warnings

    def _validate_metadata(self, analysis: Dict) -> List[str]:
        """Validate metadata completeness"""
        warnings = []

        if 'metadata' not in analysis:
            warnings.append("Missing metadata section")
            return warnings

        metadata = analysis['metadata']

        # Recommended metadata fields
        recommended_fields = [
            'model_used',
            'analysis_depth',
            'policy_length',
            'processing_time',
            'token_count'
        ]

        missing_fields = [f for f in recommended_fields if f not in metadata]
        if missing_fields:
            warnings.append(
                f"Metadata missing recommended fields: {', '.join(missing_fields)}"
            )

        return warnings

    def _check_completeness(self, analysis: Dict) -> List[str]:
        """Check analysis completeness and provide info"""
        info = []

        # Count various elements
        if 'categories' in analysis:
            num_categories = len(analysis['categories'])
            info.append(f"Categories analyzed: {num_categories}")

        if 'red_flags' in analysis:
            num_red_flags = len(analysis['red_flags'])
            info.append(f"Red flags identified: {num_red_flags}")

        if 'positive_practices' in analysis:
            num_positive = len(analysis['positive_practices'])
            info.append(f"Positive practices identified: {num_positive}")

        if 'missing_information' in analysis:
            num_missing = len(analysis['missing_information'])
            if num_missing > 0:
                info.append(f"Missing information items: {num_missing}")

        return info

    def validate_batch(self, analyses: List[Dict],
                      detect_anomalies: bool = True) -> Dict:
        """
        Validate multiple analyses and detect anomalies

        Args:
            analyses: List of analysis dictionaries
            detect_anomalies: Whether to perform outlier detection

        Returns:
            Batch validation results with:
                - individual_results: List of validation results
                - summary: Overall statistics
                - anomalies: Detected outliers (if requested)
        """
        logger.info(f"Validating batch of {len(analyses)} analyses")

        individual_results = []

        # Validate each analysis
        for analysis in analyses:
            result = self.validate_single_analysis(analysis, check_consistency=True)
            individual_results.append(result)

        # Calculate summary statistics
        num_valid = sum(1 for r in individual_results if r['is_valid'])
        num_invalid = len(individual_results) - num_valid

        total_errors = sum(len(r['errors']) for r in individual_results)
        total_warnings = sum(len(r['warnings']) for r in individual_results)

        summary = {
            'total_analyses': len(analyses),
            'valid_analyses': num_valid,
            'invalid_analyses': num_invalid,
            'validation_rate': (num_valid / len(analyses) * 100) if analyses else 0,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'avg_errors_per_analysis': total_errors / len(analyses) if analyses else 0,
            'avg_warnings_per_analysis': total_warnings / len(analyses) if analyses else 0
        }

        result = {
            'individual_results': individual_results,
            'summary': summary,
            'validation_timestamp': datetime.now().isoformat()
        }

        # Detect anomalies if requested
        if detect_anomalies and num_valid > 0:
            anomalies = self._detect_anomalies(analyses)
            result['anomalies'] = anomalies

        return result

    def _detect_anomalies(self, analyses: List[Dict]) -> Dict:
        """
        Detect statistical anomalies in batch of analyses

        Uses z-score method to identify outliers in key metrics
        """
        logger.info("Detecting anomalies in batch")

        anomalies = {
            'overall_risk_score': [],
            'overall_transparency_score': [],
            'confidence_score': [],
            'red_flag_count': [],
            'category_scores': {}
        }

        # Extract scores
        risk_scores = []
        transp_scores = []
        conf_scores = []
        rf_counts = []
        app_names = []

        for analysis in analyses:
            app_names.append(analysis.get('app_name', 'Unknown'))

            if 'overall_risk_score' in analysis:
                risk_scores.append(analysis['overall_risk_score'])
            else:
                risk_scores.append(None)

            if 'overall_transparency_score' in analysis:
                transp_scores.append(analysis['overall_transparency_score'])
            else:
                transp_scores.append(None)

            if 'confidence_score' in analysis:
                conf_scores.append(analysis['confidence_score'])
            else:
                conf_scores.append(None)

            if 'red_flags' in analysis:
                rf_counts.append(len(analysis['red_flags']))
            else:
                rf_counts.append(0)

        # Detect outliers for each metric
        anomalies['overall_risk_score'] = self._find_outliers(
            risk_scores, app_names, 'overall_risk_score'
        )

        anomalies['overall_transparency_score'] = self._find_outliers(
            transp_scores, app_names, 'overall_transparency_score'
        )

        anomalies['confidence_score'] = self._find_outliers(
            conf_scores, app_names, 'confidence_score'
        )

        anomalies['red_flag_count'] = self._find_outliers(
            rf_counts, app_names, 'red_flag_count'
        )

        # Detect anomalies in category scores
        category_names = set()
        for analysis in analyses:
            if 'categories' in analysis:
                category_names.update(analysis['categories'].keys())

        for cat_name in category_names:
            cat_scores = []
            for analysis in analyses:
                if 'categories' in analysis and cat_name in analysis['categories']:
                    score = analysis['categories'][cat_name].get('score')
                    cat_scores.append(score)
                else:
                    cat_scores.append(None)

            outliers = self._find_outliers(cat_scores, app_names, cat_name)
            if outliers:
                anomalies['category_scores'][cat_name] = outliers

        return anomalies

    def _find_outliers(self, values: List[Optional[float]],
                      labels: List[str],
                      metric_name: str) -> List[Dict]:
        """
        Find outliers using z-score method

        Returns list of outlier dictionaries with app name, value, z-score
        """
        # Filter out None values
        valid_pairs = [(v, l) for v, l in zip(values, labels) if v is not None]

        if len(valid_pairs) < 3:
            return []  # Need at least 3 values for meaningful statistics

        valid_values = [v for v, _ in valid_pairs]
        valid_labels = [l for _, l in valid_pairs]

        # Calculate z-scores
        z_scores = np.abs(stats.zscore(valid_values))

        # Find outliers
        outliers = []
        for value, label, z_score in zip(valid_values, valid_labels, z_scores):
            if z_score > self.OUTLIER_THRESHOLD:
                outliers.append({
                    'app_name': label,
                    'metric': metric_name,
                    'value': float(value),
                    'z_score': float(z_score),
                    'deviation': 'high' if value > np.mean(valid_values) else 'low'
                })

        return outliers

    def generate_validation_report(self, batch_results: Dict,
                                  output_path: Optional[str] = None) -> str:
        """
        Generate human-readable validation report

        Args:
            batch_results: Results from validate_batch()
            output_path: Optional path to save report

        Returns:
            Report as string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("PRIVACY POLICY ANALYSIS - QUALITY VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Generated: {batch_results['validation_timestamp']}")
        lines.append("")

        # Summary
        summary = batch_results['summary']
        lines.append("VALIDATION SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Analyses:        {summary['total_analyses']}")
        lines.append(f"Valid Analyses:        {summary['valid_analyses']}")
        lines.append(f"Invalid Analyses:      {summary['invalid_analyses']}")
        lines.append(f"Validation Rate:       {summary['validation_rate']:.1f}%")
        lines.append(f"Total Errors:          {summary['total_errors']}")
        lines.append(f"Total Warnings:        {summary['total_warnings']}")
        lines.append(f"Avg Errors/Analysis:   {summary['avg_errors_per_analysis']:.2f}")
        lines.append(f"Avg Warnings/Analysis: {summary['avg_warnings_per_analysis']:.2f}")
        lines.append("")

        # Individual results
        lines.append("INDIVIDUAL VALIDATION RESULTS")
        lines.append("-" * 80)

        for result in batch_results['individual_results']:
            app_name = result['app_name']
            status = "✓ PASS" if result['is_valid'] else "✗ FAIL"

            lines.append(f"\n{app_name}: {status}")

            if result['errors']:
                lines.append(f"  Errors ({len(result['errors'])}):")
                for error in result['errors']:
                    lines.append(f"    - {error}")

            if result['warnings']:
                lines.append(f"  Warnings ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    lines.append(f"    - {warning}")

            if result['info']:
                lines.append(f"  Info:")
                for info in result['info']:
                    lines.append(f"    - {info}")

        # Anomalies
        if 'anomalies' in batch_results:
            lines.append("\n")
            lines.append("ANOMALY DETECTION")
            lines.append("-" * 80)

            anomalies = batch_results['anomalies']
            total_anomalies = 0

            for metric, outliers in anomalies.items():
                if metric == 'category_scores':
                    for cat_name, cat_outliers in outliers.items():
                        if cat_outliers:
                            total_anomalies += len(cat_outliers)
                            lines.append(f"\n{cat_name} (Category):")
                            for outlier in cat_outliers:
                                lines.append(
                                    f"  - {outlier['app_name']}: "
                                    f"{outlier['value']:.1f} "
                                    f"(z-score: {outlier['z_score']:.2f}, "
                                    f"{outlier['deviation']} deviation)"
                                )
                elif outliers:
                    total_anomalies += len(outliers)
                    lines.append(f"\n{metric}:")
                    for outlier in outliers:
                        lines.append(
                            f"  - {outlier['app_name']}: "
                            f"{outlier['value']:.1f} "
                            f"(z-score: {outlier['z_score']:.2f}, "
                            f"{outlier['deviation']} deviation)"
                        )

            if total_anomalies == 0:
                lines.append("\nNo statistical anomalies detected.")

        lines.append("\n")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        report = "\n".join(lines)

        # Save if path provided
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Validation report saved to: {output_path}")

        return report


def load_and_validate_directory(directory: str,
                               strict_mode: bool = False,
                               output_report: Optional[str] = None) -> Dict:
    """
    Convenience function to load and validate all analyses in a directory

    Args:
        directory: Path to directory containing JSON analysis files
        strict_mode: If True, treat warnings as errors
        output_report: Optional path to save validation report

    Returns:
        Batch validation results
    """
    logger.info(f"Loading analyses from: {directory}")

    # Load all JSON files
    analyses = []
    json_files = list(Path(directory).glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
                analyses.append(analysis)
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")

    if not analyses:
        logger.warning(f"No valid JSON files found in {directory}")
        return {
            'individual_results': [],
            'summary': {
                'total_analyses': 0,
                'valid_analyses': 0,
                'invalid_analyses': 0,
                'validation_rate': 0,
                'total_errors': 0,
                'total_warnings': 0
            }
        }

    # Validate
    validator = AnalysisValidator(strict_mode=strict_mode)
    results = validator.validate_batch(analyses, detect_anomalies=True)

    # Generate report
    report = validator.generate_validation_report(results, output_path=output_report)

    return results


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python validator.py <directory> [--strict] [--report <path>]")
        sys.exit(1)

    directory = sys.argv[1]
    strict_mode = '--strict' in sys.argv

    report_path = None
    if '--report' in sys.argv:
        idx = sys.argv.index('--report')
        if idx + 1 < len(sys.argv):
            report_path = sys.argv[idx + 1]

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run validation
    results = load_and_validate_directory(
        directory,
        strict_mode=strict_mode,
        output_report=report_path
    )

    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Total Analyses:   {results['summary']['total_analyses']}")
    print(f"Valid:            {results['summary']['valid_analyses']}")
    print(f"Invalid:          {results['summary']['invalid_analyses']}")
    print(f"Validation Rate:  {results['summary']['validation_rate']:.1f}%")

    if results['summary']['invalid_analyses'] > 0:
        print("\n⚠ Some analyses failed validation. See report for details.")
        sys.exit(1)
    else:
        print("\n✓ All analyses passed validation.")
        sys.exit(0)
