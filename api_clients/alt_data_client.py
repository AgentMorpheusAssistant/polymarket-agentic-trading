"""
Alternative Data API Clients
For whale tracking, blockchain analysis, and on-chain metrics
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from base_client import BaseAPIClient, APIResponse, load_api_key


class EtherscanClient(BaseAPIClient):
    """
    Etherscan API Client
    For: Whale tracking, transaction monitoring, wallet analysis
    Free tier: 5 calls/second
    Get key: https://etherscan.io/apis
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://api.etherscan.io/api",
            api_key=load_api_key("ETHERSCAN_API_KEY"),
            rate_limit=0.2  # 5 calls per second
        )
        
    async def get_wallet_transactions(self, address: str, 
                                     start_block: Optional[int] = None,
                                     end_block: Optional[int] = None) -> APIResponse:
        """
        Get transactions for a wallet address
        
        Args:
            address: Ethereum wallet address
            start_block: Start block number
            end_block: End block number
        """
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        if start_block:
            params["startblock"] = start_block
        if end_block:
            params["endblock"] = end_block
            
        response = await self.get("", params=params)
        
        # Etherscan wraps response in result field
        if response.success and response.data:
            if response.data.get("status") == "1":
                return APIResponse(
                    success=True,
                    data=response.data.get("result", []),
                    latency_ms=response.latency_ms
                )
            else:
                return APIResponse(
                    success=False,
                    data=None,
                    error=response.data.get("result", "Unknown error"),
                    latency_ms=response.latency_ms
                )
        return response
        
    async def get_token_transfers(self, address: str, 
                                  contract_address: Optional[str] = None) -> APIResponse:
        """Get ERC20 token transfers for an address"""
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        if contract_address:
            params["contractaddress"] = contract_address
            
        response = await self.get("", params=params)
        
        if response.success and response.data:
            if response.data.get("status") == "1":
                return APIResponse(
                    success=True,
                    data=response.data.get("result", [])
                )
        return response
        
    async def get_eth_balance(self, address: str) -> APIResponse:
        """Get ETH balance for an address"""
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key
        }
        return await self.get("", params=params)
        
    async def get_gas_price(self) -> APIResponse:
        """Get current gas price"""
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": self.api_key
        }
        return await self.get("", params=params)


class PolygonClient(BaseAPIClient):
    """
    Polygon.io API Client
    For: Stock market data, crypto prices (can correlate with prediction markets)
    Get key: https://polygon.io/
    """
    
    def __init__(self):
        super().__init__(
            base_url="https://api.polygon.io/v2",
            api_key=load_api_key("POLYGON_API_KEY"),
            rate_limit=5.0  # Varies by plan
        )
        
    async def get_stock_price(self, ticker: str) -> APIResponse:
        """Get current stock price"""
        return await self.get(f"/aggs/ticker/{ticker}/prev")
        
    async def get_crypto_price(self, ticker: str) -> APIResponse:
        """Get crypto price (e.g., X:BTCUSD)"""
        return await self.get(f"/aggs/ticker/X:{ticker}USD/prev")


