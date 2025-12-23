"""Unit tests for scraper module"""

import pytest
from unittest.mock import Mock, patch
from src.modules.scraper import PolicyScraper


@pytest.fixture
def scraper_config():
    """Sample scraper configuration"""
    return {
        'timeout': 30,
        'user_agent': 'Mozilla/5.0',
        'max_retries': 3,
        'delay_between_requests': 1,
        'use_headless': True
    }


@pytest.fixture
def scraper(scraper_config):
    """Create PolicyScraper instance"""
    return PolicyScraper(scraper_config)


def test_scraper_initialization(scraper, scraper_config):
    """Test scraper initializes with correct config"""
    assert scraper.timeout == scraper_config['timeout']
    assert scraper.user_agent == scraper_config['user_agent']
    assert scraper.max_retries == scraper_config['max_retries']


@patch('src.modules.scraper.requests.get')
def test_scrape_with_requests_success(mock_get, scraper):
    """Test successful scraping with requests"""
    mock_response = Mock()
    mock_response.text = '<html><body><main>Privacy Policy Content</main></body></html>'
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    result = scraper.scrape_with_requests('https://example.com/privacy')

    assert result is not None
    assert 'Privacy Policy Content' in result
    mock_get.assert_called_once()


@patch('src.modules.scraper.requests.get')
def test_scrape_with_requests_failure(mock_get, scraper):
    """Test scraping failure handling"""
    mock_get.side_effect = Exception('Connection error')

    result = scraper.scrape_with_requests('https://example.com/privacy')

    assert result is None


def test_scrape_policy_returns_dict(scraper):
    """Test scrape_policy returns proper dictionary structure"""
    with patch.object(scraper, 'scrape_with_requests', return_value='Sample text'):
        result = scraper.scrape_policy('https://example.com/privacy')

        assert isinstance(result, dict)
        assert 'url' in result
        assert 'text' in result
        assert 'success' in result
        assert 'length' in result
        assert 'timestamp' in result
        assert result['success'] is True
