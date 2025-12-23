import sys
import traceback

try:
    from datetime import datetime
    print("✅ datetime import works")
    
    from src.modules.analyzer import PolicyAnalyzer
    print("✅ PolicyAnalyzer import works")
    
    # Try to create analyzer
    analyzer = PolicyAnalyzer(
        primary_model='openai/gpt-4-turbo-preview',
        fallback_model=None,
        analysis_depth='standard'
    )
    print("✅ Analyzer created successfully")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n📋 Full traceback:")
    traceback.print_exc()