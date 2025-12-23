# Quick Reference Guide

## Installation & Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Test installation
python main.py --help
```

## Common Commands

### Analyze Single Policy
```bash
python main.py --url <URL> --name "<App Name>"
```

### Analyze with Selenium
```bash
python main.py --url <URL> --name "<App Name>" --selenium
```

### Analyze Multiple Policies
```bash
python main.py --analyze-all
```

### Use Custom Config
```bash
python main.py --analyze-all --config path/to/config.yaml
```

## File Locations

| Type | Location |
|------|----------|
| Configuration | `config/config.yaml` |
| Environment Variables | `.env` |
| Raw Scraped Data | `data/raw/` |
| HTML Reports | `outputs/reports/*.html` |
| JSON Reports | `outputs/reports/*.json` |
| Visualizations | `outputs/visualizations/*.png` |
| Logs | `logs/analyzer.log` |

## Configuration Quick Reference

### Change LLM Provider

```yaml
# config/config.yaml
llm:
  provider: "openai"  # or "anthropic"
  model: "gpt-4-turbo-preview"  # or "claude-3-opus-20240229"
```

### Adjust Scoring Weights

```yaml
scoring:
  weights:
    data_collection: 0.15
    data_usage: 0.15
    third_party_sharing: 0.20
    data_retention: 0.15
    user_rights: 0.10
    security_measures: 0.15
    healthcare_compliance: 0.10
```

### Add Target Apps

```yaml
targets:
  - name: "App Name"
    url: "https://example.com/privacy"
    category: "telehealth"
```

## Risk Levels

| Score | Level | Color |
|-------|-------|-------|
| 0.00 - 0.30 | LOW | Green |
| 0.30 - 0.60 | MEDIUM | Yellow |
| 0.60 - 0.80 | HIGH | Orange |
| 0.80 - 1.00 | CRITICAL | Red |

## Analysis Categories

1. Data Collection
2. Data Usage
3. Third-Party Sharing
4. Data Retention
5. User Rights
6. Security Measures
7. Healthcare Compliance
8. International Transfers

## Common Red Flags

- Third-party data sharing/selling
- Advertising partnerships
- Indefinite data retention
- Lack of encryption
- Missing HIPAA compliance
- No opt-out options
- Vague consent mechanisms
- Cross-border transfers

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No API key found" | Check `.env` file exists and contains valid API key |
| Scraping fails | Try `--selenium` flag |
| Out of memory | Reduce `max_tokens` in config |
| Import errors | Run `pip install -r requirements.txt` |
| Selenium error | Install ChromeDriver: `pip install webdriver-manager` |

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_scraper.py
```

## Output Examples

### Terminal Output
```
======================================================================
Analyzing Privacy Policy for: Example Healthcare App
======================================================================

[1/4] Scraping privacy policy...
✓ Successfully scraped 15,234 characters

[2/4] Analyzing policy with LLM...
✓ Analysis complete

[3/4] Calculating risk scores...
✓ Risk Score: 0.72/1.00 (HIGH)
✓ Red Flags: 5

[4/4] Generating reports and visualizations...
✓ HTML report: outputs/reports/Example_Healthcare_App_report_20240115_143022.html
```

### HTML Report Structure
- Header (app name, URL, date)
- Risk Assessment (score, level, red flags)
- Executive Summary
- Visualizations
- Detailed Category Analysis
- Red Flags List
- Recommendations

## Environment Variables

```bash
# Required (choose one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
CHROME_DRIVER_PATH=/path/to/chromedriver
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=https://proxy:port
```

## Project Structure

```
Privacy Policy Analyzer/
├── main.py              # Entry point
├── config/
│   └── config.yaml      # Configuration
├── src/
│   ├── modules/         # Core modules
│   │   ├── scraper.py
│   │   ├── analyzer.py
│   │   ├── scorer.py
│   │   └── reporter.py
│   └── utils/           # Utilities
│       ├── logger.py
│       └── file_handler.py
├── data/                # Data storage
├── outputs/             # Generated reports
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Tips

1. **Start small**: Analyze one policy first
2. **Review HTML reports**: Most user-friendly format
3. **Customize weights**: Adjust based on research focus
4. **Use comparison reports**: Compare multiple apps
5. **Check logs**: `logs/analyzer.log` for debugging
6. **Save raw data**: Keep for reproducibility

## Links

- Full Documentation: [README.md](README.md)
- Getting Started: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
- API Reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
