# API Reference

Documentation for the core modules and classes.

## Module: `src.modules.scraper`

### Class: `PolicyScraper`

Web scraper for extracting privacy policies.

#### Constructor

```python
PolicyScraper(config: Dict)
```

**Parameters:**
- `config` (dict): Scraping configuration containing:
  - `timeout` (int): Request timeout in seconds
  - `user_agent` (str): User agent string
  - `max_retries` (int): Maximum retry attempts
  - `delay_between_requests` (int): Delay between retries
  - `use_headless` (bool): Use headless browser mode

#### Methods

##### `scrape_policy(url: str, use_selenium: bool = False) -> Dict`

Scrape privacy policy from URL.

**Parameters:**
- `url` (str): Privacy policy URL
- `use_selenium` (bool): Use Selenium instead of requests

**Returns:**
- Dictionary with keys:
  - `url`: Original URL
  - `text`: Extracted text
  - `success`: Whether scraping succeeded
  - `length`: Character count
  - `timestamp`: Scrape timestamp

**Example:**
```python
scraper = PolicyScraper(config)
result = scraper.scrape_policy("https://example.com/privacy")
if result['success']:
    print(f"Scraped {result['length']} characters")
```

---

## Module: `src.modules.analyzer`

### Class: `PolicyAnalyzer`

LLM-based privacy policy analyzer.

#### Constructor

```python
PolicyAnalyzer(config: Dict)
```

**Parameters:**
- `config` (dict): Configuration containing:
  - `llm`: LLM settings (provider, model, temperature, etc.)
  - `analysis`: Analysis parameters (red flags, categories)

#### Methods

##### `analyze_policy(policy_text: str) -> Dict`

Analyze privacy policy using configured LLM.

**Parameters:**
- `policy_text` (str): Privacy policy text to analyze

**Returns:**
- Dictionary with keys:
  - `summary`: Executive summary
  - `categories`: Analysis by category
  - `red_flags_detected`: List of red flags found
  - `overall_assessment`: Overall assessment
  - `recommendations`: List of recommendations
  - `metadata`: Analysis metadata

**Example:**
```python
analyzer = PolicyAnalyzer(config)
analysis = analyzer.analyze_policy(policy_text)
print(analysis['summary'])
```

---

## Module: `src.modules.scorer`

### Class: `RiskScorer`

Risk scoring calculator.

#### Constructor

```python
RiskScorer(config: Dict)
```

**Parameters:**
- `config` (dict): Configuration containing:
  - `scoring`: Scoring settings (weights, thresholds)

#### Methods

##### `calculate_risk_score(analysis: Dict) -> Dict`

Calculate risk score from analysis results.

**Parameters:**
- `analysis` (dict): Analysis results from PolicyAnalyzer

**Returns:**
- Dictionary with keys:
  - `overall_score`: Overall risk score (0-1)
  - `base_score`: Score before red flag adjustment
  - `risk_level`: Risk level (LOW/MEDIUM/HIGH/CRITICAL)
  - `risk_color`: Color code for visualization
  - `category_scores`: Scores by category
  - `red_flags_count`: Number of red flags
  - `red_flags`: List of red flags

**Example:**
```python
scorer = RiskScorer(config)
scoring = scorer.calculate_risk_score(analysis)
print(f"Risk: {scoring['overall_score']:.2f} ({scoring['risk_level']})")
```

##### `get_risk_level(score: float) -> str`

Get risk level label from score.

**Parameters:**
- `score` (float): Risk score (0-1)

**Returns:**
- String: "LOW", "MEDIUM", "HIGH", or "CRITICAL"

---

## Module: `src.modules.reporter`

### Class: `ReportGenerator`

Multi-format report generator.

#### Constructor

```python
ReportGenerator(config: Dict)
```

**Parameters:**
- `config` (dict): Configuration containing:
  - `output`: Output settings
  - `paths`: Output directory paths

#### Methods

##### `generate_html_report(app_name: str, url: str, analysis: Dict, scoring: Dict, visualizations: List[str]) -> str`

Generate HTML report.

