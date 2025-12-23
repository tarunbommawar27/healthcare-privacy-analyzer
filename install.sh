#!/bin/bash

# Privacy Policy Analyzer - Installation Script
# Supports: Ubuntu/Debian, macOS, Docker

set -e  # Exit on error

echo "========================================================================="
echo "Privacy Policy Analyzer for Healthcare Apps - Installation"
echo "========================================================================="
echo ""

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
echo "[1/7] Checking Python installation..."
if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Check pip
echo ""
echo "[2/7] Checking pip installation..."
if ! command_exists pip3; then
    echo "❌ pip3 not found. Installing pip..."
    python3 -m ensurepip --upgrade
fi
echo "✓ pip found"

# Create virtual environment
echo ""
echo "[3/7] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "[4/7] Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "[5/7] Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel
echo "✓ Core packages upgraded"

# Install dependencies
echo ""
echo "[6/7] Installing Python dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt

# Check critical dependencies
echo ""
echo "Checking critical dependencies:"
python3 -c "import anthropic; print('  ✓ anthropic')" 2>/dev/null || echo "  ⚠ anthropic (optional)"
python3 -c "import openai; print('  ✓ openai')" 2>/dev/null || echo "  ⚠ openai (optional)"
python3 -c "import requests; print('  ✓ requests')"
python3 -c "import pandas; print('  ✓ pandas')"
python3 -c "import numpy; print('  ✓ numpy')"
python3 -c "import yaml; print('  ✓ pyyaml')"

echo "✓ Dependencies installed"

# Download spaCy model
echo ""
echo "[7/7] Downloading spaCy language model..."
python3 -m spacy download en_core_web_sm
echo "✓ spaCy model downloaded"

# Create necessary directories
echo ""
echo "Creating directory structure..."
mkdir -p data/cache
mkdir -p data/raw_policies
mkdir -p outputs/reports
mkdir -p outputs/visualizations
mkdir -p outputs/exports
mkdir -p research_output/reports
mkdir -p research_output/statistics
mkdir -p research_output/visualizations
mkdir -p research_output/dashboard
mkdir -p research_output/checkpoints
mkdir -p logs
echo "✓ Directories created"

# Setup .env file
echo ""
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env file created from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (for Claude)"
    echo "   - OPENAI_API_KEY (for GPT-4)"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Install Chrome/ChromeDriver (Linux only)
if [[ "$OS" == "linux" ]]; then
    echo ""
    echo "Optional: Install Chrome and ChromeDriver for dynamic scraping?"
    read -p "Install Chrome/ChromeDriver? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Chrome..."
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable

        echo "Installing ChromeDriver..."
        CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
        wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
        unzip chromedriver_linux64.zip
        sudo mv chromedriver /usr/local/bin/chromedriver
        sudo chmod +x /usr/local/bin/chromedriver
        rm chromedriver_linux64.zip
        echo "✓ Chrome and ChromeDriver installed"
    fi
fi

# Test installation
echo ""
echo "========================================================================="
echo "Testing installation..."
echo "========================================================================="
python3 main.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Installation successful!"
else
    echo "⚠️  Installation completed with warnings"
fi

echo ""
echo "========================================================================="
echo "Installation Complete!"
echo "========================================================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the analyzer: python main.py --help"
echo ""
echo "Quick start:"
echo "  python main.py --url <PRIVACY_POLICY_URL> --name \"App Name\""
echo ""
echo "For detailed documentation, see:"
echo "  - README.md - Overview and getting started"
echo "  - QUICK_START_V2.md - 5-minute guide"
echo "  - ENHANCEMENTS_V2.md - Feature documentation"
echo ""
echo "For Docker deployment:"
echo "  docker-compose up -d"
echo ""
