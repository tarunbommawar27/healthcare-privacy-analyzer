"""
Fix the model variable name mismatch
"""

print("🔧 Fixing model variable name in main.py...\n")

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Find the PrivacyPolicyAnalyzer __init__ signature
init_line = None
for i, line in enumerate(lines):
    if 'class PrivacyPolicyAnalyzer:' in line:
        # Found class, now find __init__
        for j in range(i+1, min(i+30, len(lines))):
            if 'def __init__' in lines[j]:
                init_line = lines[j]
                print(f"Found __init__ at line {j+1}:")
                print(f"  {init_line}")
                break
        break

if init_line:
    # Extract parameter names
    import re
    # Match parameters like: def __init__(self, param1='default', param2='default'):
    params_match = re.search(r'def __init__\(self,\s*(.+?)\):', init_line)
    if params_match:
        params_str = params_match.group(1)
        print(f"\nParameters: {params_str}")
        
        # Parse individual parameters
        params = [p.strip().split('=')[0] for p in params_str.split(',')]
        print(f"\nParameter names: {params}")
        
        # Find what to use for model
        model_param = None
        depth_param = None
        cache_param = None
        
        for param in params:
            if 'model' in param.lower():
                model_param = param
            if 'depth' in param.lower():
                depth_param = param
            if 'cache' in param.lower():
                cache_param = param
        
        print(f"\nDetected parameter names:")
        print(f"  Model: {model_param}")
        print(f"  Depth: {depth_param}")
        print(f"  Cache: {cache_param}")
        
        # Now fix the PolicyAnalyzer initialization
        # Find the line with model_override=model
        content = content.replace(
            'model_override=model,',
            f'model_override={model_param},' if model_param else 'model_override=None,'
        )
        content = content.replace(
            'analysis_depth=depth,',
            f'analysis_depth={depth_param},' if depth_param else 'analysis_depth="standard",'
        )
        content = content.replace(
            'use_cache=cache',
            f'use_cache={cache_param}' if cache_param else 'use_cache=True'
        )
        
        # Write fixed version
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ Fixed variable names in PolicyAnalyzer initialization")
        print("\nUpdated to:")
        print(f"  model_override={model_param}")
        print(f"  analysis_depth={depth_param}")
        print(f"  use_cache={cache_param}")
    else:
        print("❌ Could not parse parameters")
else:
    print("❌ Could not find __init__ method")

print("\n" + "="*70)
print("Now test with:")
print('python main.py --url "https://www.teladoc.com/privacy-policy/" --name "Teladoc" --model gpt4 --depth standard')