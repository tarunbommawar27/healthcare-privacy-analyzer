# Quick Start Guide - Version 2.0

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+
- An API key from OpenAI or Anthropic (or both)

---

## Step 1: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

---

## Step 2: Configure API Keys (1 minute)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key(s)
# Option 1: Use Anthropic Claude Sonnet 4 (recommended)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 2: Use OpenAI GPT-4
OPENAI_API_KEY=sk-your-key-here

# Best: Add both for automatic fallback
```

**Get API Keys:**
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

---

## Step 3: Run Your First Analysis (3 minutes)

### Basic Analysis
```bash
python main.py \
  --url https://www.zocdoc.com/about/privacy/ \
  --name "Zocdoc"
```

### With Model Selection
```bash
python main.py \
  --url https://www.teladoc.com/privacy-policy/ \
  --name "Teladoc" \
  --model claude
```

### Deep Analysis for Research
```bash
python main.py \
  --url https://www.fitbit.com/global/us/legal/privacy-policy \
  --name "Fitbit" \
  --depth deep
```

---

## 🎯 Common Use Cases

### 1. Quick Screening (Fastest, Cheapest)
```bash
python main.py --url <URL> --name "<App>" --depth quick
```
- **Time**: ~30 seconds
- **Cost**: ~$0.01
- **Use for**: Initial screening, batch processing

### 2. Standard Analysis (Recommended)
```bash
python main.py --url <URL> --name "<App>" --model auto
```
- **Time**: ~1-2 minutes
- **Cost**: ~$0.03-0.05
- **Use for**: Most analyses, reports, general research

### 3. Deep Research Analysis (Most Detailed)
```bash
python main.py --url <URL> --name "<App>" --model claude --depth deep
```
- **Time**: ~2-4 minutes
- **Cost**: ~$0.10-0.15
- **Use for**: Academic papers, detailed audits, compliance reviews

### 4. Batch Analysis
```bash
# Add apps to config/config.yaml, then:
python main.py --analyze-all
```
- Analyzes all configured apps
- Generates comparison report
- Uses caching for efficiency

---

## 📊 Understanding the Output

### What You'll Get:

1. **Terminal Summary**
   - Overall risk score (0-100)
   - Transparency score
   - Red flags with severity levels
   - Category scores
   - Quotable research findings

2. **HTML Report** (`outputs/reports/`)
   - Beautiful interactive report
   - Embedded visualizations
   - Full analysis details
   - Shareable with stakeholders

3. **JSON Data** (`outputs/reports/`)
   - Machine-readable format
   - Complete analysis data
   - Ready for further processing

4. **Visualizations** (`outputs/visualizations/`)
   - Risk gauge chart
   - Category scores bar chart
   - High-resolution PNG images

---

## 🎨 CLI Cheat Sheet

### Model Selection
```bash
--model claude    # Use Claude Sonnet 4 (recommended for healthcare)
--model gpt4      # Use GPT-4 Turbo
--model auto      # Auto-select based on available keys
```

### Analysis Depth
```bash
--depth quick     # Fast, high-level (~30s, ~$0.01)
--depth standard  # Comprehensive (default) (~1-2min, ~$0.03)
--depth deep      # In-depth research (~2-4min, ~$0.10)
```

### Caching Options
```bash
--no-cache           # Disable caching for this run
--force-reanalyze    # Re-analyze even if cached
```

### Display Options
```bash
--show-cost          # Show cost estimate (default: ON)
--no-cost-estimate   # Hide cost estimate
```

### Scraping Options
```bash
--selenium           # Use Selenium for JavaScript-heavy pages
```

---

## 💰 Cost Guide

| Depth | Model | Avg Tokens | Avg Cost | Time |
|-------|-------|------------|----------|------|
| Quick | Claude | ~5K | $0.01 | 30s |
| Standard | Claude | ~10K | $0.03 | 1-2min |
| Deep | Claude | ~20K | $0.11 | 2-4min |
| Quick | GPT-4 | ~5K | $0.05 | 30s |
| Standard | GPT-4 | ~10K | $0.15 | 1-2min |
| Deep | GPT-4 | ~20K | $0.30 | 2-4min |

**💡 Tip**: Use Claude for best value on healthcare analysis!

---

## 🔍 What Gets Analyzed

### 8 Categories:
1. **Data Collection** - What data is collected
2. **Data Usage** - How data is used
3. **Third-Party Sharing** - Who gets access
4. **Data Retention** - How long data is kept
5. **User Rights** - Access, deletion, portability
6. **Security Measures** - Encryption, safeguards
7. **Healthcare Compliance** - HIPAA, PHI protection
8. **Older Adult Considerations** - Readability, accessibility

### Special Features:
- **Red Flags**: Concerning practices with severity levels
- **Positive Practices**: Things they do well
- **Vague Language**: Euphemisms and unclear terms
- **Missing Information**: Critical omissions
- **Quotable Findings**: Research-ready citations
- **HIPAA Assessment**: Compliance evaluation

---

## 🎓 Example Workflow

### For Researchers:
```bash
# 1. Deep analysis of target app
python main.py \
  --url https://app.com/privacy \
  --name "HealthApp" \
  --model claude \
  --depth deep

