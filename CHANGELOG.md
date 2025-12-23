# Changelog

All notable changes to the Privacy Policy Analyzer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Interactive HTML dashboard
- REST API server
- Comprehensive test suite
- Web-based user interface
- Multi-language support

---

## [2.0.0] - 2025-01-15

### 🎉 Major Release - Research-Grade Platform

This release transforms the Privacy Policy Analyzer into a production-ready, research-grade platform with comprehensive analysis, validation, and automation capabilities.

### Added

#### Enhanced LLM Analysis
- **Multi-model support** with automatic fallback (Claude Sonnet 4 primary, GPT-4 fallback)
- **Three analysis depths**: quick (~$0.01), standard (~$0.03), deep with chain-of-thought (~$0.11)
- **Advanced prompting** with 8-step chain-of-thought reasoning in deep mode
- **Comprehensive JSON schema** with 8 categories, red flags with severity/quotes/location
- **Policy preprocessing** with intelligent chunking for long policies (>6000 tokens)
- **Intelligent caching** using SHA-256 hashes for cost and time savings
- **Cost estimation** with real-time token counting and pricing display
- **Enhanced CLI** with new flags: `--model`, `--depth`, `--force-reanalyze`, `--show-cost`

#### Comparative Analysis Module
- **Statistical analysis**: mean, median, std deviation, percentiles (25th, 50th, 75th, 90th)
- **Correlation analysis**: Pearson correlation, point-biserial tests
- **K-means clustering**: automatic grouping of similar apps
- **Gap analysis**: HIPAA mention %, retention policies %, data deletion rights %
- **Pattern detection**: common red flags, severity distribution, category patterns
- **Best/worst practice identification**: top/bottom 25% performers per category
- **Research quote extraction**: quotable findings organized by theme

#### Research Workflow Orchestrator
- **End-to-end automation**: CSV input → analysis → validation → statistics → summary
- **Batch processing** with configurable parallel execution (default: 3 concurrent)
- **Checkpoint/resume functionality** for long-running workflows
- **Progress tracking** with tqdm progress bars
- **Comparative analysis integration** within workflow
- **Multi-format statistics export**: CSV (wide format), Excel (multi-sheet)
- **Research summary generation** in Markdown format

#### Quality Validation System
- **Completeness validation**: all required fields, correct types, non-null values
- **Score validation**: 0-100 range, no negative values, numeric types
- **Consistency checks**: overall vs category scores (±15 point tolerance)
- **Red flag validation**: proper structure, valid severity levels, non-empty quotes
- **Anomaly detection**: statistical outlier identification using z-scores (threshold: 3.0)
- **Dual modes**: normal (lenient) and strict (warnings = errors)
- **Comprehensive reporting**: human-readable text + machine-readable JSON
- **Workflow integration**: automatic validation in research pipeline

#### Deployment & DevOps
- **Dockerfile** with Python 3.11, Chrome/ChromeDriver, non-root user, health checks
- **Docker Compose** with analyzer service, optional Jupyter Lab, named volumes
- **Installation script** (`install.sh`) with automatic dependency installation
- **Demo script** (`demo.sh`) with 9 interactive demos
- **.dockerignore** for optimized container builds

#### Documentation
- **VALIDATION_GUIDE.md** (600+ lines) - Comprehensive quality validation guide
- **DEPLOYMENT_GUIDE.md** (500+ lines) - Local, Docker, and cloud deployment
- **ENHANCEMENTS_V2.md** (500+ lines) - Complete feature documentation
- **PROJECT_STATUS.md** - Current project status and capabilities
- **CITATION.cff** - Citation File Format for academic citations
- **LICENSE** - MIT License with third-party attributions
- **CONTRIBUTORS.md** - Contribution guidelines and recognition
- **CHANGELOG.md** - This file

#### Examples
- **comparative_analysis_example.py** - 8 usage examples for comparative analysis
- **validator_example.py** - 7 examples demonstrating quality validation

### Changed

#### Core Modules
- **analyzer.py** - Complete rewrite (1,067 lines) with multi-model support and advanced prompting
- **main.py** - Complete rewrite (555 lines) with enhanced CLI and new flags
- **config.yaml** - Expanded to 150 lines with multi-model settings, analysis depths, expanded red flags