**Parameters:**
- `app_name` (str): Application name
- `url` (str): Privacy policy URL
- `analysis` (dict): Analysis results
- `scoring` (dict): Risk scoring results
- `visualizations` (list): List of visualization file paths

**Returns:**
- String: Path to generated HTML file

##### `generate_json_report(app_name: str, url: str, analysis: Dict, scoring: Dict) -> str`

Generate JSON report.

**Parameters:**
- `app_name` (str): Application name
- `url` (str): Privacy policy URL
- `analysis` (dict): Analysis results
- `scoring` (dict): Risk scoring results

**Returns:**
- String: Path to generated JSON file

##### `create_visualizations(app_name: str, scoring: Dict) -> List[str]`

Create visualization charts.

**Parameters:**
- `app_name` (str): Application name
- `scoring` (dict): Risk scoring results

**Returns:**
- List of created file paths

##### `generate_comparison_report(results: List[Dict]) -> str`

Generate comparison report for multiple apps.

**Parameters:**
- `results` (list): List of analysis results

**Returns:**
- String: Path to comparison report

---

## Module: `src.utils.logger`

### Function: `setup_logger(log_file: str, level: str) -> Logger`

Configure application logger.

**Parameters:**
- `log_file` (str): Path to log file
- `level` (str): Logging level (DEBUG/INFO/WARNING/ERROR)

**Returns:**
- Logger instance

### Function: `get_logger() -> Logger`

Get the configured logger instance.

---

## Module: `src.utils.file_handler`

### Class: `FileHandler`

File I/O utility class.

#### Methods

##### `save_json(data: Dict, filepath: str, indent: int = 2) -> None`

Save data to JSON file.

##### `load_json(filepath: str) -> Dict`

Load data from JSON file.

##### `load_yaml(filepath: str) -> Dict`

Load configuration from YAML file.

##### `save_text(text: str, filepath: str) -> None`

Save text to file.

##### `load_text(filepath: str) -> str`

Load text from file.

##### `ensure_dir(path: str) -> Path`

Ensure directory exists.

##### `generate_filename(prefix: str, extension: str = "json") -> str`

Generate timestamped filename.

---

## Configuration Schema

### Main Configuration (`config.yaml`)

```yaml
llm:
  provider: string  # "openai" or "anthropic"
  model: string
  temperature: float  # 0.0 - 1.0
  max_tokens: int
  timeout: int

scraping:
  timeout: int
  user_agent: string
  max_retries: int
  delay_between_requests: int
  use_headless: bool
  wait_for_load: int

analysis:
  red_flags: list[string]
  healthcare_specific: list[string]
  categories: list[string]

scoring:
  weights:
    data_collection: float
    data_usage: float
    third_party_sharing: float
    data_retention: float
    user_rights: float
    security_measures: float
    healthcare_compliance: float
  risk_thresholds:
    low: float
    medium: float
    high: float

output:
  report_format: list[string]  # ["html", "pdf", "json"]
  include_visualizations: bool
  save_raw_data: bool
  summary_length: int

targets:
  - name: string
    url: string
    category: string

logging:
  level: string
  file: string
  rotation: string
  retention: string

paths:
  raw_data: string
  processed_data: string
  reports: string
  visualizations: string
  logs: string
```

---

## Data Structures

### Analysis Result

```python
{
    "summary": str,
    "categories": {
        "Category Name": {
            "findings": str,
            "concerns": list[str],
            "positive_aspects": list[str]
        }
    },
    "red_flags_detected": list[str],
    "overall_assessment": str,
    "recommendations": list[str],
    "metadata": {
        "provider": str,
        "model": str,
        "text_length": int
    }
}
```

### Scoring Result

```python
{
    "overall_score": float,  # 0.0 - 1.0
    "base_score": float,
    "risk_level": str,  # LOW/MEDIUM/HIGH/CRITICAL
    "risk_color": str,  # Hex color code
    "category_scores": dict[str, float],
    "red_flags_count": int,
    "red_flags": list[str]
}
```

### Complete Result

```python
{
    "app_name": str,
    "url": str,
    "scraped_data": dict,
    "analysis": dict,
    "scoring": dict,
    "reports": list[str],  # File paths
    "visualizations": list[str]  # File paths
}
```