class WhaleTracker:
    """
    Whale tracking using Etherscan and other sources
    Tracks large wallet movements that might indicate smart money
    """
    
    # Known whale addresses (example - would be expanded in production)
    KNOWN_WHALE_ADDRESSES = [
        "0x0716a17fbaee714f1e6ab0f9d59edbdeb5de06f6",  # Example whale
        # Add more known whales here
    ]
    
    WHALE_THRESHOLD_USD = 50000  # Transactions > $50k considered whale moves
    
    def __init__(self):
        self.etherscan = None
        
    async def __aenter__(self):
        self.etherscan = EtherscanClient()
        await self.etherscan.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.etherscan:
            await self.etherscan.__aexit__(exc_type, exc_val, exc_tb)
            
    async def track_wallet(self, address: str, days: int = 7) -> Dict:
        """
        Track a specific wallet's recent activity
        
        Returns:
            {
                "address": str,
                "total_transactions": int,
                "total_volume_eth": float,
                "recent_transactions": List,
                "risk_score": float  # 0-1, higher = more whale-like
            }
        """
        response = await self.etherscan.get_wallet_transactions(address)
        
        if not response.success:
            return {"error": response.error}
            
        transactions = response.data
        
        # Filter recent transactions
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        total_volume = 0.0
        
        for tx in transactions:
            try:
                tx_time = datetime.fromtimestamp(int(tx.get("timeStamp", 0)))
                if tx_time > cutoff:
                    value_eth = int(tx.get("value", 0)) / 1e18
                    total_volume += value_eth
                    recent.append({
                        "hash": tx.get("hash"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "value_eth": value_eth,
                        "timestamp": tx_time.isoformat(),
                        "gas_price_gwei": int(tx.get("gasPrice", 0)) / 1e9
                    })
            except:
                continue
                
        # Calculate whale score
        whale_score = min(total_volume / 1000, 1.0)  # Normalize to 0-1
        
        return {
            "address": address,
            "total_transactions": len(transactions),
            "recent_transactions": len(recent),
            "total_volume_eth_7d": round(total_volume, 4),
            "whale_score": round(whale_score, 3),
            "is_active_whale": whale_score > 0.5 and len(recent) > 5,
            "transactions": recent[:10]  # Last 10 transactions
        }
        
    async def scan_for_whale_moves(self, addresses: List[str] = None) -> List[Dict]:
        """Scan known whale addresses for recent large moves"""
        if addresses is None:
            addresses = self.KNOWN_WHALE_ADDRESSES
            
        whale_moves = []
        
        for address in addresses:
            result = await self.track_wallet(address, days=1)
            if result.get("is_active_whale"):
                whale_moves.append(result)
                
        return whale_moves
        
    async def detect_polymarket_correlation(self, whale_address: str) -> Dict:
        """
        Check if a whale has Polymarket-related transactions
        """
        # Polymarket contract addresses
        POLYMARKET_CONTRACTS = [
            "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",  # CTF Exchange
            # Add more as needed
        ]
        
        response = await self.etherscan.get_wallet_transactions(whale_address)
        
        if not response.success:
            return {"error": response.error}
            
        transactions = response.data
        polymarket_interactions = []
        
        for tx in transactions:
            to_addr = tx.get("to", "").lower()
            from_addr = tx.get("from", "").lower()
            
            for contract in POLYMARKET_CONTRACTS:
                if contract.lower() in [to_addr, from_addr]:
                    polymarket_interactions.append({
                        "hash": tx.get("hash"),
                        "value": int(tx.get("value", 0)) / 1e18,
                        "timestamp": datetime.fromtimestamp(
                            int(tx.get("timeStamp", 0))
                        ).isoformat()
                    })
                    
        return {
            "address": whale_address,
            "polymarket_interactions": len(polymarket_interactions),
            "is_polymarket_whale": len(polymarket_interactions) > 0,
            "recent_interactions": polymarket_interactions[:5]
        }


class OnChainMetrics:
    """
    Aggregate on-chain metrics for Layer 0 data ingestion
    """
    
    def __init__(self):
        self.etherscan = None
        self.whale_tracker = None
        
    async def __aenter__(self):
        self.etherscan = EtherscanClient()
        self.whale_tracker = WhaleTracker()
        await self.etherscan.__aenter__()
        await self.whale_tracker.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.etherscan:
            await self.etherscan.__aexit__(exc_type, exc_val, exc_tb)
        if self.whale_tracker:
            await self.whale_tracker.__aexit__(exc_type, exc_val, exc_tb)
            
    async def get_network_health(self) -> Dict:
        """Get Ethereum network health metrics"""
        gas_response = await self.etherscan.get_gas_price()
        
        if gas_response.success and gas_response.data:
            result = gas_response.data.get("result", {})
            return {
                "safe_gas_price": result.get("SafeGasPrice"),
                "propose_gas_price": result.get("ProposeGasPrice"),
                "fast_gas_price": result.get("FastGasPrice"),
                "network_congestion": "high" if int(result.get("SafeGasPrice", 0)) > 50 else "normal"
            }
        return {"error": "Could not fetch gas prices"}
        
    async def get_whale_alert_feed(self) -> List[Dict]:
        """Get whale alert feed for Layer 0 ingestion"""
        return await self.whale_tracker.scan_for_whale_moves()


# Test function
async def test_alt_data_apis():
    """Test alternative data APIs"""
    print("Testing Alternative Data APIs...")
    
    # Test Etherscan
    etherscan_key = load_api_key("ETHERSCAN_API_KEY")
    if etherscan_key:
        print("\n1. Testing Etherscan...")
        async with EtherscanClient() as client:
            # Test gas price
            gas = await client.get_gas_price()
            print(f"   Gas price fetch: {'✅' if gas.success else '❌'}")
            if gas.success:
                result = gas.data.get("result", {})
                print(f"   Safe gas: {result.get('SafeGasPrice')} gwei")
    else:
        print("\n1. Etherscan: No API key (skipping)")
        
    # Test Whale Tracker
    print("\n2. Testing Whale Tracker...")
    async with WhaleTracker() as tracker:
        if etherscan_key:
            # Track a known address
            test_address = "0x0716a17fbaee714f1e6ab0f9d59edbdeb5de06f6"
            result = await tracker.track_wallet(test_address, days=1)
            print(f"   Wallet tracking: {'✅' if 'error' not in result else '❌'}")
            if 'error' not in result:
                print(f"   Whale score: {result.get('whale_score', 0)}")
        else:
            print("   (Requires Etherscan API key)")
            
    # Test OnChain Metrics
    print("\n3. Testing OnChain Metrics...")
    async with OnChainMetrics() as metrics:
        if etherscan_key:
            health = await metrics.get_network_health()
            print(f"   Network health: {'✅' if 'error' not in health else '❌'}")
            if 'error' not in health:
                print(f"   Congestion: {health.get('network_congestion')}")
        else:
            print("   (Requires Etherscan API key)")
            
    print("\n✅ Alternative Data API tests complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_alt_data_apis())
