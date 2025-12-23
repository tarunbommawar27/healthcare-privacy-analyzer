# Quality Validation Guide

## Overview

The **Quality Validation System** (`src/utils/validator.py`) ensures that privacy policy analyses meet research-grade quality standards through comprehensive validation, consistency checks, and anomaly detection.

## Table of Contents

1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Validation Checks](#validation-checks)
4. [Usage Examples](#usage-examples)
5. [Integration with Workflow](#integration-with-workflow)
6. [Interpreting Results](#interpreting-results)
7. [Best Practices](#best-practices)
8. [API Reference](#api-reference)

---

## Features

### 1. **Completeness Validation**
- ✓ All required fields present
- ✓ Correct data types
- ✓ Non-null values
- ✓ Minimum content requirements

### 2. **Score Validation**
- ✓ All scores in valid range (0-100)
- ✓ No negative values
- ✓ Numeric types only
- ✓ Category scores present

### 3. **Consistency Checks**
- ✓ Overall score aligns with category averages
- ✓ Risk score inversely related to transparency
- ✓ Confidence score reasonableness

### 4. **Red Flag Validation**
- ✓ Proper structure (finding, severity, quote, category)
- ✓ Valid severity levels (critical, high, medium, low)
- ✓ Non-empty quotes
- ✓ Severity distribution analysis

### 5. **Anomaly Detection**
- ✓ Statistical outlier identification (z-scores)
- ✓ Identifies unusually high/low scores
- ✓ Detects abnormal red flag counts
- ✓ Per-category anomaly detection

### 6. **Metadata Validation**
- ✓ Recommended metadata fields present
- ✓ Model information tracking
- ✓ Processing metadata

### 7. **Reporting**
- ✓ Human-readable text reports
- ✓ Machine-readable JSON outputs
- ✓ Detailed error/warning messages
- ✓ Summary statistics

---

## Quick Start

### Command Line Usage

```bash
# Validate all analyses in a directory
python -m src.utils.validator outputs/reports/

# Strict mode (warnings = errors)
python -m src.utils.validator outputs/reports/ --strict

# Save report to custom location
python -m src.utils.validator outputs/reports/ --report validation_report.txt
```

### Python API Usage

```python
from src.utils.validator import AnalysisValidator, load_and_validate_directory

# Method 1: Convenience function
results = load_and_validate_directory(
    directory='outputs/reports/',
    strict_mode=False,
    output_report='validation_report.txt'
)

# Method 2: Manual validation
validator = AnalysisValidator(strict_mode=False)

# Validate single analysis
with open('analysis.json', 'r') as f:
    analysis = json.load(f)
result = validator.validate_single_analysis(analysis)

# Validate batch
analyses = [...]  # List of analysis dicts
batch_results = validator.validate_batch(analyses, detect_anomalies=True)

# Generate report
report = validator.generate_validation_report(batch_results, 'report.txt')
```

---

## Validation Checks

### Required Fields

The validator checks for the presence and correct types of these fields:

```python
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
```

### Category Structure

Each category must have:

```python
REQUIRED_CATEGORY_FIELDS = {
    'score': (int, float),
    'explanation': str,
    'key_findings': list
}
```

**Example:**
```json
{
  "Data Collection": {
    "score": 65,
    "explanation": "Collects extensive health information including...",
    "key_findings": [
      "Tracks daily health metrics",
      "Records medication adherence"
    ]
  }
}
```

### Red Flag Structure

Each red flag must have:

```python
REQUIRED_RED_FLAG_FIELDS = {
    'finding': str,
    'severity': str,  # Must be: critical, high, medium, or low
    'quote': str,
    'category': str
}
```

**Example:**
```json
{
  "finding": "Shares health data with advertisers",
  "severity": "critical",
  "quote": "We may share your personal health information with our advertising partners...",
  "category": "Data Sharing"
}
```

### Score Ranges

- **All scores:** 0-100
- **No negative values**
- **Must be numeric** (int or float)

### Consistency Tolerance

The validator allows **±15 percentage points** between:
- Overall risk score vs. category average (inversely)
- Overall transparency score vs. category average

Differences exceeding this threshold trigger warnings.

### Outlier Detection

Uses **z-score method** with threshold of **3.0**:
- Scores with |z-score| > 3.0 are flagged as outliers
- Requires minimum 3 analyses for meaningful statistics
- Detects both high and low deviations

---

## Usage Examples

### Example 1: Validate Single Analysis

```python
from src.utils.validator import AnalysisValidator
import json

# Load analysis
with open('outputs/reports/myapp_analysis.json', 'r') as f:
    analysis = json.load(f)

# Create validator
validator = AnalysisValidator(strict_mode=False)

# Validate
result = validator.validate_single_analysis(analysis)

# Check results
if result['is_valid']:
    print(f"✓ {result['app_name']} passed validation")
else:
    print(f"✗ {result['app_name']} failed validation")
    for error in result['errors']:
        print(f"  Error: {error}")
```

### Example 2: Batch Validation with Anomaly Detection

```python
from src.utils.validator import AnalysisValidator
from pathlib import Path
import json

# Load all analyses
analyses = []
for json_file in Path('outputs/reports/').glob('*.json'):
    with open(json_file, 'r') as f:
        analyses.append(json.load(f))

# Validate
validator = AnalysisValidator()
results = validator.validate_batch(analyses, detect_anomalies=True)

# Display summary
summary = results['summary']
print(f"Valid: {summary['valid_analyses']}/{summary['total_analyses']}")
print(f"Validation rate: {summary['validation_rate']:.1f}%")

# Check anomalies
if 'anomalies' in results:
    for metric, outliers in results['anomalies'].items():
        if outliers and metric != 'category_scores':
            print(f"\n{metric} outliers:")
            for outlier in outliers:
                print(f"  - {outlier['app_name']}: {outlier['value']:.1f}")
```

### Example 3: Generate Validation Report

```python
from src.utils.validator import load_and_validate_directory

# Validate and generate report
results = load_and_validate_directory(
    directory='outputs/reports/',
    strict_mode=False,
    output_report='validation_report.txt'
)

# Report is automatically saved
print(f"Report saved with {results['summary']['total_analyses']} analyses")
```

### Example 4: Strict Mode

```python
from src.utils.validator import AnalysisValidator

# Strict mode: warnings treated as errors
validator = AnalysisValidator(strict_mode=True)

result = validator.validate_single_analysis(analysis)

# In strict mode, warnings will cause is_valid = False
if not result['is_valid']:
    print("Failed strict validation:")
    print(f"  Errors: {len(result['errors'])}")
    print(f"  Warnings: {len(result['warnings'])}")  # These count as failures
```

---

## Integration with Workflow

The validator is **automatically integrated** with the `ResearchWorkflow` class.

### Automatic Validation

```python
from src.modules.research_workflow import ResearchWorkflow

workflow = ResearchWorkflow(
    input_csv='data/apps.csv',
    output_dir='research_output/'
)

# Validation is enabled by default
results = workflow.run_complete_workflow(
    validate=True,              # Enable validation (default)
    strict_validation=False     # Lenient mode (default)
)

# Check outputs
if results['status'] == 'success':
    print(f"Validation report: {results['validation_report']}")
    print(f"Validation JSON: {results['validation_results']}")
```

### Manual Validation in Workflow

```python
# Run workflow without automatic validation
results = workflow.run_complete_workflow(validate=False)

# Then validate separately
validation_results = workflow.validate_analyses(
    strict_mode=False,
    save_report=True
)

# Check validation
if validation_results['summary']['invalid_analyses'] > 0:
    print("Some analyses failed validation")
```

### Strict Mode in Workflow

```python
# Use strict validation (abort on any warnings)
results = workflow.run_complete_workflow(
    validate=True,
    strict_validation=True
)

if results['status'] == 'failed':
    print(f"Workflow aborted: {results['reason']}")
    # Review validation results
    val_results = results['validation_results']
```

---

## Interpreting Results

### Validation Result Structure

```python
{
    'app_name': 'MyApp',
    'is_valid': True,
    'errors': [],           # Critical issues that prevent use
    'warnings': [],         # Non-critical issues to review
    'info': [],            # Informational messages
    'validation_timestamp': '2025-01-15T10:30:00'
}
```

### Batch Validation Result Structure

```python
{
    'individual_results': [
        # List of individual validation results
    ],
    'summary': {
        'total_analyses': 10,
        'valid_analyses': 8,
        'invalid_analyses': 2,
        'validation_rate': 80.0,
        'total_errors': 5,
        'total_warnings': 12,
        'avg_errors_per_analysis': 0.5,
        'avg_warnings_per_analysis': 1.2
    },
    'anomalies': {
        'overall_risk_score': [
            {
                'app_name': 'OutlierApp',
                'metric': 'overall_risk_score',
                'value': 95.0,
                'z_score': 3.5,
                'deviation': 'high'
            }
        ],
        'category_scores': {
            'Data Collection': [...]
        }
    },
    'validation_timestamp': '2025-01-15T10:30:00'
}
```

### Error Types

**Critical Errors** (prevent using analysis):
- Missing required fields
- Incorrect data types
- Scores out of range (< 0 or > 100)
- Invalid red flag severity levels
- Malformed category structure

**Warnings** (review recommended):
- Low confidence score (< 50)
- Inconsistent overall vs. category scores (> ±15 points)
- Empty key findings lists
- Empty red flag quotes
- Unusually high number of critical red flags (> 5)
- Missing recommended metadata fields

### Anomaly Interpretation

**Z-score interpretation:**
- |z| > 3.0: Strong outlier (flagged)
- |z| > 2.0: Moderate outlier (review)
- |z| < 2.0: Normal variation

**High deviation:** Value significantly above average
**Low deviation:** Value significantly below average

**Example:**
```
App: HealthTracker
Metric: overall_risk_score
Value: 92.0
Z-score: 3.2
Deviation: high

→ This app has unusually high risk compared to peers
→ Review analysis for accuracy
```

---

## Best Practices

### 1. **Use Validation Early and Often**

```python
# Validate immediately after analysis
analysis = analyzer.analyze_policy(text)
result = validator.validate_single_analysis(analysis)

if not result['is_valid']:
    logger.error(f"Analysis failed validation: {result['errors']}")
    # Fix issues or re-run analysis
```

### 2. **Choose Appropriate Mode**

**Normal Mode (default):**
- Research workflows
- Iterative analysis
- Allows minor issues

**Strict Mode:**
- Publication-ready data
- Final datasets
- Zero tolerance for issues

### 3. **Review Anomalies**

```python
# Always review detected anomalies
for outlier in anomalies['overall_risk_score']:
    if outlier['z_score'] > 3.5:
        # Very unusual - verify analysis
        logger.warning(f"Review {outlier['app_name']}")
```

### 4. **Track Validation Metrics Over Time**

```python
# Save validation results for trend analysis
validation_history = []

for batch in batches:
    results = validator.validate_batch(batch)
    validation_history.append({
        'date': datetime.now(),
        'rate': results['summary']['validation_rate']
    })

# Monitor improvement
avg_rate = np.mean([h['rate'] for h in validation_history])
```

### 5. **Customize Thresholds (Advanced)**

```python
# Adjust validator parameters
validator = AnalysisValidator()

# More lenient consistency tolerance
validator.CONSISTENCY_TOLERANCE = 20  # Default: 15

# More sensitive outlier detection
validator.OUTLIER_THRESHOLD = 2.5  # Default: 3.0
```

---

## API Reference

### `AnalysisValidator`

**Constructor:**
```python
AnalysisValidator(strict_mode: bool = False)
```

**Methods:**

#### `validate_single_analysis()`
```python
validate_single_analysis(
    analysis: Dict,
    check_consistency: bool = True
) -> Dict
```

Validates a single analysis result.

**Returns:**
```python
{
    'app_name': str,
    'is_valid': bool,
    'errors': List[str],
    'warnings': List[str],
    'info': List[str],
    'validation_timestamp': str
}
```

#### `validate_batch()`
```python
validate_batch(
    analyses: List[Dict],
    detect_anomalies: bool = True
) -> Dict
```

Validates multiple analyses with anomaly detection.

**Returns:**
```python
{
    'individual_results': List[Dict],
    'summary': Dict,
    'anomalies': Dict,
    'validation_timestamp': str
}
```

#### `generate_validation_report()`
```python
generate_validation_report(
    batch_results: Dict,
    output_path: Optional[str] = None
) -> str
```

Generates human-readable validation report.

**Returns:** Report as string, optionally saves to file

---

### Convenience Functions

#### `load_and_validate_directory()`
```python
load_and_validate_directory(
    directory: str,
    strict_mode: bool = False,
    output_report: Optional[str] = None
) -> Dict
```

Loads all JSON files from directory and validates them.

**Example:**
```python
results = load_and_validate_directory(
    directory='outputs/reports/',
    strict_mode=False,
    output_report='validation.txt'
)
```

---

## Troubleshooting

### Issue: High number of consistency warnings

**Cause:** Overall scores don't align with category averages

**Solution:**
1. Check LLM prompt - ensure it calculates overall scores correctly
2. Review individual analyses for accuracy
3. Adjust `CONSISTENCY_TOLERANCE` if legitimately different

### Issue: Many empty key findings warnings

**Cause:** Categories have empty `key_findings` lists

**Solution:**
1. Improve LLM prompts to extract more findings
2. Use deeper analysis mode
3. Review policy text for sufficient detail

### Issue: Anomalies detected in all analyses

**Cause:** Small sample size or high variance

**Solution:**
1. Need at least 10-15 analyses for robust anomaly detection
2. Review if apps are truly diverse (different privacy practices)
3. Consider domain-specific thresholds

### Issue: Validation fails on all analyses

**Cause:** Structural issue in analysis output

**Solution:**
1. Check LLM output schema matches expected format
2. Review `analyzer.py` output structure
3. Validate JSON schema compliance

---

## Advanced Usage

### Custom Validation Rules

```python
from src.utils.validator import AnalysisValidator

class CustomValidator(AnalysisValidator):
    """Extended validator with custom rules"""

    def validate_single_analysis(self, analysis, check_consistency=True):
        # Run standard validation
        result = super().validate_single_analysis(analysis, check_consistency)

        # Add custom checks
        if 'healthcare_specific_field' not in analysis.get('metadata', {}):
            result['warnings'].append("Missing healthcare-specific metadata")

        # Custom red flag severity check
        critical_flags = [
            rf for rf in analysis.get('red_flags', [])
            if rf.get('severity') == 'critical'
        ]
        if len(critical_flags) > 10:
            result['warnings'].append("Excessive critical flags - verify severity")

        return result

# Use custom validator
validator = CustomValidator()
```

### Parallel Validation

```python
from concurrent.futures import ThreadPoolExecutor
from src.utils.validator import AnalysisValidator

def validate_analysis(analysis_path):
    """Validate single analysis file"""
    with open(analysis_path, 'r') as f:
        analysis = json.load(f)

    validator = AnalysisValidator()
    return validator.validate_single_analysis(analysis)

# Validate in parallel
analysis_files = list(Path('outputs/reports/').glob('*.json'))

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(validate_analysis, analysis_files))

# Aggregate results
valid_count = sum(1 for r in results if r['is_valid'])
print(f"Valid: {valid_count}/{len(results)}")
```

---

## Summary

The Quality Validation System provides:

✓ **Comprehensive validation** of all analysis components
✓ **Statistical anomaly detection** for outlier identification
✓ **Flexible modes** (normal vs. strict) for different use cases
✓ **Detailed reporting** for debugging and quality assurance
✓ **Seamless integration** with research workflow
✓ **Programmatic API** for custom validation pipelines

**Use it to ensure research-grade data quality in all your privacy policy analyses!**

---

## Next Steps

1. **Run examples:** `python examples/validator_example.py`
2. **Validate your analyses:** `python -m src.utils.validator outputs/reports/`
3. **Integrate with workflow:** See [Integration with Workflow](#integration-with-workflow)
4. **Customize validation:** Extend `AnalysisValidator` for domain-specific checks

**For more information, see:**
- [Research Workflow Guide](RESEARCH_WORKFLOW.md)
- [Comparative Analysis Guide](COMPARATIVE_ANALYSIS_IMPLEMENTATION.md)
- [API Documentation](API_REFERENCE.md)
