"""
Check PrivacyPolicyAnalyzer __init__ parameters
"""

# Read main.py and find the __init__ method
with open('main.py', 'r') as f:
    lines = f.readlines()

# Find PrivacyPolicyAnalyzer class __init__
in_class = False
for i, line in enumerate(lines, 1):
    if 'class PrivacyPolicyAnalyzer:' in line:
        in_class = True
        print(f"Found class at line {i}")
    
    if in_class and 'def __init__' in line:
        print(f"\nFound __init__ at line {i}:")
        # Print next 20 lines
        for j in range(i-1, min(i+19, len(lines))):
            print(f"{j+1:4d} | {lines[j]}", end='')
        break