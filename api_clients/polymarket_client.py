"""
Polymarket API Clients
Connects to Polymarket CLOB and Gamma APIs for trading and market data
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from base_client import BaseAPIClient, APIResponse, load_api_key


class PolymarketCLOBClient(BaseAPIClient):
    """
    Polymarket CLOB (Central Limit Order Book) API Client
    For: Order book data, placing orders, checking fills
    Docs: https://docs.polymarket.com/
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://clob.polymarket.com",
            api_key=load_api_key("POLYMARKET_API_KEY"),
            rate_limit=2.0  # 2 calls per second
        )
        self.api_secret = load_api_key("POLYMARKET_API_SECRET")
        self.passphrase = load_api_key("POLYMARKET_API_PASSPHRASE")
        
    async def get_order_book(self, token_id: str) -> APIResponse:
        """
        Get order book for a specific market token
        
        Args:
            token_id: The token ID for the market outcome
            
        Returns:
            APIResponse with bids and asks
        """
        endpoint = f"/book/{token_id}"
        return await self.get(endpoint)
        
    async def get_markets(self, active: bool = True, closed: bool = False) -> APIResponse:
        """
        Get list of available markets
        
        Args:
            active: Include active markets
            closed: Include closed markets
        """
        params = {"active": str(active).lower(), "closed": str(closed).lower()}
        return await self.get("/markets", params=params)
        
    async def get_market(self, condition_id: str) -> APIResponse:
        """Get detailed market information"""
        return await self.get(f"/markets/{condition_id}")
        
    async def get_price(self, token_id: str, side: str = "BUY", 
                       amount: Optional[Decimal] = None) -> APIResponse:
        """
        Get indicative price for a trade
        
        Args:
            token_id: Token ID to trade
            side: "BUY" or "SELL"
            amount: Optional amount to get price for
        """
        params = {"token_id": token_id, "side": side}
        if amount:
            params["amount"] = str(amount)
        return await self.get("/price", params=params)
        
    async def place_order(self, order_data: Dict) -> APIResponse:
        """
        Place a limit order
        
        Args:
            order_data: {
                "tokenID": str,
                "price": float (0-1),
                "size": float,
                "side": "BUY" or "SELL",
                "feeRateBps": int (optional)
            }
        """
        # In production: Sign order with private key
        # For now, return simulated response
        if os.getenv("PAPER_TRADING", "true").lower() == "true":
            return APIResponse(
                success=True,
                data={
                    "order_id": f"paper_{datetime.now().timestamp()}",
                    "status": "PAPER_TRADE",
                    "message": "Paper trading mode - no real order placed"
                }
            )
        
        # Real trading would require wallet signature
        return await self.post("/order", json_data=order_data)
        
    async def cancel_order(self, order_id: str) -> APIResponse:
        """Cancel an existing order"""
        return await self.post(f"/order/{order_id}/cancel")
        
    async def get_open_orders(self) -> APIResponse:
        """Get all open orders"""
        return await self.get("/orders")
        
    async def get_fills(self, market_id: Optional[str] = None) -> APIResponse:
        """Get fill history"""
        params = {}
        if market_id:
            params["market"] = market_id
        return await self.get("/fills", params=params)


class PolymarketGammaClient(BaseAPIClient):
    """
    Polymarket Gamma API Client
    For: Market metadata, prices, events
    Docs: https://docs.polymarket.com/
    """
    
    def __init__(self):
        super().__init__(
            base_url=os.getenv("POLYMARKET_GAMMA_URL", "https://gamma-api.polymarket.com"),
            rate_limit=5.0  # 5 calls per second (more lenient)
        )
        
    async def get_events(self, active: bool = True, limit: int = 100) -> APIResponse:
        """
        Get prediction market events
        
        Args:
            active: Only active events
            limit: Number of events to return
        """
        params = {"active": str(active).lower(), "limit": limit}
        return await self.get("/events", params=params)
        
    async def get_event(self, event_id: str) -> APIResponse:
        """Get detailed event information"""
        return await self.get(f"/events/{event_id}")
        
    async def get_markets(self, limit: int = 100, offset: int = 0) -> APIResponse:
        """Get all markets"""
        params = {"limit": limit, "offset": offset}
        return await self.get("/markets", params=params)
        
    async def get_market(self, market_slug: str) -> APIResponse:
        """Get market by slug"""
        return await self.get(f"/markets/{market_slug}")
        
    async def get_market_by_condition(self, condition_id: str) -> APIResponse:
        """Get market by condition ID"""
        return await self.get(f"/markets", params={"conditionIds": condition_id})
        
    async def get_series(self) -> APIResponse:
        """Get event series/categories"""
        return await self.get("/series")