# 2. Review HTML report for insights
open outputs/reports/HealthApp_report_*.html

# 3. Extract quotable findings from JSON
cat outputs/reports/HealthApp_report_*.json | \
  jq '.quotable_findings'

# 4. Compare multiple apps
# (Add apps to config.yaml first)
python main.py --analyze-all
```

### For Compliance Teams:
```bash
# 1. Standard analysis
python main.py \
  --url https://yourapp.com/privacy \
  --name "YourApp" \
  --depth standard

# 2. Focus on HIPAA section in report
# 3. Review red flags for compliance gaps
# 4. Share HTML report with legal team
```

### For App Developers:
```bash
# 1. Analyze your own policy
python main.py \
  --url https://yourapp.com/privacy \
  --name "YourApp"

# 2. Analyze competitors
python main.py --analyze-all

# 3. Review comparison report
open outputs/reports/comparison_report_*.html

# 4. Improve based on findings
```

---

## 🛠️ Troubleshooting

### "No API key found"
```bash
# Check .env file exists
ls -la .env

# Verify key format
cat .env
# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### "Scraping failed"
```bash
# Try with Selenium
python main.py --url <URL> --name "<App>" --selenium
```

### "Analysis taking too long"
```bash
# Use quick mode
python main.py --url <URL> --name "<App>" --depth quick
```

### "Cost too high"
```bash
# Use Claude instead of GPT-4
python main.py --url <URL> --name "<App>" --model claude

# Or use quick mode
python main.py --url <URL> --name "<App>" --depth quick
```

---

## 📁 Where Files Are Saved

```
Privacy Policy Analyzer/
├── outputs/
│   ├── reports/          # HTML and JSON reports
│   └── visualizations/   # Charts and graphs
├── data/
│   ├── raw/              # Original scraped text
│   └── cache/            # Cached analyses
└── logs/
    └── analyzer.log      # Detailed logs
```

---

## 🔄 Using the Cache

The analyzer automatically caches results to save time and money:

```bash
# First run: Full analysis (~$0.03)
python main.py --url https://app.com/privacy --name "App"

# Second run: Instant from cache ($0.00)
python main.py --url https://app.com/privacy --name "App"

# Force fresh analysis
python main.py --url https://app.com/privacy --name "App" --force-reanalyze
```

**Cache Location**: `data/cache/`
**Cache Key**: SHA-256 hash of (policy text + depth + model)

---

## 🎯 Best Practices

1. **Start with Standard**: Use `--depth standard` for most cases
2. **Use Claude**: Better value for healthcare (`--model claude`)
3. **Enable Cache**: Don't use `--no-cache` unless necessary
4. **Batch Process**: Add multiple apps to config.yaml, use `--analyze-all`
5. **Check Costs**: Review cost estimate before proceeding
6. **Save Reports**: HTML reports are great for sharing
7. **Use JSON**: For programmatic access and further analysis

---

## 🆘 Getting Help

```bash
# Show all options
python main.py --help

# Check version
python main.py --version  # (if implemented)

# View logs
tail -f logs/analyzer.log

# Full documentation
cat README.md
cat ENHANCEMENTS_V2.md
```

---

## 📚 Next Steps

1. **Read Full Docs**: [ENHANCEMENTS_V2.md](ENHANCEMENTS_V2.md)
2. **Understand Output**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
3. **Advanced Config**: Edit `config/config.yaml`
4. **Research Features**: Check quotable_findings in JSON output
5. **Share Results**: HTML reports are publication-ready

---

## ✨ Pro Tips

### 💡 Cost Optimization
```bash
# Use quick mode for screening
python main.py --url <URL> --name "<App>" --depth quick

# Then deep dive on interesting ones
python main.py --url <URL> --name "<App>" --depth deep --force-reanalyze
```

### 💡 Research Workflow
```bash
# 1. Analyze multiple apps
python main.py --analyze-all

# 2. Extract all quotable findings
for file in outputs/reports/*_report_*.json; do
  jq '.quotable_findings[]' "$file"
done > research_quotes.txt
```

### 💡 Batch Processing
```yaml
# Edit config/config.yaml
targets:
  - name: "App 1"
    url: "https://app1.com/privacy"
  - name: "App 2"
    url: "https://app2.com/privacy"
  # ... add more
```
```bash
python main.py --analyze-all
```

---

**You're ready to analyze healthcare privacy policies! 🎉**

For detailed documentation, see:
- [ENHANCEMENTS_V2.md](ENHANCEMENTS_V2.md) - All features explained
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
- [README.md](README.md) - Complete project documentation