#### Dependencies
- Added `tiktoken>=0.5.2` for token counting
- Added `scipy>=1.11.0` for statistical tests
- Added `weasyprint>=60.0` for PDF generation (future use)
- Added `openpyxl>=3.1.2` and `xlsxwriter>=3.1.9` for Excel export

### Fixed
- Improved error handling throughout codebase
- Better API key validation with helpful error messages
- Graceful degradation on LLM API failures
- Proper type checking and validation

### Security
- Non-root user in Docker containers (uid 1000)
- API keys stored only in .env file
- Read-only filesystem support in Docker
- Network isolation in Docker Compose

### Performance
- Intelligent caching reduces repeated analysis costs by 100%
- Parallel processing in batch mode (3 concurrent by default)
- Efficient tokenization with tiktoken
- Chunking only when necessary (policies >6000 tokens)

---

## [1.0.0] - 2024-12-01

### Initial Release

#### Added
- Basic privacy policy scraping (static web pages)
- LLM-based analysis with OpenAI GPT models
- Risk scoring system
- JSON and HTML report generation
- Basic CLI interface
- Configuration management with YAML
- Logging utilities
- File handling utilities
- Basic documentation (README.md)

#### Features
- Scrape privacy policies from URLs
- Analyze policies using LLM
- Generate risk scores
- Create structured reports
- Command-line interface

#### Modules
- `scraper.py` - Web scraping functionality
- `analyzer.py` - Basic LLM analysis (300 lines)
- `scorer.py` - Risk scoring
- `reporter.py` - Report generation
- `logger.py` - Logging utilities
- `file_handler.py` - File I/O

---

## Version History Summary

| Version | Date | Key Features | Lines of Code |
|---------|------|--------------|---------------|
| **2.0.0** | 2025-01-15 | Research-grade platform, validation, workflows | ~10,000 |
| **1.0.0** | 2024-12-01 | Initial release, basic analysis | ~2,000 |

---

## Upgrade Guide

### Upgrading from v1.0 to v2.0

#### Breaking Changes
- Configuration file structure has changed (new fields in `config.yaml`)
- CLI flags have been extended (new flags added, old flags still work)
- JSON output schema has been significantly enhanced
- Analysis results are no longer backward compatible

#### Migration Steps

1. **Backup existing data:**
   ```bash
   cp -r outputs/ outputs_backup/
   cp config/config.yaml config/config.yaml.backup
   ```

2. **Update configuration:**
   ```bash
   # Review new config.yaml structure
   diff config/config.yaml.backup config/config.yaml

   # Update your config with new fields
   nano config/config.yaml
   ```

3. **Update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   python -m spacy download en_core_web_sm
   ```

4. **Test new features:**
   ```bash
   # Run a quick test analysis
   python main.py --url <URL> --name "Test" --depth quick

   # Run demos
   ./demo.sh
   ```

5. **Migrate existing analyses (optional):**
   ```bash
   # Re-analyze with new system for consistency
   python main.py --analyze-all --force-reanalyze
   ```

#### New Capabilities Available

After upgrading, you can:
- Use multiple models (`--model claude`, `--model gpt4`, `--model auto`)
- Choose analysis depth (`--depth quick|standard|deep`)
- Enable validation (`validate=True` in workflow)
- Run comparative analysis (see examples/)
- Use Docker deployment

---

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR version** (x.0.0): Incompatible API changes
- **MINOR version** (0.x.0): Backward-compatible new features
- **PATCH version** (0.0.x): Backward-compatible bug fixes

---

## How to Contribute

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for contribution guidelines.

Report bugs or request features via [GitHub Issues](https://github.com/yourusername/privacy-policy-analyzer/issues).

---

## Links

- **Repository**: https://github.com/yourusername/privacy-policy-analyzer
- **Documentation**: See `docs/` folder
- **Issues**: https://github.com/yourusername/privacy-policy-analyzer/issues
- **Releases**: https://github.com/yourusername/privacy-policy-analyzer/releases

---

*Generated by Privacy Policy Analyzer Team*
*Last updated: 2025-01-15*
