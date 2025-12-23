"""Enhanced LLM-based analysis module for privacy policies with advanced features"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import tiktoken
from openai import OpenAI
from anthropic import Anthropic
from src.utils.logger import get_logger
from src.utils.file_handler import FileHandler

logger = get_logger()


class PolicyPreprocessor:
    """Preprocess privacy policies for better analysis"""

    @staticmethod
    def extract_structure(policy_text: str) -> Dict:
        """
        Extract structural information from policy

        Args:
            policy_text: Raw policy text

        Returns:
            Dictionary with structure information
        """
        lines = policy_text.split('\n')
        headers = []

        # Simple header detection (lines that are short, capitalized, or numbered)
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean and len(line_clean) < 100:
                # Check if it looks like a header
                if (line_clean.isupper() or
                    line_clean[0].isdigit() or
                    line_clean.endswith(':') or
                    any(keyword in line_clean.lower() for keyword in
                        ['introduction', 'collection', 'usage', 'sharing', 'retention',
                         'rights', 'security', 'contact', 'changes', 'compliance'])):
                    headers.append({
                        'line': i,
                        'text': line_clean,
                        'level': PolicyPreprocessor._estimate_header_level(line_clean)
                    })

        return {
            'total_lines': len(lines),
            'headers': headers,
            'estimated_sections': len(headers)
        }

    @staticmethod
    def _estimate_header_level(text: str) -> int:
        """Estimate header level (1-3)"""
        if text.isupper():
            return 1
        elif text[0].isdigit():
            return 2
        else:
            return 3

    @staticmethod
    def chunk_policy(policy_text: str, max_tokens: int = 6000) -> List[Dict]:
        """
        Intelligently chunk long policies

        Args:
            policy_text: Full policy text
            max_tokens: Maximum tokens per chunk

        Returns:
            List of chunks with metadata
        """
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            tokens = encoding.encode(policy_text)

            if len(tokens) <= max_tokens:
                return [{'text': policy_text, 'chunk_id': 0, 'total_chunks': 1}]

            # Split into chunks at section boundaries when possible
            structure = PolicyPreprocessor.extract_structure(policy_text)
            lines = policy_text.split('\n')

            chunks = []
            current_chunk = []
            current_tokens = 0
            chunk_id = 0

            for i, line in enumerate(lines):
                line_tokens = len(encoding.encode(line))

                # Check if adding this line would exceed limit
                if current_tokens + line_tokens > max_tokens and current_chunk:
                    # Save current chunk
                    chunks.append({
                        'text': '\n'.join(current_chunk),
                        'chunk_id': chunk_id,
                        'total_chunks': -1  # Will update later
                    })
                    chunk_id += 1
                    current_chunk = []
                    current_tokens = 0

                current_chunk.append(line)
                current_tokens += line_tokens

            # Add final chunk
            if current_chunk:
                chunks.append({
                    'text': '\n'.join(current_chunk),
                    'chunk_id': chunk_id,
                    'total_chunks': -1
                })

            # Update total_chunks
            total = len(chunks)
            for chunk in chunks:
                chunk['total_chunks'] = total

            return chunks

        except Exception as e:
            logger.warning(f"Chunking failed, returning full text: {str(e)}")
            return [{'text': policy_text, 'chunk_id': 0, 'total_chunks': 1}]


class PolicyAnalyzer:
    """Enhanced analyzer for privacy policies with multi-model support and advanced features"""

    def __init__(self, config: Dict, model_override: Optional[str] = None,
                 analysis_depth: str = 'standard', use_cache: bool = True):
        """
        Initialize enhanced analyzer

        Args:
            config: LLM and analysis configuration
            model_override: Override model from config ('claude', 'gpt4', 'auto')
            analysis_depth: Analysis depth ('quick', 'standard', 'deep')
            use_cache: Whether to use response caching
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        self.analysis_config = config.get('analysis', {})
        self.analysis_depth = analysis_depth
        self.use_cache = use_cache

        # Model configuration with fallback support
        self.primary_provider, self.primary_model = self._setup_models(model_override)
        self.fallback_provider, self.fallback_model = self._setup_fallback()

        self.temperature = self.llm_config.get('temperature', 0.3)
        self.max_tokens = self._get_max_tokens_for_depth()

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()

        # Setup caching
        self.cache_dir = Path(config.get('paths', {}).get('cache', 'data/cache'))
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"Analyzer initialized: {self.primary_provider}/{self.primary_model} "
                   f"(fallback: {self.fallback_provider}/{self.fallback_model})")

    def _setup_models(self, override: Optional[str]) -> Tuple[str, str]:
        """Setup primary model based on override or config"""
        if override == 'claude':
            return 'anthropic', 'claude-sonnet-4-20250514'
        elif override == 'gpt4':
            return 'openai', 'gpt-4-turbo-preview'
        elif override == 'auto':
            # Auto-select based on available API keys
            if os.getenv('ANTHROPIC_API_KEY'):
                return 'anthropic', 'claude-sonnet-4-20250514'
            elif os.getenv('OPENAI_API_KEY'):
                return 'openai', 'gpt-4-turbo-preview'

        # Use config
        provider = self.llm_config.get('provider', 'anthropic')
        model = self.llm_config.get('model', 'claude-sonnet-4-20250514')
        return provider, model

    def _setup_fallback(self) -> Tuple[str, str]:
        """Setup fallback model"""
        if self.primary_provider == 'anthropic':
            return 'openai', 'gpt-4-turbo-preview'
        else:
            return 'anthropic', 'claude-sonnet-4-20250514'

    def _initialize_clients(self):
        """Initialize API clients for available providers"""
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key.startswith('sk-'):
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")

        try:
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key and anthropic_key.startswith('sk-ant-'):
                self.anthropic_client = Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
        except Exception as e:
            logger.warning(f"Anthropic client initialization failed: {e}")

    def _get_max_tokens_for_depth(self) -> int:
        """Get max tokens based on analysis depth and model limits"""
        # Model-specific max completion token limits
        model_limits = {
            'gpt-4-turbo-preview': 4096,
            'gpt-4': 4096,
            'gpt-4-32k': 4096,
            'gpt-3.5-turbo': 4096,
            'claude-sonnet-4-20250514': 8192,
            'claude-3-5-sonnet-20241022': 8192,
            'claude-3-opus-20240229': 4096
        }

        # Desired tokens by depth
        depths = {
            'quick': 3000,
            'standard': 6000,
            'deep': 12000
        }

        desired_tokens = depths.get(self.analysis_depth, 6000)
        model_limit = model_limits.get(self.primary_model, 4096)

        # Return the minimum of desired and model limit
        actual_tokens = min(desired_tokens, model_limit)

        # Log if tokens are being capped
        if actual_tokens < desired_tokens:
            logger.info(
                f"max_tokens capped at {actual_tokens} (model limit) "
                f"instead of {desired_tokens} (depth: {self.analysis_depth})"
            )

        return actual_tokens

    def _get_cache_key(self, policy_text: str, depth: str) -> str:
        """Generate cache key for policy"""
        content = f"{policy_text}_{depth}_{self.primary_model}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load analysis from cache"""
        if not self.use_cache:
            return None

        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache_hits += 1
                    logger.info(f"Cache hit: {cache_key[:16]}...")
                    return data
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")

        self.cache_misses += 1
        return None

    def _save_to_cache(self, cache_key: str, analysis: Dict):
        """Save analysis to cache"""
        if not self.use_cache:
            return

        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2)
            logger.info(f"Saved to cache: {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def _create_enhanced_prompt(self, policy_text: str, structure: Dict) -> str:
        """
        Create sophisticated analysis prompt with chain-of-thought reasoning

        Args:
            policy_text: Privacy policy text
            structure: Structural information about the policy

        Returns:
            Enhanced prompt
        """
        prompt_templates = {
            'quick': self._get_quick_prompt(),
            'standard': self._get_standard_prompt(),
            'deep': self._get_deep_prompt()
        }

        template = prompt_templates.get(self.analysis_depth, self._get_standard_prompt())

        # Add structure information if available
        structure_info = ""
        if structure.get('headers'):
            structure_info = "\n\nDOCUMENT STRUCTURE:\n"
            structure_info += f"Total sections identified: {len(structure['headers'])}\n"
            structure_info += "Main sections:\n"
            for header in structure['headers'][:10]:  # First 10 headers
                structure_info += f"  - {header['text']}\n"

        return template.format(
            policy_text=policy_text,
            structure_info=structure_info
        )

    def _get_deep_prompt(self) -> str:
        """Get prompt for deep analysis"""
        return """You are a privacy and security expert specializing in healthcare applications and HIPAA compliance.
Analyze the following privacy policy using chain-of-thought reasoning.

PRIVACY POLICY TEXT:
{policy_text}
{structure_info}

ANALYSIS INSTRUCTIONS:

Use the following reasoning process:

STEP 1: STAKEHOLDER IDENTIFICATION
First, identify ALL stakeholders mentioned in this policy:
- Patients/users (primary data subjects)
- Healthcare providers/practitioners
- Insurance companies/payers
- Third-party service providers
- Analytics/advertising partners
- Government entities/regulatory bodies
- Business associates (HIPAA context)

STEP 2: DATA FLOW ANALYSIS
Map how data flows between stakeholders:
- What data is collected from users?
- What data is shared with each stakeholder?
- What is the stated purpose for each data share?
- Are there any implied but not explicitly stated data flows?

STEP 3: CONSENT MECHANISM ANALYSIS
Examine consent practices:
- Is consent explicit (opt-in) or implicit (opt-out)?
- Can users granularly control different types of data sharing?
- Are pre-checked boxes or automatic consent used?
- How clear is the consent language?

STEP 4: LANGUAGE ANALYSIS
Identify euphemistic or vague language:
- Terms like "may share", "partners", "business purposes", "affiliates"
- Phrases that obscure actual practices
- Contradictions or ambiguous statements
- Technical jargon that obscures meaning

STEP 5: MISSING INFORMATION DETECTION
Flag critical information that is NOT mentioned or is vague:
- Data retention periods
- Specific third parties by name
- Security breach notification timelines
- User rights implementation details
- International transfer mechanisms

STEP 6: HIPAA COMPLIANCE ASSESSMENT
Evaluate HIPAA compliance claims:
- Is HIPAA explicitly mentioned?
- Are Protected Health Information (PHI) safeguards described?
- Business Associate Agreements referenced?
- Minimum necessary standard discussed?
- Patient rights under HIPAA listed?
- Compare claims vs. actual practices described

STEP 7: READABILITY FOR OLDER ADULTS
Assess accessibility for vulnerable populations:
- Reading level (grade level estimate)
- Use of complex legal jargon vs. plain language
- Sentence complexity and length
- Availability of simplified versions
- Specific mentions of accommodations

STEP 8: SYNTHESIS
Synthesize findings into scores and structured output.

REQUIRED OUTPUT FORMAT (strict JSON):
{{
  "summary": "2-3 sentence executive summary highlighting most critical findings",
  "data_collection": {{
    "types_collected": ["specific data types listed"],
    "collection_methods": ["automatic", "user-provided", "third-party sources"],
    "sensitive_data_handling": "detailed analysis of PHI/PII handling practices",
    "concerns": ["specific concerning practices with details"],
    "positive_aspects": ["good practices identified"],
    "score": 0-100
  }},
  "data_usage": {{
    "stated_purposes": ["list all purposes mentioned"],
    "concerning_uses": ["uses that may concern users"],
    "user_control": "what control users have over usage",
    "concerns": ["specific issues"],
    "positive_aspects": ["good practices"],
    "score": 0-100
  }},
  "third_party_sharing": {{
    "partners_mentioned": ["list all third parties by name or category"],
    "purposes": ["why data is shared with each"],
    "user_control": "opt-out mechanisms, if any",
    "data_flows": ["describe specific data flows identified"],
    "concerns": ["specific concerning practices"],
    "positive_aspects": ["good practices"],
    "score": 0-100
  }},
  "data_retention": {{
    "duration_specified": true or false,
    "retention_period": "specific timeframe or 'unspecified' or 'indefinite'",
    "deletion_process": "how users can request deletion",
    "deletion_timeline": "how long deletion takes",
    "concerns": ["issues with retention"],
    "positive_aspects": ["good practices"],
    "score": 0-100
  }},
  "user_rights": {{
    "access_rights": "detailed description of data access rights",
    "deletion_rights": "right to delete data",
    "portability": "can users export their data",
    "opt_out_mechanisms": ["list all opt-out methods"],
    "consent_management": "how consent is obtained and managed",
    "concerns": ["rights that are missing or limited"],
    "positive_aspects": ["strong user rights"],
    "score": 0-100
  }},
  "security_measures": {{
    "technical_safeguards": ["encryption at rest", "encryption in transit", "access controls", etc.],
    "organizational_safeguards": ["staff training", "audits", "policies"],
    "breach_notification": "how and when users are notified of breaches",
    "specific_technologies": ["any specific security tech mentioned"],
    "concerns": ["security weaknesses or vague claims"],
    "positive_aspects": ["strong security practices"],
    "score": 0-100
  }},
  "compliance": {{
    "hipaa_mentioned": true or false,
    "hipaa_compliance_details": "what they claim about HIPAA compliance",
    "gdpr_mentioned": true or false,
    "other_regulations": ["CCPA", "HITECH", "state laws", etc.],
    "business_associate_agreement": "mentioned or not",
    "concerns": ["compliance gaps or questionable claims"],
    "positive_aspects": ["strong compliance posture"],
    "score": 0-100
  }},
  "older_adult_considerations": {{
    "readability_score": "estimated grade level (e.g., '12th grade', 'college level')",
    "readability_assessment": "analysis of language complexity",
    "accessibility_features": "large print, audio versions, simplified versions mentioned",
    "specific_protections": "mentions of vulnerable populations",
    "concerns": ["accessibility barriers"],
    "positive_aspects": ["good accessibility features"],
    "score": 0-100
  }},
  "red_flags": [
    {{
      "category": "category name",
      "severity": "high" or "medium" or "low",
      "description": "specific concerning practice in detail",
      "quote": "exact text from policy that demonstrates this",
      "location": "section name or paragraph indicator",
      "impact": "why this matters for users"
    }}
  ],
  "positive_practices": [
    {{
      "category": "category name",
      "description": "what they do well",
      "quote": "supporting text from policy",
      "impact": "why this benefits users"
    }}
  ],
  "missing_information": [
    "specific critical information not included"
  ],
  "contradictions": [
    {{
      "description": "description of contradiction",
      "locations": ["section 1", "section 2"]
    }}
  ],
  "vague_language_examples": [
    {{
      "quote": "exact vague phrase",
      "concern": "why this is problematic",
      "location": "where found"
    }}
  ],
  "quotable_findings": [
    {{
      "category": "category",
      "finding": "research-worthy finding",
      "quote": "exact quote suitable for research paper",
      "significance": "why this is notable"
    }}
  ],
  "overall_transparency_score": 0-100,
  "confidence_score": 0-100,
  "metadata": {{
    "analysis_date": "ISO timestamp",
    "policy_length": 0,
    "sections_analyzed": 0
  }}
}}

SCORING GUIDANCE:
- 90-100: Excellent practices, very protective of user privacy
- 70-89: Good practices with minor concerns
- 50-69: Average with notable concerns
- 30-49: Poor practices, significant concerns
- 0-29: Severe privacy issues, highly concerning

Be thorough, specific, and cite exact quotes. Identify at least 3-5 red flags if present, and 2-3 positive practices.
Ensure ALL JSON fields are present and properly formatted."""

    def _get_standard_prompt(self) -> str:
        """Get prompt for standard analysis"""
        return """You are a privacy and security expert specializing in healthcare applications.
Analyze the following privacy policy comprehensively.

PRIVACY POLICY TEXT:
{policy_text}
{structure_info}

Analyze this policy systematically across all categories. Identify stakeholders, data flows, consent mechanisms,
vague language, missing information, and HIPAA compliance. Assess readability for older adults.

Provide analysis in this EXACT JSON format:
{{
  "summary": "2-3 sentence overview",
  "data_collection": {{
    "types_collected": [],
    "collection_methods": [],
    "sensitive_data_handling": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "data_usage": {{
    "stated_purposes": [],
    "concerning_uses": [],
    "user_control": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "third_party_sharing": {{
    "partners_mentioned": [],
    "purposes": [],
    "user_control": "",
    "data_flows": [],
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "data_retention": {{
    "duration_specified": true/false,
    "retention_period": "",
    "deletion_process": "",
    "deletion_timeline": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "user_rights": {{
    "access_rights": "",
    "deletion_rights": "",
    "portability": "",
    "opt_out_mechanisms": [],
    "consent_management": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "security_measures": {{
    "technical_safeguards": [],
    "organizational_safeguards": [],
    "breach_notification": "",
    "specific_technologies": [],
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "compliance": {{
    "hipaa_mentioned": true/false,
    "hipaa_compliance_details": "",
    "gdpr_mentioned": true/false,
    "other_regulations": [],
    "business_associate_agreement": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "older_adult_considerations": {{
    "readability_score": "",
    "readability_assessment": "",
    "accessibility_features": "",
    "specific_protections": "",
    "concerns": [],
    "positive_aspects": [],
    "score": 0-100
  }},
  "red_flags": [
    {{
      "category": "",
      "severity": "high/medium/low",
      "description": "",
      "quote": "",
      "location": "",
      "impact": ""
    }}
  ],
  "positive_practices": [
    {{
      "category": "",
      "description": "",
      "quote": "",
      "impact": ""
    }}
  ],
  "missing_information": [],
  "contradictions": [],
  "vague_language_examples": [
    {{
      "quote": "",
      "concern": "",
      "location": ""
    }}
  ],
  "quotable_findings": [
    {{
      "category": "",
      "finding": "",
      "quote": "",
      "significance": ""
    }}
  ],
  "overall_transparency_score": 0-100,
  "confidence_score": 0-100,
  "metadata": {{
    "analysis_date": "ISO timestamp",
    "policy_length": 0,
    "sections_analyzed": 0
  }}
}}

Be specific and cite exact quotes. Score each category 0-100."""

    def _get_quick_prompt(self) -> str:
        """Get prompt for quick analysis"""
        return """You are a privacy expert. Quickly analyze this healthcare privacy policy.

PRIVACY POLICY TEXT:
{policy_text}

Provide a focused analysis in JSON format with key findings, red flags, and scores for each category.
Use the same JSON structure as standard analysis but focus on most critical issues."""

    def analyze_with_anthropic(self, policy_text: str, structure: Dict) -> Dict:
        """
        Analyze policy using Anthropic Claude with enhanced prompting

        Args:
            policy_text: Privacy policy text
            structure: Structural information

        Returns:
            Analysis results
        """
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Check API key.")

        try:
            start_time = time.time()
            prompt = self._create_enhanced_prompt(policy_text, structure)

            logger.info(f"Calling Anthropic Claude ({self.primary_model})...")

            response = self.anthropic_client.messages.create(
                model=self.primary_model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            analysis_time = time.time() - start_time

            # Extract JSON from response
            content = response.content[0].text

            # Find JSON in response
            start = content.find('{')
            end = content.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")

            json_str = content[start:end]
            result = json.loads(json_str)

            # Add metadata
            if 'metadata' not in result:
                result['metadata'] = {}

            result['metadata'].update({
                'analysis_date': datetime.now().isoformat(),
                'model_used': self.primary_model,
                'provider': 'anthropic',
                'analysis_time_seconds': round(analysis_time, 2),
                'policy_length': len(policy_text),
                'analysis_depth': self.analysis_depth
            })

            # Validate response
            self._validate_analysis(result)

            logger.info(f"Anthropic analysis completed in {analysis_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Anthropic analysis failed: {str(e)}")
            raise

    def analyze_with_openai(self, policy_text: str, structure: Dict) -> Dict:
        """
        Analyze policy using OpenAI with enhanced prompting

        Args:
            policy_text: Privacy policy text
            structure: Structural information

        Returns:
            Analysis results
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        try:
            start_time = time.time()
            prompt = self._create_enhanced_prompt(policy_text, structure)

            logger.info(f"Calling OpenAI ({self.primary_model})...")

            response = self.openai_client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a privacy and security expert specializing in healthcare applications and HIPAA compliance. Provide comprehensive analysis in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            analysis_time = time.time() - start_time

            result = json.loads(response.choices[0].message.content)

            # Add metadata
            if 'metadata' not in result:
                result['metadata'] = {}

            result['metadata'].update({
                'analysis_date': datetime.now().isoformat(),
                'model_used': self.primary_model,
                'provider': 'openai',
                'analysis_time_seconds': round(analysis_time, 2),
                'policy_length': len(policy_text),
                'analysis_depth': self.analysis_depth,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
            })

            # Validate response
            self._validate_analysis(result)

            logger.info(f"OpenAI analysis completed in {analysis_time:.2f}s")
            return result

        except Exception as e:
            import traceback
            logger.error(f"OpenAI analysis failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _validate_analysis(self, analysis: Dict) -> bool:
        """
        Validate analysis result has required fields and valid values

        Args:
            analysis: Analysis dictionary

        Returns:
            True if valid

        Raises:
            ValueError if validation fails
        """
        required_categories = [
            'data_collection', 'data_usage', 'third_party_sharing',
            'data_retention', 'user_rights', 'security_measures',
            'compliance', 'older_adult_considerations'
        ]

        # Check required top-level fields
        if 'summary' not in analysis:
            logger.warning("Missing 'summary' field")

        # Check categories
        for category in required_categories:
            if category not in analysis:
                logger.warning(f"Missing category: {category}")
                # Add empty category
                analysis[category] = {
                    'concerns': [],
                    'positive_aspects': [],
                    'score': 50
                }

            # Validate score
            if 'score' in analysis[category]:
                score = analysis[category]['score']
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    logger.warning(f"Invalid score for {category}: {score}")
                    analysis[category]['score'] = 50

        # Ensure red_flags and positive_practices exist
        if 'red_flags' not in analysis:
            analysis['red_flags'] = []
        if 'positive_practices' not in analysis:
            analysis['positive_practices'] = []

        # Check minimum content
        total_items = len(analysis.get('red_flags', [])) + len(analysis.get('positive_practices', []))
        if total_items < 3:
            logger.warning(f"Analysis seems sparse: only {total_items} red flags + positive practices")

        return True

    def analyze_policy(self, policy_text: str, force_reanalyze: bool = False) -> Dict:
        """
        Analyze privacy policy with multi-model support, caching, and fallback

        Args:
            policy_text: Privacy policy text to analyze
            force_reanalyze: Bypass cache and force new analysis

        Returns:
            Comprehensive analysis results
        """
        if not policy_text or len(policy_text.strip()) < 100:
            logger.warning("Policy text too short or empty")
            return {
                'error': 'Policy text too short or empty',
                'summary': 'Unable to analyze - insufficient text',
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'policy_length': len(policy_text) if policy_text else 0
                }
            }

        # Check cache
        cache_key = self._get_cache_key(policy_text, self.analysis_depth)
        if not force_reanalyze:
            cached = self._load_from_cache(cache_key)
            if cached:
                logger.info("Returning cached analysis")
                return cached

        # Preprocess policy
        logger.info("Preprocessing policy...")
        structure = PolicyPreprocessor.extract_structure(policy_text)

        # Check if chunking needed
        chunks = PolicyPreprocessor.chunk_policy(policy_text, max_tokens=6000)

        if len(chunks) > 1:
            logger.info(f"Policy requires {len(chunks)} chunks for analysis")
            analysis = self._analyze_chunks(chunks, structure)
        else:
            analysis = self._analyze_single(policy_text, structure)

        # Save to cache
        if not force_reanalyze and analysis and 'error' not in analysis:
            self._save_to_cache(cache_key, analysis)

        return analysis

    def _analyze_single(self, policy_text: str, structure: Dict) -> Dict:
        """Analyze single policy (not chunked)"""
        try:
            # Try primary model
            if self.primary_provider == 'anthropic':
                return self.analyze_with_anthropic(policy_text, structure)
            else:
                return self.analyze_with_openai(policy_text, structure)

        except Exception as e:
            logger.error(f"Primary model failed: {str(e)}")

            # Try fallback
            logger.info(f"Attempting fallback to {self.fallback_provider}...")
            try:
                if self.fallback_provider == 'anthropic':
                    # Temporarily switch to fallback
                    old_model = self.primary_model
                    self.primary_model = self.fallback_model
                    result = self.analyze_with_anthropic(policy_text, structure)
                    self.primary_model = old_model
                    return result
                else:
                    old_model = self.primary_model
                    self.primary_model = self.fallback_model
                    result = self.analyze_with_openai(policy_text, structure)
                    self.primary_model = old_model
                    return result

            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {str(fallback_error)}")
                return {
                    'error': f'Both primary and fallback models failed. Primary: {str(e)}, Fallback: {str(fallback_error)}',
                    'summary': 'Analysis failed - all models unavailable',
                    'metadata': {
                        'analysis_date': datetime.now().isoformat(),
                        'policy_length': len(policy_text)
                    }
                }

    def _analyze_chunks(self, chunks: List[Dict], structure: Dict) -> Dict:
        """Analyze policy in chunks and synthesize results"""
        logger.info(f"Analyzing {len(chunks)} chunks...")

        chunk_analyses = []
        for chunk in chunks:
            try:
                chunk_analysis = self._analyze_single(chunk['text'], structure)
                chunk_analyses.append(chunk_analysis)
            except Exception as e:
                logger.error(f"Chunk {chunk['chunk_id']} failed: {e}")
                continue

        if not chunk_analyses:
            return {
                'error': 'All chunks failed to analyze',
                'summary': 'Analysis failed',
                'metadata': {
                    'analysis_date': datetime.now().isoformat()
                }
            }

        # Synthesize results
        return self._synthesize_chunk_analyses(chunk_analyses)

    def _synthesize_chunk_analyses(self, analyses: List[Dict]) -> Dict:
        """Combine multiple chunk analyses into one"""
        logger.info(f"Synthesizing {len(analyses)} chunk analyses...")

        # Combine scores (average)
        categories = ['data_collection', 'data_usage', 'third_party_sharing',
                     'data_retention', 'user_rights', 'security_measures',
                     'compliance', 'older_adult_considerations']

        synthesized = {
            'summary': ' '.join([a.get('summary', '') for a in analyses]),
            'red_flags': [],
            'positive_practices': [],
            'missing_information': [],
            'quotable_findings': [],
            'metadata': analyses[0].get('metadata', {})
        }

        # Combine category data
        for category in categories:
            scores = [a.get(category, {}).get('score', 50) for a in analyses if category in a]
            avg_score = sum(scores) / len(scores) if scores else 50

            all_concerns = []
            all_positives = []

            for a in analyses:
                if category in a:
                    all_concerns.extend(a[category].get('concerns', []))
                    all_positives.extend(a[category].get('positive_aspects', []))

            synthesized[category] = {
                'concerns': list(set(all_concerns))[:10],  # Dedupe and limit
                'positive_aspects': list(set(all_positives))[:10],
                'score': round(avg_score, 0)
            }

            # Copy other fields from first chunk
            if category in analyses[0]:
                for key, value in analyses[0][category].items():
                    if key not in ['concerns', 'positive_aspects', 'score']:
                        synthesized[category][key] = value

        # Combine red flags and positive practices
        for a in analyses:
            synthesized['red_flags'].extend(a.get('red_flags', []))
            synthesized['positive_practices'].extend(a.get('positive_practices', []))
            synthesized['missing_information'].extend(a.get('missing_information', []))
            synthesized['quotable_findings'].extend(a.get('quotable_findings', []))

        # Calculate overall transparency score
        all_scores = [synthesized[cat]['score'] for cat in categories if cat in synthesized]
        synthesized['overall_transparency_score'] = round(sum(all_scores) / len(all_scores)) if all_scores else 50
        synthesized['confidence_score'] = 75  # Lower for chunked analysis

        synthesized['metadata']['chunked_analysis'] = True
        synthesized['metadata']['chunks_analyzed'] = len(analyses)

        return synthesized

    def estimate_cost(self, policy_text: str) -> Dict:
        """
        Estimate analysis cost

        Args:
            policy_text: Policy text

        Returns:
            Cost estimate dictionary
        """
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            input_tokens = len(encoding.encode(policy_text))

            # Estimate output tokens based on depth
            output_estimates = {
                'quick': 2000,
                'standard': 4000,
                'deep': 8000
            }
            output_tokens = output_estimates.get(self.analysis_depth, 4000)

            # Pricing (approximate, as of 2024)
            pricing = {
                'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},  # per 1K tokens
                'claude-sonnet-4-20250514': {'input': 0.003, 'output': 0.015}
            }

            model_pricing = pricing.get(self.primary_model, {'input': 0.01, 'output': 0.03})

            input_cost = (input_tokens / 1000) * model_pricing['input']
            output_cost = (output_tokens / 1000) * model_pricing['output']
            total_cost = input_cost + output_cost

            return {
                'input_tokens': input_tokens,
                'estimated_output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'estimated_cost_usd': round(total_cost, 4),
                'model': self.primary_model,
                'analysis_depth': self.analysis_depth
            }

        except Exception as e:
            logger.warning(f"Cost estimation failed: {e}")
            return {
                'estimated_cost_usd': 'unknown',
                'error': str(e)
            }

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_requests': total,
            'hit_rate_percent': round(hit_rate, 1),
            'cache_enabled': self.use_cache
        }
