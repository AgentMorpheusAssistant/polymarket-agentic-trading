#!/bin/bash
# Push to GitHub v1.0 - Run this script

cd /Users/morpheus/.openclaw/workspace/polymarket-agentic-trading

echo "============================================"
echo "Pushing Polymarket Agentic Trading v1.0"
echo "============================================"

# Get GitHub username
echo "Enter your GitHub username:"
read USERNAME

# Add remote
git remote add origin https://github.com/$USERNAME/polymarket-agentic-trading.git 2>/dev/null || git remote set-url origin https://github.com/$USERNAME/polymarket-agentic-trading.git

# Push to main
git branch -M main
git push -u origin main

# Create v1.0 tag
git tag -a v1.0 -m "Version 1.0: Complete 5-layer agentic trading system

- Layer 0: Data Ingestion
- Layer 1: Research Agents  
- Layer 2: Signal Generation
- Layer 3: Portfolio & Risk
- Layer 4: Execution
- Layer 5: Monitoring & Learning
- Feedback loops
- Human-in-the-loop checkpoints"

# Push tag
git push origin v1.0

echo ""
echo "============================================"
echo "✅ SUCCESS! v1.0 Published to GitHub"
echo "============================================"
echo "View at: https://github.com/$USERNAME/polymarket-agentic-trading"
echo "Release: https://github.com/$USERNAME/polymarket-agentic-trading/releases/tag/v1.0"
