# Getting Started with Privacy Policy Analyzer

This guide will help you get up and running with the Privacy Policy Analyzer for Healthcare Apps.

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your API key:

```bash
# Copy the example
cp .env.example .env

# Add your API key (choose one)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run Your First Analysis

```bash
python main.py --url https://www.example.com/privacy --name "Example App"
```

## Step-by-Step Tutorial

### Analyzing a Single Privacy Policy

1. **Find the privacy policy URL** of a healthcare app
2. **Run the analyzer**:

```bash
python main.py --url https://healthcare-app.com/privacy --name "HealthApp"
```

3. **Check the outputs**:
   - HTML report in `outputs/reports/`
   - Visualizations in `outputs/visualizations/`
   - Raw data in `data/raw/`

### Analyzing Multiple Policies

1. **Edit `config/config.yaml`** and add your targets:

```yaml
targets:
  - name: "Telehealth App"
    url: "https://telehealth.com/privacy"
    category: "telehealth"

  - name: "Fitness Tracker"
    url: "https://fitness.com/privacy-policy"
    category: "health_tracker"
```

2. **Run batch analysis**:

```bash
python main.py --analyze-all
```

3. **Review the comparison report** in `outputs/reports/`

### Using Selenium for Dynamic Content

Some websites load content dynamically with JavaScript. Use the `--selenium` flag:

```bash
python main.py --url https://dynamic-site.com/privacy --name "Dynamic App" --selenium
```

## Understanding the Output

### Risk Score

The analyzer generates a risk score from 0.00 to 1.00:

- **0.00 - 0.30**: LOW risk
- **0.30 - 0.60**: MEDIUM risk
- **0.60 - 0.80**: HIGH risk
- **0.80 - 1.00**: CRITICAL risk

### Categories Analyzed

Each policy is analyzed across 8 categories:

1. **Data Collection**: What data is collected
2. **Data Usage**: How data is used
3. **Third-Party Sharing**: Who else gets access
4. **Data Retention**: How long data is kept
5. **User Rights**: What control users have
6. **Security Measures**: How data is protected
7. **Healthcare Compliance**: HIPAA and health regulations
8. **International Transfers**: Cross-border data movement

### Red Flags

Red flags are specific concerning practices identified in the policy:

- Data sharing with advertisers
- Indefinite retention
- Missing HIPAA compliance
- Vague consent mechanisms
- And more...

## Customization

### Changing the LLM Provider

Edit `config/config.yaml`:

```yaml
llm:
  provider: "anthropic"  # Changed from "openai"
  model: "claude-3-opus-20240229"
```

### Adjusting Category Weights

Make certain categories more important in the overall score:

```yaml
scoring:
  weights:
    third_party_sharing: 0.30  # Increased from 0.20
    healthcare_compliance: 0.15  # Increased from 0.10
```

### Adding Custom Red Flags

```yaml
analysis:
  red_flags:
    - "sells user data"
    - "shares with insurance"
    - "your custom flag here"
```

## Troubleshooting

### "No API key found" Error

Make sure you've created `.env` file and added your API key:

```bash
# Check if .env exists
ls -la .env

# Verify it contains your key
cat .env
```

### Scraping Fails

Try these solutions:

1. Use Selenium: `--selenium` flag
2. Check if URL is accessible in browser
3. Verify the website allows automated access
4. Check internet connection

### Out of Memory

For very large policies:

1. Reduce `max_tokens` in config
2. Use a lighter model (e.g., gpt-3.5-turbo)
3. Increase system memory

## Best Practices

1. **Start with one policy** to understand the output
2. **Review the HTML report** for detailed insights
3. **Use comparison reports** to evaluate multiple apps
4. **Customize weights** based on your research focus
5. **Save raw data** for reproducibility
6. **Check logs** if something goes wrong

## Next Steps

- Review the full [README.md](../README.md) for detailed documentation
- Explore example configurations in `config/`
- Run tests with `pytest tests/`
- Contribute improvements!

## Example Workflows

### Research Workflow

```bash
# 1. Analyze all target apps
python main.py --analyze-all

# 2. Review comparison report
# Opens in browser: outputs/reports/comparison_report_*.html

# 3. Deep dive into specific app
python main.py --url https://concerning-app.com/privacy --name "App Name"

# 4. Export data for further analysis
# JSON files available in outputs/reports/
```

### Privacy Audit Workflow

```bash
# 1. Analyze app with Selenium for accuracy
python main.py --url https://app.com/privacy --name "App" --selenium

# 2. Review red flags in HTML report
# Check outputs/reports/*_report_*.html

# 3. Document findings
# HTML reports can be shared with stakeholders

# 4. Compare with competitors
# Add competitors to config.yaml and run --analyze-all
```

## Support

If you encounter issues:

1. Check `logs/analyzer.log` for detailed error messages
2. Review common issues in README.md
3. Verify your configuration in `config/config.yaml`
4. Ensure dependencies are installed correctly

Happy analyzing!
