"""
News & Social Media API Clients
For Layer 0 Data Ingestion and Layer 1 Sentiment Analysis
"""

import os
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from base_client import BaseAPIClient, APIResponse, load_api_key


class NewsAPIClient(BaseAPIClient):
    """
    NewsAPI Client
    Free tier: 100 requests/day
    Get key: https://newsapi.org/
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://newsapi.org/v2",
            api_key=load_api_key("NEWSAPI_KEY"),
            rate_limit=0.1  # 6 requests per minute (free tier)
        )
        
    async def search_news(self, query: str, from_date: Optional[str] = None,
                         to_date: Optional[str] = None, language: str = "en",
                         sort_by: str = "relevancy", page_size: int = 20) -> APIResponse:
        """
        Search for news articles
        
        Args:
            query: Search query (e.g., "Trump Fed Chair")
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            language: Article language
            sort_by: relevancy, popularity, publishedAt
            page_size: Number of results (max 100)
        """
        params = {
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
            "apiKey": self.api_key
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
            
        return await self.get("/everything", params=params)
        
    async def get_headlines(self, category: Optional[str] = None,
                           country: str = "us", query: Optional[str] = None) -> APIResponse:
        """Get top headlines"""
        params = {
            "country": country,
            "apiKey": self.api_key
        }
        if category:
            params["category"] = category
        if query:
            params["q"] = query
            
        return await self.get("/top-headlines", params=params)
        
    async def search_political_news(self, keywords: List[str] = None) -> List[Dict]:
        """Search for political/prediction market relevant news"""
        if keywords is None:
            keywords = ["Trump", "Biden", "election", "Fed", "Congress", "Senate"]
            
        all_articles = []
        
        for keyword in keywords[:3]:  # Limit to avoid rate limits
            response = await self.search_news(
                query=keyword,
                from_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                page_size=10
            )
            
            if response.success:
                articles = response.data.get("articles", [])
                for article in articles:
                    article["search_keyword"] = keyword
                all_articles.extend(articles)
                
        return all_articles


class TwitterAPIClient(BaseAPIClient):
    """
    Twitter/X API v2 Client
    For: Social sentiment, trending topics, influencer tracking
    Get key: https://developer.twitter.com/
    
    Note: Free tier is very limited. Basic tier ($100/mo) recommended.
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://api.twitter.com/2",
            api_key=load_api_key("TWITTER_BEARER_TOKEN"),
            rate_limit=0.5  # 1 request per 2 seconds
        )
        
    async def search_tweets(self, query: str, max_results: int = 10,
                           start_time: Optional[str] = None) -> APIResponse:
        """
        Search for tweets
        
        Args:
            query: Search query (supports operators)
            max_results: 10-100 (depends on tier)
            start_time: ISO 8601 timestamp
        """
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id,context_annotations"
        }
        
        if start_time:
            params["start_time"] = start_time
            
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self.get("/tweets/search/recent", params=params, headers=headers)
        
    async def get_user_tweets(self, user_id: str, max_results: int = 10) -> APIResponse:
        """Get tweets from a specific user"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics"
        }
        return await self.get(f"/users/{user_id}/tweets", params=params, headers=headers)
        
    async def get_user_by_username(self, username: str) -> APIResponse:
        """Get user ID from username"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await self.get(f"/users/by/username/{username}", headers=headers)
        
    async def search_market_sentiment(self, market_keywords: List[str]) -> List[Dict]:
        """Search for market-related sentiment"""
        tweets = []
        
        for keyword in market_keywords[:2]:  # Limit for rate
            query = f"{keyword} -is:retweet lang:en"
            response = await self.search_tweets(query, max_results=20)
            
            if response.success:
                for tweet in response.data.get("data", []):
                    tweet["market_keyword"] = keyword
                    tweets.append(tweet)
                    
        return tweets


