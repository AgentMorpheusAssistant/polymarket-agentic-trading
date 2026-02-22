"""
Real-Time Data Ingestion Layer (Layer 0)
Uses actual API connections instead of simulated data
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any

# Import from our API clients
try:
    from api_clients import (
        PolymarketDataAggregator,
        NewsAPIClient,
        GDELTClient,
        TwitterAPIClient,
        WhaleTracker,
        OnChainMetrics,
        SentimentAnalyzer
    )
    API_CLIENTS_AVAILABLE = True
except ImportError:
    API_CLIENTS_AVAILABLE = False
    print("Warning: API clients not available. Install required packages.")


class RealTimeDataIngestion:
    """
    Layer 0: Real-time data ingestion using live APIs
    Falls back to simulation if APIs unavailable
    """
    
    def __init__(self, event_bus, data_store, use_real_apis: bool = True):
        self.event_bus = event_bus
        self.data_store = data_store
        self.running = False
        self.use_real_apis = use_real_apis and API_CLIENTS_AVAILABLE
        
        # API clients (initialized in start())
        self.polymarket = None
        self.news_client = None
        self.twitter_client = None
        self.whale_tracker = None
        self.onchain_metrics = None
        self.gdelt = None
        
        # Tracking
        self.ingestion_stats = {
            "polymarket": 0,
            "news": 0,
            "social": 0,
            "whale": 0,
            "errors": 0
        }
        
    async def start(self):
        """Initialize API clients and start ingestion"""
        self.running = True
        
        if self.use_real_apis:
            print("🔄 LAYER 0: Initializing real API connections...")
            await self._init_api_clients()
            
            # Start real data ingestion
            await asyncio.gather(
                self._ingest_polymarket_real(),
                self._ingest_news_real(),
                self._ingest_whale_data_real(),
                self._ingest_social_real(),
            )
        else:
            print("🔄 LAYER 0: Using simulated data (APIs not configured)")
            await self._ingest_simulated()
            
    async def _init_api_clients(self):
        """Initialize all API clients"""
        try:
            self.polymarket = PolymarketDataAggregator()
            await self.polymarket.__aenter__()
            print("  ✅ Polymarket API connected")
        except Exception as e:
            print(f"  ❌ Polymarket API failed: {e}")
            self.polymarket = None
            
        try:
            self.news_client = NewsAPIClient()
            await self.news_client.__aenter__()
            print("  ✅ News API connected")
        except Exception as e:
            print(f"  ❌ News API failed: {e}")
            self.news_client = None
            
        try:
            self.gdelt = GDELTClient()
            print("  ✅ GDELT API connected (no key needed)")
        except Exception as e:
            print(f"  ❌ GDELT failed: {e}")
            self.gdelt = None
            
        try:
            self.twitter_client = TwitterAPIClient()
            await self.twitter_client.__aenter__()
            print("  ✅ Twitter API connected")
        except Exception as e:
            print(f"  ❌ Twitter API failed: {e}")
            self.twitter_client = None
            
        try:
            self.whale_tracker = WhaleTracker()
            await self.whale_tracker.__aenter__()
            print("  ✅ Whale Tracker connected")
        except Exception as e:
            print(f"  ❌ Whale Tracker failed: {e}")
            self.whale_tracker = None
            
    async def _ingest_polymarket_real(self):
        """Real Polymarket data ingestion"""
        if not self.polymarket:
            return
            
        print("📊 Polymarket ingestion started")
        
        while self.running:
            try:
                # Get high volume markets
                markets = await self.polymarket.get_high_volume_markets(min_volume=100000)
                
                for market in markets[:5]:  # Top 5 markets
                    event = {
                        "id": "",
                        "timestamp": datetime.now(),
                        "event_type": "clob_update",
                        "source": "polymarket_real",
                        "layer": "Layer0",
                        "data": {
                            "market_id": market.get("id"),
                            "question": market.get("question"),
                            "volume": market.get("volume"),
                            "liquidity": market.get("liquidity"),
                            "outcomes": market.get("outcomes"),
                            "end_date": market.get("end_date")
                        }
                    }
                    
                    # Store time series
                    self.data_store.ts_insert(
                        f"volume_{market.get('id')}",
                        event["timestamp"],
                        market.get("volume", 0),
                        {"liquidity": market.get("liquidity")}
                    )
                    
                    await self.event_bus.publish(event)
                    self.ingestion_stats["polymarket"] += 1
                    
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                print(f"  ❌ Polymarket error: {e}")
                self.ingestion_stats["errors"] += 1
                await asyncio.sleep(120)
                
    async def _ingest_news_real(self):
        """Real news ingestion"""
        print("📰 News ingestion started")
        
        while self.running:
            try:
                articles = []
                
                # Try NewsAPI
                if self.news_client:
                    try:
                        response = await self.news_client.search_political_news(
                            keywords=["Trump", "Fed", "election"]
                        )
                        articles.extend(response)
                    except Exception as e:
                        print(f"  NewsAPI error: {e}")
                        
                # Try GDELT as fallback/additional
                if self.gdelt and len(articles) < 5:
                    try:
                        gdelt_articles = await self.gdelt.get_political_coverage(
                            topics=["Trump", "Biden"]
                        )
                        for art in gdelt_articles:
                            articles.append({
                                "title": art.get("title"),
                                "description": art.get("seendoc", ""),
                                "url": art.get("url"),
                                "publishedAt": art.get("seendate"),
                                "source": {"name": "GDELT"}
                            })
                    except Exception as e:
                        print(f"  GDELT error: {e}")
                        
                # Process and emit articles
                for article in articles[:10]:
                    # Analyze sentiment
                    sentiment = SentimentAnalyzer.analyze_article(article)
                    
                    event = {
                        "id": "",
                        "timestamp": datetime.now(),
                        "event_type": "news_article",
                        "source": article.get("source", {}).get("name", "news"),
                        "layer": "Layer0",
                        "data": {
                            "headline": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url"),
                            "published_at": article.get("publishedAt"),
                            "sentiment": sentiment["sentiment"],
                            "sentiment_confidence": sentiment["confidence"]
                        }
                    }
                    
                    await self.event_bus.publish(event)
                    self.ingestion_stats["news"] += 1
                    
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                print(f"  ❌ News error: {e}")
                self.ingestion_stats["errors"] += 1
                await asyncio.sleep(600)
                
    async def _ingest_social_real(self):
        """Real social media ingestion"""
        if not self.twitter_client:
            return
            
        print("🐦 Social ingestion started")
        
        while self.running:
            try:
                # Search for market-relevant tweets
                tweets = await self.twitter_client.search_market_sentiment(
                    market_keywords=["Trump", "Polymarket", "prediction market"]
                )
                
                for tweet in tweets[:20]:
                    sentiment = SentimentAnalyzer.analyze_tweet(tweet)
                    
                    event = {
                        "id": "",
                        "timestamp": datetime.now(),
                        "event_type": "social_post",
                        "source": "twitter",
                        "layer": "Layer0",
                        "data": {
                            "text": tweet.get("text", ""),
                            "author_id": tweet.get("author_id"),
                            "created_at": tweet.get("created_at"),
                            "metrics": tweet.get("public_metrics", {}),
                            "sentiment": sentiment["sentiment"],
                            "engagement_weight": sentiment.get("engagement_weight", 0),
                            "market_keyword": tweet.get("market_keyword")
                        }
                    }
                    
                    await self.event_bus.publish(event)
                    self.ingestion_stats["social"] += 1
                    
                await asyncio.sleep(180)  # Every 3 minutes
                
            except Exception as e:
                print(f"  ❌ Social error: {e}")
                await asyncio.sleep(300)
                
    async def _ingest_whale_data_real(self):
        """Real whale tracking data"""
        if not self.whale_tracker:
            return
            
        print("🐋 Whale tracking started")
        
        while self.running:
            try:
                # Scan for whale moves
                whale_moves = await self.whale_tracker.scan_for_whale_moves()
                
                for move in whale_moves:
                    event = {
                        "id": "",
                        "timestamp": datetime.now(),
                        "event_type": "whale_movement",
                        "source": "etherscan",
                        "layer": "Layer0",
                        "data": {
                            "address": move.get("address"),
                            "volume_eth_7d": move.get("total_volume_eth_7d"),
                            "whale_score": move.get("whale_score"),
                            "is_active_whale": move.get("is_active_whale"),
                            "recent_transactions": move.get("transactions", [])
                        }
                    }
                    
                    await self.event_bus.publish(event)
                    self.ingestion_stats["whale"] += 1
                    
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                print(f"  ❌ Whale error: {e}")
                await asyncio.sleep(900)
                
    async def _ingest_simulated(self):
        """Fallback simulated data ingestion"""
        print("Using simulated data (no APIs configured)")
        
        # Import simulated ingestion from main system
        from polymarket_agentic_system_complete import DataIngestionLayer
        simulated = DataIngestionLayer(self.event_bus, self.data_store)
        simulated.running = True
        
        await asyncio.gather(
            simulated._ingest_clob_data(),
            simulated._ingest_news_data(),
            simulated._ingest_social_data(),
        )
        
    async def stop(self):
        """Stop ingestion and cleanup"""
        self.running = False
        
        # Cleanup API clients
        if self.polymarket:
            await self.polymarket.__aexit__(None, None, None)
        if self.news_client:
            await self.news_client.__aexit__(None, None, None)
        if self.twitter_client:
            await self.twitter_client.__aexit__(None, None, None)
        if self.whale_tracker:
            await self.whale_tracker.__aexit__(None, None, None)
            
        print(f"⏹️ Layer 0 stopped. Stats: {self.ingestion_stats}")


# Factory function
def create_data_ingestion_layer(event_bus, data_store, use_real_apis: bool = True):
    """
    Create appropriate data ingestion layer
    
    Args:
        event_bus: Event bus for publishing
        data_store: Data store for persistence
        use_real_apis: If True, try to use real APIs; else simulated
        
    Returns:
        RealTimeDataIngestion instance
    """
    # Check if we should use real APIs
    paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
    
    if use_real_apis and not paper_trading:
        print("🔌 Connecting to REAL APIs (LIVE MODE)")
    else:
        print("📊 Using SIMULATED data (PAPER TRADING MODE)")
        use_real_apis = False
        
    return RealTimeDataIngestion(event_bus, data_store, use_real_apis)
