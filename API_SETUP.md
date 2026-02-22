# API Connections Setup Guide

This guide covers all API connections needed for the Polymarket Agentic Trading System.

## Quick Start Checklist

- [ ] Polymarket API (for trading)
- [ ] NewsAPI (for sentiment - free tier available)
- [ ] Twitter/X API (for social sentiment - paid)
- [ ] Etherscan API (for whale tracking - free tier available)
- [ ] Optional: Telegram bot (for alerts)

---

## Required APIs

### 1. Polymarket APIs (REQUIRED for trading)

**Purpose**: Order book data, placing trades, checking positions

**Setup**:
1. Go to https://docs.polymarket.com/
2. Create developer account
3. Generate API credentials
4. Set in `.env`:
   ```
   POLYMARKET_API_KEY=your_key
   POLYMARKET_API_SECRET=your_secret
   POLYMARKET_API_PASSPHRASE=your_passphrase
   ```

**Cost**: Free for read-only, fees for trading

**Rate Limits**: 
- Read: 100 requests/10 seconds
- Write: 10 requests/10 seconds

---

### 2. NewsAPI (RECOMMENDED - Free tier)

**Purpose**: News sentiment analysis for Layer 1

**Setup**:
1. Go to https://newsapi.org/
2. Sign up (free tier: 100 requests/day)
3. Copy API key
4. Set in `.env`:
   ```
   NEWSAPI_KEY=your_key
   ```

**Cost**: Free tier available ($0)
- 100 requests/day
- 1 month history

**Paid Tiers**:
- Developer: $449/month (100K requests/day)
- Business: Contact sales

**Rate Limits**: 
- Free: 100/day
- Paid: Varies by tier

---

### 3. Twitter/X API (OPTIONAL but powerful)

**Purpose**: Social sentiment, trending topics

**Setup**:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Apply for developer account
3. Create project and app
4. Generate Bearer Token
5. Set in `.env`:
   ```
   TWITTER_BEARER_TOKEN=your_token
   ```

**Cost**: 
- Free tier: 1,500 tweets/month (very limited)
- Basic: $100/month (10,000 tweets/month)
- Pro: $5,000/month (1M tweets/month)

**Recommendation**: Start with free, upgrade if sentiment analysis is critical

**Rate Limits**: Varies by tier

---

### 4. Etherscan API (RECOMMENDED - Free tier)

**Purpose**: Whale tracking, blockchain analysis

**Setup**:
1. Go to https://etherscan.io/apis
2. Create free account
3. Generate API key
4. Set in `.env`:
   ```
   ETHERSCAN_API_KEY=your_key
   ```

**Cost**: Free tier available ($0)
- 5 calls/second
- Up to 100,000 calls/day

**Paid Tiers**:
- API Pro: $199/month (higher limits)

**Rate Limits**: 5 calls/second

---

### 5. Telegram Bot (OPTIONAL)

**Purpose**: Alerts, notifications

**Setup**:
1. Message @BotFather on Telegram
2. Create new bot
3. Copy bot token
4. Get your chat ID by messaging @userinfobot
5. Set in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

**Cost**: Free

---

## Optional APIs

### Polygon.io

**Purpose**: Stock/crypto correlation data

**Setup**: https://polygon.io/

**Cost**: Free tier available

### The Graph (Polymarket Subgraph)

**Purpose**: Historical on-chain data

**Setup**: https://thegraph.com/explorer/subgraphs

**Cost**: Free tier available

### GDELT

**Purpose**: Global news database

**Setup**: No key needed! Already enabled.

**Cost**: Free

---

## Setup Steps

### Step 1: Copy Environment Template

```bash
cd /Users/morpheus/.openclaw/workspace/polymarket-agentic-trading
cp .env.example .env
```

### Step 2: Fill in API Keys

Edit `.env` with your keys:

```bash
# Required for trading
POLYMARKET_API_KEY=xxx
POLYMARKET_API_SECRET=xxx
POLYMARKET_API_PASSPHRASE=xxx

# Recommended for sentiment
NEWSAPI_KEY=xxx

# Optional but powerful
TWITTER_BEARER_TOKEN=xxx
ETHERSCAN_API_KEY=xxx

# For alerts
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

### Step 3: Test Connections

```bash
# Test all APIs
python3 -c "
import asyncio
from api_clients import *

async def test():
    # Test Polymarket
    async with PolymarketDataAggregator() as poly:
        markets = await poly.get_all_active_markets()
        print(f'Polymarket: {len(markets)} markets')
    
    # Test News
    async with NewsAPIClient() as news:
        result = await news.search_news('Trump', page_size=1)
        print(f'NewsAPI: {result.success}')

asyncio.run(test())
"
```

---

## Cost Summary

| API | Free Tier | Recommended Tier | Monthly Cost |
|-----|-----------|------------------|--------------|
| Polymarket | ✅ Read-only | Production | Trading fees only |
| NewsAPI | ✅ 100/day | Free | $0 |
| Twitter/X | ⚠️ 1,500 tweets | Basic | $100 |
| Etherscan | ✅ 100K/day | Free | $0 |
| Telegram | ✅ | Free | $0 |
| **TOTAL** | | | **~$100/mo** |

---

## Troubleshooting

### "API key not found"
- Check `.env` file exists in same directory
- Ensure no spaces around `=` in `.env`
- Run: `source .env` before starting

### "Rate limit exceeded"
- Reduce API call frequency in code
- Upgrade to paid tier if needed
- Enable caching (see Layer 5)

### "Connection timeout"
- Check internet connection
- Verify API service status
- Increase timeout in client config

---

## Security Notes

⚠️ **NEVER commit `.env` to GitHub!**

The `.gitignore` should include:
```
.env
*.key
*.secret
```

⚠️ **Protect your private keys!**
- Polymarket API keys can place real trades
- Store securely (use 1Password, etc.)
- Rotate keys periodically

---

## Next Steps

1. Sign up for APIs above
2. Copy `.env.example` to `.env`
3. Add your keys
4. Test connections
5. Run the system!

```bash
python3 polymarket_agentic_system_complete.py
```

Ready to connect, Neo?
