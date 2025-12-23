"""
Complete inspection of PolicyAnalyzer class
"""

import inspect
from src.modules.analyzer import PolicyAnalyzer

print("="*70)
print("PolicyAnalyzer Class Inspection")
print("="*70)

# Get __init__ signature
print("\n1️⃣ __init__ method signature:")
print("-"*70)
sig = inspect.signature(PolicyAnalyzer.__init__)
for param_name, param in sig.parameters.items():
    if param_name != 'self':
        default = param.default if param.default != inspect.Parameter.empty else 'REQUIRED'
        annotation = param.annotation if param.annotation != inspect.Parameter.empty else 'Any'
        print(f"   {param_name}")
        print(f"      Type: {annotation}")
        print(f"      Default: {default}")
        print()

# Get the actual __init__ source code
print("\n2️⃣ __init__ source code:")
print("-"*70)
try:
    source = inspect.getsource(PolicyAnalyzer.__init__)
    # Print first 50 lines
    lines = source.split('\n')[:50]
    for i, line in enumerate(lines, 1):
        print(f"{i:3d} | {line}")
except Exception as e:
    print(f"Could not get source: {e}")

# List all methods
print("\n3️⃣ Available methods:")
print("-"*70)
for name, method in inspect.getmembers(PolicyAnalyzer, predicate=inspect.ismethod):
    if not name.startswith('_'):
        sig = inspect.signature(method)
        print(f"   {name}{sig}")

print("\n" + "="*70)