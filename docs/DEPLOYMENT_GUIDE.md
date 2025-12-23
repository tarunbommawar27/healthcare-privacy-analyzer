# Deployment Guide

## Overview

This guide covers deploying the Privacy Policy Analyzer in various environments:

1. **Local Installation** - Development and single-user usage
2. **Docker Deployment** - Containerized, reproducible environment
3. **Cloud Deployment** - AWS, Google Cloud, Azure
4. **CI/CD Integration** - Automated analysis pipelines

---

## Table of Contents

- [Quick Start](#quick-start)
- [Local Installation](#local-installation)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd privacy-policy-analyzer

# Run installation script
chmod +x install.sh
./install.sh

# Configure API keys
nano .env  # Add your ANTHROPIC_API_KEY and/or OPENAI_API_KEY

# Test installation
python main.py --help
```

### Option 2: Docker (Fastest)

```bash
# Clone repository
git clone <repository-url>
cd privacy-policy-analyzer

# Configure API keys
cp .env.example .env
nano .env  # Add API keys

# Build and run
docker-compose up -d

# Run analysis
docker-compose exec analyzer python main.py --help
```

---

## Local Installation

### Prerequisites

- **Python 3.9+** (3.11 recommended)
- **pip** (Python package manager)
- **Git** (for cloning repository)
- **4GB RAM minimum** (8GB recommended)
- **5GB disk space** (for dependencies and cache)

### Step-by-Step Installation

#### 1. Clone Repository

```bash
git clone <repository-url>
cd privacy-policy-analyzer
```

#### 2. Create Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

#### 4. Setup Environment Variables

```bash
# Copy example
cp .env.example .env

# Edit with your API keys
# Linux/macOS: nano .env
# Windows: notepad .env
```

Add your API keys:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

#### 5. Create Directory Structure

```bash
mkdir -p data/cache data/raw_policies
mkdir -p outputs/reports outputs/visualizations outputs/exports
mkdir -p research_output/{reports,statistics,visualizations,dashboard,checkpoints}
mkdir -p logs
```

#### 6. Test Installation

```bash
python main.py --help
```

### Optional: Install Chrome/ChromeDriver (for dynamic scraping)

#### Ubuntu/Debian

```bash
# Install Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip
```

#### macOS

```bash
# Using Homebrew
brew install --cask google-chrome
brew install chromedriver
```

#### Windows

1. Download [Chrome](https://www.google.com/chrome/)
2. Download [ChromeDriver](https://chromedriver.chromium.org/)
3. Add ChromeDriver to PATH

---

## Docker Deployment

### Prerequisites

- **Docker** 20.10+
- **Docker Compose** 1.29+
- **4GB RAM** allocated to Docker
- **10GB disk space**

### Quick Start with Docker

#### 1. Build Image

```bash
# Build from Dockerfile
docker build -t privacy-policy-analyzer:latest .

# Or use docker-compose
docker-compose build
```

#### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit and add API keys
nano .env
```

#### 3. Run Container

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f analyzer

# Run analysis
docker-compose exec analyzer python main.py \
    --url "https://www.zocdoc.com/about/privacy/" \
    --name "Zocdoc" \
    --model claude \
    --depth standard
```

#### 4. Access Outputs

Outputs are automatically mounted to your host machine:
- `./outputs/` - Analysis reports
- `./research_output/` - Research workflow outputs
- `./logs/` - Application logs

### Docker Compose Services

#### Main Analyzer Service

```yaml
# Start analyzer service
docker-compose up analyzer

# Run specific command
docker-compose run analyzer python main.py --analyze-all
```

#### Jupyter Lab (Optional)

For interactive analysis and development:

```bash
# Start Jupyter Lab
docker-compose --profile jupyter up jupyter

# Access at http://localhost:8888
# Token will be displayed in logs
docker-compose logs jupyter | grep token
```

### Docker Commands Cheat Sheet

```bash
# Build
docker-compose build

# Start services (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v

# Run one-off command
docker-compose run analyzer python main.py --help

# Execute command in running container
docker-compose exec analyzer python main.py --analyze-all

# Shell access
docker-compose exec analyzer bash

# View resource usage
docker stats privacy-analyzer
```

### Customizing Docker Deployment

#### Adjust Resource Limits

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for faster processing
      memory: 8G       # Increase for large batches
    reservations:
      cpus: '2.0'
      memory: 4G
```

#### Persistent Volumes

Named volumes for data persistence:
- `analyzer-cache` - LLM response cache
- `analyzer-raw` - Raw policy texts

Data persists across container restarts.

#### Environment Variables

Override in `docker-compose.yml`:

```yaml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - LOG_LEVEL=DEBUG
  - MAX_WORKERS=4
```

---

## Production Deployment

### Security Considerations

#### 1. API Key Management

**Never commit API keys to version control.**

Use environment variables or secret management:

```bash
# Option 1: Environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# Option 2: Docker secrets
docker secret create anthropic_key ./anthropic_api_key.txt
```

#### 2. Network Security

- Run containers in private network
- Use reverse proxy (nginx) for external access
- Enable HTTPS/TLS
- Implement rate limiting

#### 3. Container Security

```dockerfile
# Run as non-root user (already in Dockerfile)
USER analyzer

# Read-only root filesystem
docker run --read-only --tmpfs /tmp privacy-policy-analyzer

# Drop capabilities
docker run --cap-drop=ALL privacy-policy-analyzer
```

### Performance Optimization

#### 1. Parallel Processing

```python
# research_workflow.py
workflow = ResearchWorkflow(
    max_concurrent=5  # Increase for faster batch processing
)
```

#### 2. Caching Strategy

```yaml
# config/config.yaml
analysis:
  cache_enabled: true
  cache_duration_days: 90  # Longer for production
```

#### 3. Resource Allocation

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 16G
```

### Monitoring & Logging

#### 1. Application Logs

```bash
# View real-time logs
docker-compose logs -f analyzer

# Save logs to file
docker-compose logs analyzer > analyzer.log

# Rotate logs (in docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### 2. Health Checks

Built-in health check in Dockerfile:

```bash
# Check container health
docker ps
# Look for "(healthy)" status

# Manual health check
docker-compose exec analyzer python -c "import sys; sys.exit(0)"
```

#### 3. Metrics Collection

Integrate with monitoring systems:

```python
# Optional: Add Prometheus metrics
from prometheus_client import start_http_server, Counter, Gauge

analyses_counter = Counter('analyses_total', 'Total analyses performed')
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate')
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: EC2 Instance

```bash
# Launch EC2 instance (Ubuntu 22.04, t3.large minimum)
# SSH into instance
ssh -i key.pem ubuntu@<instance-ip>

# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Clone and deploy
git clone <repository-url>
cd privacy-policy-analyzer
cp .env.example .env
# Add API keys to .env
docker-compose up -d
```

#### Option 2: ECS (Fargate)

```bash
# Build and push to ECR
aws ecr create-repository --repository-name privacy-analyzer
docker tag privacy-policy-analyzer:latest <account>.dkr.ecr.<region>.amazonaws.com/privacy-analyzer:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/privacy-analyzer:latest

# Create ECS task definition and service
# Use task-definition.json (see examples/)
aws ecs create-cluster --cluster-name privacy-analyzer-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster privacy-analyzer-cluster --service-name analyzer --task-definition privacy-analyzer
```

#### Option 3: Lambda (for event-driven analysis)

```python
# lambda_handler.py
import json
from src.modules.analyzer import PolicyAnalyzer

def lambda_handler(event, context):
    url = event['url']
    app_name = event['app_name']

    analyzer = PolicyAnalyzer(config)
    result = analyzer.analyze_policy_from_url(url, app_name)

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

### Google Cloud Platform

#### Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/privacy-analyzer

# Deploy
gcloud run deploy privacy-analyzer \
    --image gcr.io/<project-id>/privacy-analyzer \
    --platform managed \
    --region us-central1 \
    --memory 4Gi \
    --set-env-vars ANTHROPIC_API_KEY=<key>
```

### Azure

#### Container Instances

```bash
# Create resource group
az group create --name privacy-analyzer-rg --location eastus

# Deploy container
az container create \
    --resource-group privacy-analyzer-rg \
    --name privacy-analyzer \
    --image <registry>/privacy-policy-analyzer:latest \
    --cpu 2 \
    --memory 4 \
    --environment-variables ANTHROPIC_API_KEY=<key>
```

---

## CI/CD Integration

### GitHub Actions

`.github/workflows/analyze.yml`:

```yaml
name: Analyze Privacy Policies

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download en_core_web_sm

      - name: Run analysis
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python main.py --analyze-all --depth standard

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: analysis-results
          path: outputs/
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
stages:
  - analyze
  - validate
  - report

analyze:
  stage: analyze
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python -m spacy download en_core_web_sm
    - python main.py --analyze-all
  artifacts:
    paths:
      - outputs/

validate:
  stage: validate
  script:
    - python -m src.utils.validator outputs/reports/
  dependencies:
    - analyze

report:
  stage: report
  script:
    - python -c "from src.modules.comparative_analyzer import *; ..."
  dependencies:
    - analyze
```

---

## Troubleshooting

### Common Issues

#### 1. "Module not found" errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. API key errors

```bash
# Check .env file exists and has correct keys
cat .env | grep API_KEY

# Verify keys are loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ANTHROPIC_API_KEY')[:10])"
```

#### 3. Chrome/Selenium errors

```bash
# Check Chrome installation
google-chrome --version

# Check ChromeDriver
chromedriver --version

# Versions should match
```

#### 4. Docker build fails

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### 5. Out of memory errors

```bash
# Increase Docker memory limit (Docker Desktop > Settings > Resources)
# Or reduce concurrent analyses
workflow = ResearchWorkflow(max_concurrent=2)
```

### Getting Help

1. **Check logs:**
   ```bash
   # Local
   tail -f logs/analyzer.log

   # Docker
   docker-compose logs -f analyzer
   ```

2. **Enable debug mode:**
   ```bash
   export LOG_LEVEL=DEBUG
   python main.py --url <url> --name <name>
   ```

3. **Review documentation:**
   - [README.md](../README.md)
   - [ENHANCEMENTS_V2.md](../ENHANCEMENTS_V2.md)
   - [VALIDATION_GUIDE.md](VALIDATION_GUIDE.md)

4. **Open an issue** on GitHub with:
   - Error message
   - Steps to reproduce
   - Environment (OS, Python version, Docker version)
   - Logs

---

## Summary

| Deployment Method | Best For | Pros | Cons |
|------------------|----------|------|------|
| **Local Install** | Development, single user | Simple, fast iteration | Manual setup |
| **Docker** | Reproducibility, testing | Consistent environment | Requires Docker |
| **Cloud (EC2/VM)** | Production, multi-user | Scalable, always-on | Higher cost |
| **Serverless (Lambda)** | Event-driven, sporadic | Pay-per-use, auto-scale | Cold starts |
| **Container Service (ECS/Cloud Run)** | Production, auto-scaling | Managed, scalable | Platform lock-in |

**Recommendation:**
- **Development:** Local installation
- **Research studies:** Docker
- **Production:** Cloud container service (ECS, Cloud Run, ACI)

---

**Next Steps:**

1. Choose deployment method
2. Follow installation steps
3. Configure API keys
4. Run test analysis
5. Set up monitoring (production)
6. Review [QUICK_START_V2.md](../QUICK_START_V2.md) for usage

For advanced configurations and production hardening, contact the maintainers.
