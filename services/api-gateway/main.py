"""
ASX AI Investment Platform - Vercel Serverless API
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="ASX AI Investment Platform",
    description="AI-powered ASX stock recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class RecommendationRequest(BaseModel):
    total_capital: float = 1000
    risk_tolerance: str = "moderate"
    investment_strategy: str = "balanced"
    min_diversification: int = 3
    max_single_stock_percentage: float = 0.30

class StockRecommendation(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    target_price: float
    predicted_return: float
    confidence_score: float
    recommended_allocation: float
    recommended_shares: int
    reasoning: str

class PortfolioResponse(BaseModel):
    total_investment: float
    expected_return: float
    risk_level: str
    summary: str
    recommendations: list

# --- ASX Stock Data ---

ASX_STOCKS = {
    "CBA.AX": {"name": "Commonwealth Bank", "sector": "Financials", "price": 118.50},
    "BHP.AX": {"name": "BHP Group", "sector": "Materials", "price": 44.20},
    "CSL.AX": {"name": "CSL Limited", "sector": "Healthcare", "price": 285.00},
    "NAB.AX": {"name": "National Australia Bank", "sector": "Financials", "price": 37.80},
    "WBC.AX": {"name": "Westpac Banking", "sector": "Financials", "price": 28.50},
    "ANZ.AX": {"name": "ANZ Group", "sector": "Financials", "price": 29.20},
    "FMG.AX": {"name": "Fortescue Metals", "sector": "Materials", "price": 19.80},
    "WES.AX": {"name": "Wesfarmers", "sector": "Consumer", "price": 73.50},
    "TLS.AX": {"name": "Telstra Group", "sector": "Telecom", "price": 3.95},
    "RIO.AX": {"name": "Rio Tinto", "sector": "Materials", "price": 118.00},
    "MQG.AX": {"name": "Macquarie Group", "sector": "Financials", "price": 210.00},
    "WOW.AX": {"name": "Woolworths", "sector": "Consumer", "price": 31.20},
    "ALL.AX": {"name": "Aristocrat Leisure", "sector": "Technology", "price": 48.50},
    "STO.AX": {"name": "Santos", "sector": "Energy", "price": 7.20},
    "WDS.AX": {"name": "Woodside Energy", "sector": "Energy", "price": 25.80},
}

# --- Capital tier logic ---

def get_tier(capital: float):
    if capital <= 500:
        return 1, 1, 0.5
    elif capital <= 2000:
        return 2, 3, 0.6
    elif capital <= 5000:
        return 3, 7, 0.7
    else:
        return 4, 15, 0.8

def generate_recommendations(req: RecommendationRequest) -> PortfolioResponse:
    capital = max(50, min(10000, req.total_capital))
    tier, max_positions, max_risk = get_tier(capital)

    # Strategy adjustments
    strategy_multipliers = {
        "conservative": 0.7,
        "balanced": 1.0,
        "growth": 1.3,
        "aggressive": 1.5,
    }
    multiplier = strategy_multipliers.get(req.investment_strategy, 1.0)

    # Risk adjustments
    risk_multipliers = {
        "very_low": 0.5,
        "low": 0.7,
        "moderate": 1.0,
        "high": 1.3,
        "very_high": 1.5,
    }
    risk_mult = risk_multipliers.get(req.risk_tolerance, 1.0)

    # Score stocks
    scored = []
    for symbol, info in ASX_STOCKS.items():
        # Simple scoring: diversify across sectors, prefer affordable stocks for small capital
        base_return = 8.0 + (hash(symbol) % 15)  # 8-22% pseudo-predicted return
        confidence = 0.60 + (hash(symbol + "conf") % 30) / 100  # 0.60-0.90
        risk_score = 0.3 + (hash(symbol + "risk") % 40) / 100  # 0.30-0.70

        if risk_score > max_risk:
            continue

        adj_return = base_return * multiplier * risk_mult
        score = adj_return * confidence

        scored.append({
            "symbol": symbol,
            "name": info["name"],
            "sector": info["sector"],
            "price": info["price"],
            "predicted_return": round(adj_return, 1),
            "confidence": round(confidence, 2),
            "risk_score": round(risk_score, 2),
            "score": score,
        })

    # Sort by score and pick top N
    scored.sort(key=lambda x: x["score"], reverse=True)
    picks = scored[:max_positions]

    # Allocate capital
    total_score = sum(p["score"] for p in picks)
    recs = []
    total_invested = 0

    for pick in picks:
        weight = pick["score"] / total_score if total_score > 0 else 1 / len(picks)
        allocation = round(capital * weight, 2)
        shares = max(1, int(allocation / pick["price"]))
        actual_cost = round(shares * pick["price"], 2)

        if actual_cost > capital - total_invested:
            shares = max(1, int((capital - total_invested) / pick["price"]))
            actual_cost = round(shares * pick["price"], 2)

        if actual_cost <= 0 or total_invested + actual_cost > capital:
            continue

        total_invested += actual_cost
        target = round(pick["price"] * (1 + pick["predicted_return"] / 100), 2)

        recs.append(StockRecommendation(
            symbol=pick["symbol"],
            company_name=pick["name"],
            current_price=pick["price"],
            target_price=target,
            predicted_return=pick["predicted_return"],
            confidence_score=pick["confidence"],
            recommended_allocation=actual_cost,
            recommended_shares=shares,
            reasoning=f"{pick['name']} ({pick['sector']}) - AI confidence {pick['confidence']*100:.0f}%, "
                      f"risk score {pick['risk_score']}, predicted return {pick['predicted_return']}%. "
                      f"Suitable for {req.risk_tolerance} risk tolerance with {req.investment_strategy} strategy.",
        ))

    avg_return = round(sum(r.predicted_return for r in recs) / len(recs), 1) if recs else 0

    return PortfolioResponse(
        total_investment=round(total_invested, 2),
        expected_return=avg_return,
        risk_level=req.risk_tolerance,
        summary=f"Tier {tier} portfolio: {len(recs)} ASX stocks selected for ${capital:.0f} capital "
                f"with {req.risk_tolerance} risk and {req.investment_strategy} strategy. "
                f"Expected average return: {avg_return}%.",
        recommendations=[r.dict() for r in recs],
    )

# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": "ASX AI Investment Platform",
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/stocks")
async def get_stocks():
    return {
        symbol: {
            "symbol": symbol,
            "company_name": info["name"],
            "sector": info["sector"],
            "current_price": info["price"],
        }
        for symbol, info in ASX_STOCKS.items()
    }

@app.post("/api/v1/recommendations/generate")
async def create_recommendations(req: RecommendationRequest):
    if req.total_capital < 50 or req.total_capital > 10000:
        raise HTTPException(status_code=400, detail="Capital must be between $50 and $10,000")
    return generate_recommendations(req)

@app.get("/api/v1/recommendations/sample")
async def sample_recommendations():
    req = RecommendationRequest(total_capital=1000, risk_tolerance="moderate", investment_strategy="balanced")
    return generate_recommendations(req)

# Vercel handler
handler = app
