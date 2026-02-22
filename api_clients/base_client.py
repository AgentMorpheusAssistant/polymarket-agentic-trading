"""
API Client Infrastructure for Polymarket Agentic Trading System
Base classes and utilities for all API connections
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: datetime = None
    latency_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RateLimiter:
    """Rate limiter for API calls"""
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0
        
    async def acquire(self):
        """Wait if needed to respect rate limit"""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_call_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
            
        self.last_call_time = asyncio.get_event_loop().time()


class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 rate_limit: float = 1.0, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.rate_limiter = RateLimiter(rate_limit)
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.error_count = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, method: str, endpoint: str, 
                           headers: Dict = None, params: Dict = None,
                           json_data: Dict = None) -> APIResponse:
        """Make HTTP request with rate limiting and error handling"""
        await self.rate_limiter.acquire()
        
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = headers or {}
        
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
            
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            ) as response:
                
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                self.request_count += 1
                
                if response.status == 200:
                    data = await response.json()
                    return APIResponse(
                        success=True,
                        data=data,
                        latency_ms=latency
                    )
                else:
                    error_text = await response.text()
                    self.error_count += 1
                    logger.error(f"API Error {response.status}: {error_text}")
                    return APIResponse(
                        success=False,
                        data=None,
                        error=f"HTTP {response.status}: {error_text}",
                        latency_ms=latency
                    )
                    
        except asyncio.TimeoutError:
            self.error_count += 1
            logger.error(f"API Timeout: {url}")
            return APIResponse(
                success=False,
                data=None,
                error="Request timeout",
                latency_ms=(asyncio.get_event_loop().time() - start_time) * 1000
            )
        except Exception as e:
            self.error_count += 1
            logger.error(f"API Exception: {e}")
            return APIResponse(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def get(self, endpoint: str, params: Dict = None, headers: Dict = None) -> APIResponse:
        """Make GET request"""
        return await self._make_request('GET', endpoint, headers, params)
        
    async def post(self, endpoint: str, json_data: Dict = None, headers: Dict = None) -> APIResponse:
        """Make POST request"""
        return await self._make_request('POST', endpoint, headers, json_data=json_data)
        
    def get_stats(self) -> Dict:
        """Get API usage statistics"""
        return {
            "requests": self.request_count,
            "errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "base_url": self.base_url
        }


class APIHealthMonitor:
    """Monitor health of all API connections"""
    def __init__(self):
        self.clients: Dict[str, BaseAPIClient] = {}
        self.health_status: Dict[str, Dict] = {}
        
    def register_client(self, name: str, client: BaseAPIClient):
        """Register an API client for monitoring"""
        self.clients[name] = client
        
    async def check_health(self) -> Dict[str, Dict]:
        """Check health of all registered APIs"""
        for name, client in self.clients.items():
            self.health_status[name] = {
                "stats": client.get_stats(),
                "last_check": datetime.now().isoformat()
            }
        return self.health_status


# Convenience function to load API keys from environment
def load_api_key(key_name: str, required: bool = False) -> Optional[str]:
    """Load API key from environment"""
    value = os.getenv(key_name)
    if required and not value:
        raise ValueError(f"Required API key {key_name} not found in environment")
    return value
