# Polymarket Agentic Trading System v1.0

A complete 5-layer agentic architecture for autonomous prediction market trading on Polymarket.

Based on architecture diagrams by [@thejayden](https://x.com/thejayden/status/2025657149515542746)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 0: DATA INGESTION                                    │
│  ├── CLOB Data (Polymarket order book)                     │
│  ├── News APIs (sentiment)                                 │
│  ├── Social Feeds (Twitter/X)                              │
│  ├── Prediction Markets (Kalshi, etc.)                     │
│  └── Alt Data (whale movements, blockchain)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: RESEARCH AGENTS                                   │
│  ├── Sentiment Agent (news/social analysis)                │
│  ├── Forecasting Agent (price prediction)                  │
│  ├── Calibration Agent (cross-platform arb)                │
│  ├── Liquidity Agent (order book depth)                    │
│  ├── Resolution Agent (timing analysis)                    │
│  └── Research Synthesis (combines insights)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: SIGNAL GENERATION                                 │
│  ├── Alpha Generator                                       │
│  ├── Devil's Advocate (risk challenge)                     │
│  ├── Backtester (historical validation)                    │
│  └── Signal Validator                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: PORTFOLIO & RISK                                  │
│  ├── Portfolio Manager (Kelly sizing)                      │
│  ├── Correlation Monitor                                   │
│  ├── Tail Risk Agent (VaR)                                 │
│  ├── Platform Risk                                         │
│  └── ⚠️ HUMAN CHECKPOINT (large positions)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: EXECUTION                                         │
│  ├── Execution Agent                                       │
│  ├── Order Book Sniper (price improvement)                 │
│  ├── Fill Monitor                                          │
│  └── Hedge Agent                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: MONITORING & LEARNING                             │
│  ├── Resolution Monitor                                    │
│  ├── Attribution                                           │
│  ├── Model Calibration                                     │
│  ├── Drift Detection                                       │
│  ├── Strategy Evolution                                    │
│  └── Long-Term Memory                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    FEEDBACK LOOP → Layer 0
```

---

## 🚀 Quick Start

```bash
# Run the complete system
python3 polymarket_agentic_system_complete.py
```

You'll see live trading signals flowing through all 5 layers with real-time feedback.

---

## 📁 Files

| File | Description |
|------|-------------|
| `polymarket_agentic_system_complete.py` | Full 5-layer production system |
| `polymarket_agentic_system.py` | Simplified 3-layer version |
| `architecture_layer0-2.jpg` | Architecture diagram (Layers 0-2) |
| `architecture_layer3-5.jpg` | Architecture diagram (Layers 3-5) |

---

## 🎯 Key Features

- **Event-Driven Architecture** — Decoupled layers via Event Bus
- **Multi-Agent Consensus** — Research agents vote on opportunities
- **Risk Management** — Kelly criterion, VaR, correlation checks
- **Human-in-the-Loop** — Large positions require approval
- **Learning System** — Drift detection, strategy evolution, long-term memory
- **Feedback Loops** — Layer 5 continuously improves Layer 0

---

## 🔄 Data Flow

```
Raw Data → Research → Signals → Risk Check → Execution → Monitor
                                              ↑_______________↓
                                                   (feedback)
```

---

## 🛡️ Safety Features

1. **Portfolio Exposure Limits** — Max 80% portfolio in positions
2. **Tail Risk Circuit Breaker** — Rejects signals exceeding 10% portfolio VaR
3. **Correlation Checks** — Reduces size if correlated positions exist
4. **Human Checkpoints** — Positions > $2000 require approval
5. **Drift Detection** — Auto-retrains if win rate drops below 50%

---

## 📊 Performance Monitoring

Layer 5 continuously tracks:
- Win rates and PnL attribution
- Model calibration accuracy
- Strategy drift detection
- Pattern recognition for evolution

---

## 🔮 Future Enhancements

- [ ] Real Polymarket API integration
- [ ] ML model training pipeline
- [ ] Web dashboard for monitoring
- [ ] Telegram alerts for signals
- [ ] Multi-market support (Kalshi, etc.)

---

## 📜 Version History

### v1.0 (2026-02-22)
- Initial release
- Complete 5-layer architecture
- Event-driven implementation
- Human-in-the-loop checkpoints
- Feedback loops from Layer 5 to Layer 0

---

Built by Morpheus for Neo. Red pill only.
