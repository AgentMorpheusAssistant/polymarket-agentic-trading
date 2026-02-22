"""
API Clients Package for Polymarket Agentic Trading System

Usage:
    from api_clients import PolymarketDataAggregator, NewsAPIClient, WhaleTracker
    
    async with PolymarketDataAggregator() as poly:
        markets = await poly.get_all_active_markets()
"""

from .base_client import BaseAPIClient, APIResponse, RateLimiter, APIHealthMonitor
from .polymarket_client import (
    PolymarketCLOBClient,
    PolymarketGammaClient,
    PolymarketDataAggregator
)
from .news_social_client import (
    NewsAPIClient,
    TwitterAPIClient,
    GDELTClient,
    SentimentAnalyzer
)
from .alt_data_client import (
    EtherscanClient,
    PolygonClient,
    WhaleTracker,
    OnChainMetrics
)

__all__ = [
    # Base
    'BaseAPIClient',
    'APIResponse',
    'RateLimiter',
    'APIHealthMonitor',
    # Polymarket
    'PolymarketCLOBClient',
    'PolymarketGammaClient',
    'PolymarketDataAggregator',
    # News & Social
    'NewsAPIClient',
    'TwitterAPIClient',
    'GDELTClient',
    'SentimentAnalyzer',
    # Alternative Data
    'EtherscanClient',
    'PolygonClient',
    'WhaleTracker',
    'OnChainMetrics',
]
