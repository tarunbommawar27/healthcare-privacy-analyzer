"""Risk scoring module for privacy policy analysis"""

from typing import Dict, List
from src.utils.logger import get_logger

logger = get_logger()


class RiskScorer:
    """Calculate risk scores for privacy policies"""

    def __init__(self, config: Dict):
        """
        Initialize scorer with configuration

        Args:
            config: Scoring configuration from config.yaml
        """
        self.scoring_config = config.get('scoring', {})
        self.weights = self.scoring_config.get('weights', {})
        self.thresholds = self.scoring_config.get('risk_thresholds', {})

    def score_category(self, category_name: str, findings: Dict) -> float:
        """
        Score individual category based on findings

        Args:
            category_name: Name of the category
            findings: Category findings from analysis

        Returns:
            Risk score (0-1, where 1 is highest risk)
        """
        # Check if LLM provided a score (0-100 scale)
        if 'score' in findings and findings['score'] is not None:
            llm_score = findings['score']
            if isinstance(llm_score, (int, float)):
                # Convert from 0-100 to 0-1 scale
                # Higher score from LLM = better (more transparent/protective)
                # So we invert it for risk: risk = (100 - score) / 100
                risk_score = (100 - float(llm_score)) / 100
                logger.debug(f"Using LLM score for {category_name}: {llm_score}/100 -> risk: {risk_score:.2f}")
                return max(0.0, min(1.0, risk_score))

        # Fallback to concerns-based scoring if no LLM score
        concerns = findings.get('concerns', [])
        positive_aspects = findings.get('positive_aspects', [])

        # Base scoring logic
        concern_count = len(concerns)
        positive_count = len(positive_aspects)

        # Higher concerns = higher risk
        # More positive aspects = lower risk
        if concern_count == 0 and positive_count > 0:
            return 0.1  # Very low risk
        elif concern_count == 0:
            return 0.3  # Low-medium risk (neutral)
        else:
            # Calculate risk based on concern-to-positive ratio
            base_score = min(concern_count / 5.0, 1.0)  # Cap at 1.0
            reduction = min(positive_count * 0.1, 0.3)  # Max 30% reduction
            return max(base_score - reduction, 0.1)

    def calculate_weighted_score(self, category_scores: Dict[str, float]) -> float:
        """
        Calculate overall weighted risk score

        Args:
            category_scores: Individual category scores

        Returns:
            Weighted overall score (0-1)
        """
        total_score = 0.0
        total_weight = 0.0

        # Map category names to config keys
        category_map = {
            'Data Collection': 'data_collection',
            'Data Usage': 'data_usage',
            'Third-Party Sharing': 'third_party_sharing',
            'Data Retention': 'data_retention',
            'User Rights': 'user_rights',
            'Security Measures': 'security_measures',
            'Healthcare Compliance': 'healthcare_compliance',
            'International Transfers': 'data_retention'  # Use retention weight as fallback
        }

        for category, score in category_scores.items():
            config_key = category_map.get(category, 'data_collection')
            weight = self.weights.get(config_key, 0.125)  # Default equal weight
            total_score += score * weight
            total_weight += weight

        # Normalize if weights don't sum to 1
        if total_weight > 0:
            return total_score / total_weight
        return 0.5  # Default medium risk if no scores

    def adjust_for_red_flags(self, base_score: float, red_flags: List[str]) -> float:
        """
        Adjust score based on detected red flags

        Args:
            base_score: Base risk score
            red_flags: List of detected red flags

        Returns:
            Adjusted score
        """
        # Each red flag increases risk by 5%, max 30% increase
        adjustment = min(len(red_flags) * 0.05, 0.30)
        adjusted = min(base_score + adjustment, 1.0)

        logger.info(f"Red flags detected: {len(red_flags)}, adjustment: +{adjustment:.2f}")
        return adjusted

    def get_risk_level(self, score: float) -> str:
        """
        Get risk level label based on score

        Args:
            score: Risk score (0-1)

        Returns:
            Risk level string
        """
        low_threshold = self.thresholds.get('low', 0.3)
        medium_threshold = self.thresholds.get('medium', 0.6)
        high_threshold = self.thresholds.get('high', 0.8)

        if score < low_threshold:
            return "LOW"
        elif score < medium_threshold:
            return "MEDIUM"
        elif score < high_threshold:
            return "HIGH"
        else:
            return "CRITICAL"

    def get_risk_color(self, risk_level: str) -> str:
        """
        Get color code for risk level visualization

        Args:
            risk_level: Risk level string

        Returns:
            Color code
        """
        colors = {
            "LOW": "#4CAF50",      # Green
            "MEDIUM": "#FFC107",   # Yellow
            "HIGH": "#FF9800",     # Orange
            "CRITICAL": "#F44336"  # Red
        }
        return colors.get(risk_level, "#9E9E9E")

    def calculate_risk_score(self, analysis: Dict) -> Dict:
        """
        Calculate comprehensive risk score from analysis

        Args:
            analysis: Analysis results from PolicyAnalyzer

        Returns:
            Risk scoring results
        """
        logger.info("Calculating risk scores")

        if 'error' in analysis:
            return {
                'overall_score': 0.5,
                'risk_level': 'UNKNOWN',
                'error': analysis['error']
            }

        categories = analysis.get('categories', {})
        red_flags = analysis.get('red_flags_detected', [])

        # Also check for red_flags (new format)
        if not red_flags:
            red_flags = analysis.get('red_flags', [])

        logger.debug(f"Categories found: {list(categories.keys())}")
        logger.debug(f"Red flags count: {len(red_flags)}")

        # Score each category
        category_scores = {}
        for category_name, findings in categories.items():
            score = self.score_category(category_name, findings)
            category_scores[category_name] = score
            logger.debug(f"{category_name}: {score:.2f}")

        # Calculate weighted overall score
        base_score = self.calculate_weighted_score(category_scores)

        # Adjust for red flags
        overall_score = self.adjust_for_red_flags(base_score, red_flags)

        # Determine risk level
        risk_level = self.get_risk_level(overall_score)

        result = {
            'overall_score': round(overall_score, 2),
            'base_score': round(base_score, 2),
            'risk_level': risk_level,
            'risk_color': self.get_risk_color(risk_level),
            'category_scores': {k: round(v, 2) for k, v in category_scores.items()},
            'red_flags_count': len(red_flags),
            'red_flags': red_flags
        }

        logger.info(f"Risk score calculated: {overall_score:.2f} ({risk_level})")
        return result
