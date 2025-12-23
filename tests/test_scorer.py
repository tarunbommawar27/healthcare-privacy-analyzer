"""Unit tests for scorer module"""

import pytest
from src.modules.scorer import RiskScorer


@pytest.fixture
def scorer_config():
    """Sample scorer configuration"""
    return {
        'scoring': {
            'weights': {
                'data_collection': 0.15,
                'data_usage': 0.15,
                'third_party_sharing': 0.20,
                'data_retention': 0.15,
                'user_rights': 0.10,
                'security_measures': 0.15,
                'healthcare_compliance': 0.10
            },
            'risk_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            }
        }
    }


@pytest.fixture
def scorer(scorer_config):
    """Create RiskScorer instance"""
    return RiskScorer(scorer_config)


def test_scorer_initialization(scorer):
    """Test scorer initializes correctly"""
    assert scorer.weights is not None
    assert scorer.thresholds is not None


def test_score_category_no_concerns(scorer):
    """Test category scoring with no concerns"""
    findings = {
        'concerns': [],
        'positive_aspects': ['Good security', 'Clear policies']
    }

    score = scorer.score_category('Data Collection', findings)

    assert 0 <= score <= 1
    assert score < 0.3  # Should be low risk


def test_score_category_with_concerns(scorer):
    """Test category scoring with concerns"""
    findings = {
        'concerns': ['Shares data', 'No encryption', 'Vague terms'],
        'positive_aspects': []
    }

    score = scorer.score_category('Data Collection', findings)

    assert 0 <= score <= 1
    assert score > 0.3  # Should be medium/high risk


def test_get_risk_level_low(scorer):
    """Test risk level classification - LOW"""
    level = scorer.get_risk_level(0.2)
    assert level == "LOW"


def test_get_risk_level_medium(scorer):
    """Test risk level classification - MEDIUM"""
    level = scorer.get_risk_level(0.5)
    assert level == "MEDIUM"


def test_get_risk_level_high(scorer):
    """Test risk level classification - HIGH"""
    level = scorer.get_risk_level(0.7)
    assert level == "HIGH"


def test_get_risk_level_critical(scorer):
    """Test risk level classification - CRITICAL"""
    level = scorer.get_risk_level(0.9)
    assert level == "CRITICAL"


def test_adjust_for_red_flags(scorer):
    """Test red flag adjustment increases score"""
    base_score = 0.5
    red_flags = ['flag1', 'flag2', 'flag3']

    adjusted = scorer.adjust_for_red_flags(base_score, red_flags)

    assert adjusted > base_score
    assert adjusted <= 1.0


def test_calculate_risk_score_structure(scorer):
    """Test risk score calculation returns proper structure"""
    analysis = {
        'categories': {
            'Data Collection': {
                'concerns': ['concern1'],
                'positive_aspects': []
            }
        },
        'red_flags_detected': ['flag1']
    }

    result = scorer.calculate_risk_score(analysis)

    assert 'overall_score' in result
    assert 'risk_level' in result
    assert 'category_scores' in result
    assert 'red_flags_count' in result