class PolymarketDataAggregator:
    """
    Aggregates data from both CLOB and Gamma APIs
    Provides unified interface for Layer 0 Data Ingestion
    """
    
    def __init__(self):
        self.clob = PolymarketCLOBClient()
        self.gamma = PolymarketGammaClient()
        
    async def __aenter__(self):
        await self.clob.__aenter__()
        await self.gamma.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.clob.__aexit__(exc_type, exc_val, exc_tb)
        await self.gamma.__aexit__(exc_type, exc_val, exc_tb)
        
    async def get_full_market_data(self, condition_id: str, token_id: str) -> Dict:
        """
        Get complete market data combining Gamma and CLOB
        
        Returns:
            Unified market data dictionary
        """
        # Fetch in parallel
        gamma_task = self.gamma.get_market_by_condition(condition_id)
        clob_task = self.clob.get_order_book(token_id)
        
        gamma_resp, clob_resp = await asyncio.gather(gamma_task, clob_task)
        
        return {
            "market_info": gamma_resp.data if gamma_resp.success else None,
            "order_book": clob_resp.data if clob_resp.success else None,
            "timestamp": datetime.now().isoformat(),
            "errors": []
        }
        
    async def get_all_active_markets(self) -> List[Dict]:
        """Get all active markets with basic info"""
        response = await self.gamma.get_events(active=True, limit=100)
        
        if not response.success:
            return []
            
        events = response.data.get("events", [])
        markets = []
        
        for event in events:
            for market in event.get("markets", []):
                markets.append({
                    "id": market.get("conditionId"),
                    "slug": market.get("slug"),
                    "question": market.get("question"),
                    "volume": market.get("volume"),
                    "liquidity": market.get("liquidity"),
                    "end_date": market.get("endDate"),
                    "event_title": event.get("title"),
                    "category": event.get("category"),
                    "outcomes": market.get("outcomes", [])
                })
                
        return markets
        
    async def get_high_volume_markets(self, min_volume: float = 100000) -> List[Dict]:
        """Get markets with volume above threshold"""
        all_markets = await self.get_all_active_markets()
        return [m for m in all_markets if m.get("volume", 0) > min_volume]


# Simple test function
async def test_polymarket_apis():
    """Test Polymarket API connections"""
    print("Testing Polymarket APIs...")
    
    async with PolymarketDataAggregator() as aggregator:
        # Test Gamma API
        print("\n1. Testing Gamma API (Events)...")
        events = await aggregator.gamma.get_events(limit=5)
        print(f"   Success: {events.success}")
        if events.success:
            print(f"   Events found: {len(events.data.get('events', []))}")
            
        # Test getting markets
        print("\n2. Testing Gamma API (Markets)...")
        markets = await aggregator.get_all_active_markets()
        print(f"   Active markets: {len(markets)}")
        if markets:
            print(f"   Sample: {markets[0]['question'][:50]}...")
            
        # Test high volume markets
        print("\n3. Testing High Volume Filter...")
        high_vol = await aggregator.get_high_volume_markets(min_volume=1000000)
        print(f"   High volume markets (>$1M): {len(high_vol)}")
        
        # Test CLOB API (if market available)
        if markets:
            market = markets[0]
            print(f"\n4. Testing CLOB API (Order Book)...")
            print(f"   Market: {market['question'][:50]}...")
            # Note: Need actual token ID for order book
            print(f"   (Requires token ID - skipping order book test)")
            
    print("\n✅ Polymarket API tests complete!")


if __name__ == "__main__":
    asyncio.run(test_polymarket_apis())
