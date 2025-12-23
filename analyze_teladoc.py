"""
Standalone Privacy Policy Analyzer
Bypasses main.py to avoid datetime issue
"""

import os
import json
from datetime import datetime
from openai import OpenAI

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Read the scraped policy
with open('data/raw/Teladoc_raw_20251222_220953.txt', 'r', encoding='utf-8') as f:
    policy_text = f.read()

print("🔍 Analyzing Teladoc Privacy Policy...")
print(f"📄 Policy length: {len(policy_text):,} characters")

# Create analysis prompt
prompt = f"""You are a privacy policy expert. Analyze this healthcare app privacy policy and return a JSON object.

Privacy Policy Text:
{policy_text[:15000]}  

Return ONLY valid JSON with this exact structure:
{{
  "summary": "2-3 sentence overview",
  "data_collection": {{
    "score": 50,
    "types_collected": ["health data", "location", "device info"],
    "concerns": ["specific concern 1", "concern 2"]
  }},
  "data_usage": {{
    "score": 50,
    "purposes": ["treatment", "marketing"],
    "concerns": []
  }},
  "third_party_sharing": {{
    "score": 60,
    "partners_mentioned": ["insurance companies", "analytics"],
    "concerns": ["vague language about partners"]
  }},
  "data_retention": {{
    "score": 40,
    "retention_period": "unspecified",
    "concerns": ["no clear retention period"]
  }},
  "user_rights": {{
    "score": 55,
    "access_rights": "yes/no",
    "deletion_rights": "yes/no",
    "concerns": []
  }},
  "security_measures": {{
    "score": 60,
    "technical_safeguards": ["encryption"],
    "concerns": []
  }},
  "compliance": {{
    "score": 70,
    "hipaa_mentioned": true,
    "hipaa_compliance_details": "claims HIPAA compliance",
    "concerns": []
  }},
  "older_adult_considerations": {{
    "score": 30,
    "readability_score": "college level",
    "concerns": ["complex legal language"]
  }},
  "red_flags": [
    {{
      "category": "third_party_sharing",
      "severity": "high",
      "description": "Shares data with unspecified partners",
      "quote": "exact quote from policy"
    }}
  ],
  "positive_practices": [
    {{
      "category": "compliance",
      "description": "Mentions HIPAA compliance",
      "quote": "relevant quote"
    }}
  ],
  "overall_transparency_score": 55,
  "missing_information": ["retention period", "breach notification timeline"]
}}

Analyze scores from 0-100 where 100 = highest risk/worst privacy.
Include at least 3 red flags and 2 positive practices.
Return ONLY the JSON, no other text."""

print("💭 Calling OpenAI GPT-4...")

try:
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a privacy policy analysis expert. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    # Extract response
    result_text = response.choices[0].message.content
    
    # Clean up response (remove markdown if present)
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0]
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0]
    
    # Parse JSON
    result = json.loads(result_text.strip())
    
    # Calculate overall risk score
    category_scores = [
        result.get('data_collection', {}).get('score', 50),
        result.get('data_usage', {}).get('score', 50),
        result.get('third_party_sharing', {}).get('score', 50),
        result.get('data_retention', {}).get('score', 50),
        result.get('user_rights', {}).get('score', 50),
        result.get('security_measures', {}).get('score', 50),
        result.get('compliance', {}).get('score', 50),
        result.get('older_adult_considerations', {}).get('score', 50)
    ]
    overall_score = sum(category_scores) / len(category_scores)
    
    result['overall_risk_score'] = round(overall_score, 1)
    result['metadata'] = {
        'app_name': 'Teladoc',
        'analysis_date': datetime.now().isoformat(),
        'model': 'gpt-4-turbo-preview',
        'policy_length': len(policy_text)
    }
    
    print("\n✅ Analysis Complete!")
    print(f"📊 Overall Risk Score: {overall_score:.1f}/100")
    print(f"🚩 Red Flags: {len(result.get('red_flags', []))}")
    print(f"✨ Positive Practices: {len(result.get('positive_practices', []))}")
    
    # Save result
    output_file = f"outputs/reports/Teladoc_standalone_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(result.get('summary', 'No summary'))
    
    print("\n📊 CATEGORY SCORES:")
    print(f"  Data Collection: {result.get('data_collection', {}).get('score', 'N/A')}")
    print(f"  Third Party Sharing: {result.get('third_party_sharing', {}).get('score', 'N/A')}")
    print(f"  Data Retention: {result.get('data_retention', {}).get('score', 'N/A')}")
    print(f"  User Rights: {result.get('user_rights', {}).get('score', 'N/A')}")
    print(f"  Security: {result.get('security_measures', {}).get('score', 'N/A')}")
    print(f"  HIPAA Compliance: {result.get('compliance', {}).get('score', 'N/A')}")
    
    print("\n🚩 TOP RED FLAGS:")
    for i, flag in enumerate(result.get('red_flags', [])[:3], 1):
        print(f"  {i}. [{flag.get('severity', 'unknown').upper()}] {flag.get('description', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()