#!/bin/bash

# Privacy Policy Analyzer - Demo Script
# Demonstrates key features with sample analyses

set -e

echo "========================================================================="
echo "Privacy Policy Analyzer - Demo Script"
echo "========================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check API keys
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create .env file from .env.example and add your API keys"
    exit 1
fi

source .env

if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ No API keys found${NC}"
    echo "Please add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env file"
    exit 1
fi

echo -e "${GREEN}✓ Environment setup complete${NC}"
echo ""

# Menu
echo "Select demo to run:"
echo "1. Single Policy Analysis (Quick)"
echo "2. Single Policy Analysis (Deep with Chain-of-Thought)"
echo "3. Cost Estimation"
echo "4. Batch Analysis (3 apps)"
echo "5. Comparative Analysis & Statistics"
echo "6. Quality Validation"
echo "7. Complete Research Workflow"
echo "8. Show Example Outputs"
echo "9. Run All Demos"
echo "0. Exit"
echo ""
read -p "Enter choice [0-9]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 1: Quick Analysis${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Analyzing a healthcare app privacy policy (quick mode)..."
        echo ""

        python main.py \
            --url "https://www.zocdoc.com/about/privacy/" \
            --name "Zocdoc" \
            --model claude \
            --depth quick \
            --show-cost

        echo ""
        echo -e "${GREEN}✓ Quick analysis complete${NC}"
        echo "Report saved to: outputs/reports/Zocdoc_analysis.json"
        ;;

    2)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 2: Deep Analysis with Chain-of-Thought${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Analyzing with 8-step chain-of-thought reasoning..."
        echo "This will take 2-4 minutes and cost ~$0.11"
        echo ""
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python main.py \
                --url "https://www.zocdoc.com/about/privacy/" \
                --name "Zocdoc" \
                --model claude \
                --depth deep \
                --show-cost \
                --force-reanalyze

            echo ""
            echo -e "${GREEN}✓ Deep analysis complete${NC}"
            echo "Review the detailed reasoning in the JSON output"
        fi
        ;;

    3)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 3: Cost Estimation${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Demonstrating cost estimation for different analysis depths..."
        echo ""

        echo "Quick mode (~$0.01):"
        python main.py \
            --url "https://www.zocdoc.com/about/privacy/" \
            --name "Zocdoc" \
            --depth quick \
            --show-cost \
            --no-cost-estimate

        echo ""
        echo "Standard mode (~$0.03):"
        python main.py \
            --url "https://www.zocdoc.com/about/privacy/" \
            --name "Zocdoc" \
            --depth standard \
            --show-cost \
            --no-cost-estimate

        echo ""
        echo "Deep mode (~$0.11):"
        python main.py \
            --url "https://www.zocdoc.com/about/privacy/" \
            --name "Zocdoc" \
            --depth deep \
            --show-cost \
            --no-cost-estimate
        ;;

    4)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 4: Batch Analysis${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Analyzing 3 healthcare apps in batch mode..."
        echo ""

        python main.py --analyze-all --depth standard

        echo ""
        echo -e "${GREEN}✓ Batch analysis complete${NC}"
        echo "Reports saved to: outputs/reports/"
        ;;

    5)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 5: Comparative Analysis & Statistics${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Running comparative analysis on all completed analyses..."
        echo ""

        python examples/comparative_analysis_example.py

        echo ""
        echo -e "${GREEN}✓ Comparative analysis complete${NC}"
        echo "See examples/comparative_analysis_example.py for programmatic usage"
        ;;

    6)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 6: Quality Validation${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Validating all analyses for quality and consistency..."
        echo ""

        python -m src.utils.validator outputs/reports/ --report outputs/validation_report.txt

        if [ -f "outputs/validation_report.txt" ]; then
            echo ""
            echo "Validation report preview:"
            head -n 50 outputs/validation_report.txt
            echo ""
            echo "Full report: outputs/validation_report.txt"
        fi

        echo ""
        echo -e "${GREEN}✓ Validation complete${NC}"
        ;;

    7)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 7: Complete Research Workflow${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""
        echo "Running end-to-end research workflow:"
        echo "  1. Load apps from CSV"
        echo "  2. Batch analyze"
        echo "  3. Validate analyses"
        echo "  4. Comparative analysis"
        echo "  5. Export statistics"
        echo "  6. Generate research summary"
        echo ""
        echo "⚠️  This will analyze all apps in config/config.yaml"
        echo "    Estimated time: 5-10 minutes per app"
        echo "    Estimated cost: $0.03-0.11 per app"
        echo ""
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python -c "
from src.modules.research_workflow import ResearchWorkflow

workflow = ResearchWorkflow(
    output_dir='research_output/',
    model='auto',
    depth='standard',
    max_concurrent=3
)

results = workflow.run_complete_workflow(
    validate=True,
    strict_validation=False
)

print('\n========================================================================')
print('Research Workflow Complete!')
print('========================================================================')
print(f\"Status: {results.get('status', 'unknown')}\")
print(f\"Outputs saved to: research_output/\")
print('\nKey outputs:')
for key, path in results.items():
    if key not in ['status', 'analyses_count']:
        print(f\"  {key}: {path}\")
"
            echo ""
            echo -e "${GREEN}✓ Research workflow complete${NC}"
        fi
        ;;

    8)
        echo ""
        echo -e "${BLUE}=========================================================================${NC}"
        echo -e "${BLUE}Demo 8: Example Outputs${NC}"
        echo -e "${BLUE}=========================================================================${NC}"
        echo ""

        if [ -d "outputs/reports" ] && [ "$(ls -A outputs/reports/*.json 2>/dev/null)" ]; then
            echo "Sample analysis output (first 50 lines):"
            echo ""
            SAMPLE=$(ls outputs/reports/*.json | head -n 1)
            echo "File: $SAMPLE"
            echo "---"
            python -m json.tool "$SAMPLE" | head -n 50
            echo "..."
            echo ""
            echo "Full reports available in: outputs/reports/"
        else
            echo "No reports found. Run Demo 1 or 4 first."
        fi

        if [ -f "research_output/statistics/research_summary.md" ]; then
            echo ""
            echo "Research summary (first 50 lines):"
            echo "---"
            head -n 50 research_output/statistics/research_summary.md
            echo "..."
            echo ""
            echo "Full summary: research_output/statistics/research_summary.md"
        fi
        ;;

    9)
        echo ""
        echo -e "${BLUE}Running all demos (excluding #7 - complete workflow)...${NC}"
        echo ""

        # Run demos 1-6 and 8
        for i in 1 3 6 8; do
            echo ""
            echo -e "${YELLOW}>>> Running Demo $i...${NC}"
            $0 <<< "$i"
            echo ""
            sleep 2
        done

        echo ""
        echo -e "${GREEN}✓ All demos complete${NC}"
        ;;

    0)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "========================================================================="
echo "Demo Complete!"
echo "========================================================================="
echo ""
echo "Next steps:"
echo "  - Review outputs in outputs/ directory"
echo "  - Try different analysis depths (quick/standard/deep)"
echo "  - Run comparative analysis on multiple apps"
echo "  - Explore research workflow features"
echo ""
echo "Documentation:"
echo "  - README.md - Overview"
echo "  - QUICK_START_V2.md - Getting started"
echo "  - ENHANCEMENTS_V2.md - All features"
echo "  - docs/VALIDATION_GUIDE.md - Quality validation"
echo ""