class GDELTClient:
    """
    GDELT API Client
    Global Database of Events, Language, and Tone
    Free, no key needed
    Docs: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
    """
    
    def __init__(self):
        self.base_url = "https://api.gdeltproject.org/api/v2"
        
    async def search_articles(self, query: str, mode: str = "ArtList",
                             max_records: int = 50) -> Dict:
        """
        Search GDELT articles
        
        Args:
            query: Search terms
            mode: ArtList, TimelineVol, ToneChart, etc.
            max_records: Number of records to return
        """
        import aiohttp
        
        params = {
            "query": query,
            "mode": mode,
            "maxrecords": max_records,
            "format": "json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/doc/doc", params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {"error": f"HTTP {response.status}"}
                
    async def get_political_coverage(self, topics: List[str] = None) -> List[Dict]:
        """Get political topic coverage"""
        if topics is None:
            topics = ["Trump", "Biden", "election"]
            
        results = []
        for topic in topics[:3]:
            data = await self.search_articles(topic, max_records=20)
            articles = data.get("articles", [])
            for article in articles:
                article["search_topic"] = topic
            results.extend(articles)
            
        return results


class SentimentAnalyzer:
    """
    Simple sentiment analysis (no API key needed)
    Uses basic keyword matching as a fallback
    """
    
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'outstanding',
        'best', 'win', 'wins', 'winning', 'success', 'successful', 'victory', 'bullish',
        'surge', 'soar', 'rally', 'moon', 'pump', 'breakthrough', 'strong', 'growth'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'worst', 'fail', 'fails', 'failure', 'failed',
        'lose', 'loses', 'losing', 'loss', 'crash', 'dump', 'bearish', 'decline',
        'drop', 'fall', 'collapse', 'weak', 'crisis', 'disaster', 'panic', 'fear'
    }
    
    @classmethod
    def analyze_text(cls, text: str) -> Dict:
        """
        Analyze sentiment of text
        Returns: {"sentiment": float (-1 to 1), "confidence": float (0 to 1)}
        """
        if not text:
            return {"sentiment": 0.0, "confidence": 0.0}
            
        words = re.findall(r'\b\w+\b', text.lower())
        
        pos_count = sum(1 for w in words if w in cls.POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in cls.NEGATIVE_WORDS)
        total_words = len(words)
        
        if pos_count == 0 and neg_count == 0:
            return {"sentiment": 0.0, "confidence": 0.3}
            
        # Calculate sentiment score
        sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        confidence = min((pos_count + neg_count) / max(total_words * 0.1, 1), 1.0)
        
        return {
            "sentiment": round(sentiment, 3),
            "confidence": round(confidence, 3),
            "positive_words": pos_count,
            "negative_words": neg_count
        }
        
    @classmethod
    def analyze_article(cls, article: Dict) -> Dict:
        """Analyze a news article"""
        text = f"{article.get('title', '')} {article.get('description', '')}"
        return cls.analyze_text(text)
        
    @classmethod
    def analyze_tweet(cls, tweet: Dict) -> Dict:
        """Analyze a tweet"""
        text = tweet.get('text', '')
        metrics = tweet.get('public_metrics', {})
        sentiment = cls.analyze_text(text)
        
        # Weight by engagement
        engagement = metrics.get('like_count', 0) + metrics.get('retweet_count', 0)
        sentiment['engagement_weight'] = min(engagement / 100, 1.0)
        
        return sentiment


# Test function
async def test_news_apis():
    """Test news and social APIs"""
    print("Testing News & Social APIs...")
    
    # Test NewsAPI
    news_key = load_api_key("NEWSAPI_KEY")
    if news_key:
        print("\n1. Testing NewsAPI...")
        async with NewsAPIClient() as client:
            response = await client.search_news("Trump", page_size=5)
            print(f"   Success: {response.success}")
            if response.success:
                print(f"   Articles: {len(response.data.get('articles', []))}")
    else:
        print("\n1. NewsAPI: No API key found (skipping)")
        
    # Test Sentiment Analyzer
    print("\n2. Testing Sentiment Analyzer...")
    text = "Trump wins big victory in latest poll! Market surges on strong performance."
    sentiment = SentimentAnalyzer.analyze_text(text)
    print(f"   Text: {text[:50]}...")
    print(f"   Sentiment: {sentiment['sentiment']:.2f} (confidence: {sentiment['confidence']:.2f})")
    
    # Test GDELT
    print("\n3. Testing GDELT (no key needed)...")
    gdelt = GDELTClient()
    articles = await gdelt.get_political_coverage(topics=["Trump"])
    print(f"   Articles found: {len(articles)}")
    if articles:
        print(f"   Sample: {articles[0].get('title', 'N/A')[:50]}...")
        
    print("\n✅ News API tests complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_news_apis())
