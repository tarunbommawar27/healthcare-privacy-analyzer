import inspect
from src.modules.analyzer import PolicyAnalyzer

# Get the __init__ signature
sig = inspect.signature(PolicyAnalyzer.__init__)
print("PolicyAnalyzer.__init__ parameters:")
for param_name, param in sig.parameters.items():
    if param_name != 'self':
        print(f"  - {param_name}: {param.default if param.default != inspect.Parameter.empty else 'required'}")