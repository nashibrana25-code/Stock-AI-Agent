"""
Shared data models for the ASX AI Investment Platform
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class InvestmentStrategy(str, Enum):
    CONSERVATIVE = "conservative"  # Focus on stable, dividend-paying stocks
    BALANCED = "balanced"  # Mix of growth and stability
    GROWTH = "growth"  # Higher risk, higher potential returns
    AGGRESSIVE = "aggressive"  # Maximum growth potential


class OrderType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SentimentScore(str, Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


# Stock Data Models
class StockPrice(BaseModel):
    """Real-time stock price data"""
    symbol: str
    source: str  # yahoo, alpha_vantage, etc.
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    adjusted_close: Optional[Decimal] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class AggregatedPrice(BaseModel):
    """Consensus price from multiple sources"""
    symbol: str
    timestamp: datetime
    consensus_price: Decimal
    price_variance: Decimal
    confidence_score: float = Field(ge=0, le=1)
    source_count: int
    individual_prices: List[StockPrice]


class StockInfo(BaseModel):
    """Company and stock information"""
    symbol: str
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    description: Optional[str] = None
    website: Optional[str] = None


# Technical Analysis Models
class TechnicalIndicators(BaseModel):
    """Technical analysis indicators"""
    symbol: str
    timestamp: datetime
    
    # Moving Averages
    sma_20: Optional[Decimal] = None
    sma_50: Optional[Decimal] = None
    sma_200: Optional[Decimal] = None
    ema_12: Optional[Decimal] = None
    ema_26: Optional[Decimal] = None
    
    # Momentum
    rsi: Optional[Decimal] = None  # 0-100
    macd: Optional[Decimal] = None
    macd_signal: Optional[Decimal] = None
    stochastic: Optional[Decimal] = None
    
    # Volatility
    bollinger_upper: Optional[Decimal] = None
    bollinger_middle: Optional[Decimal] = None
    bollinger_lower: Optional[Decimal] = None
    atr: Optional[Decimal] = None  # Average True Range
    
    # Volume
    obv: Optional[Decimal] = None  # On Balance Volume


# Sentiment Analysis Models
class NewsArticle(BaseModel):
    """News article for sentiment analysis"""
    article_id: str
    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    related_symbols: List[str] = []


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    symbol: str
    timestamp: datetime
    overall_sentiment: SentimentScore
    sentiment_score: float = Field(ge=-1, le=1)  # -1 (very negative) to +1 (very positive)
    news_count: int
    social_media_mentions: int
    trending_topics: List[str] = []


# ML Prediction Models
class PricePrediction(BaseModel):
    """AI-generated price prediction"""
    symbol: str
    prediction_timestamp: datetime
    target_date: datetime  # When the prediction is for
    
    predicted_price: Decimal
    confidence_interval_lower: Decimal
    confidence_interval_upper: Decimal
    confidence_score: float = Field(ge=0, le=1)
    
    model_name: str
    model_version: str
    features_used: List[str]


class TrendPrediction(BaseModel):
    """Trend direction prediction"""
    symbol: str
    timestamp: datetime
    timeframe: str  # "1d", "1w", "1m", etc.
    
    trend_direction: str  # "up", "down", "sideways"
    trend_strength: float = Field(ge=0, le=1)
    probability_up: float = Field(ge=0, le=1)
    probability_down: float = Field(ge=0, le=1)
    probability_sideways: float = Field(ge=0, le=1)


# Investment Recommendation Models
class PortfolioConstraints(BaseModel):
    """User's portfolio constraints"""
    total_capital: Decimal = Field(ge=50, le=10000)
    risk_tolerance: RiskLevel
    investment_strategy: InvestmentStrategy
    max_position_size: Optional[Decimal] = None
    min_diversification: int = 3  # Minimum number of different stocks
    max_single_stock_percentage: float = 0.30  # Max 30% in one stock
    preferred_sectors: List[str] = []
    excluded_sectors: List[str] = []
    
    @validator('total_capital')
    def validate_capital(cls, v):
        if v < 50:
            raise ValueError("Minimum investment is $50")
        if v > 10000:
            raise ValueError("Maximum investment is $10,000")
        return v


class StockRecommendation(BaseModel):
    """Individual stock recommendation"""
    symbol: str
    company_name: str
    action: OrderType
    
    current_price: Decimal
    target_price: Decimal
    predicted_return: Decimal  # Percentage
    
    confidence_score: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    
    recommended_allocation: Decimal  # Dollar amount
    recommended_shares: int
    
    reasoning: str
    key_metrics: Dict[str, Any]
    sentiment_summary: str
    technical_summary: str


class PortfolioRecommendation(BaseModel):
    """Complete portfolio recommendation"""
    recommendation_id: str
    generated_at: datetime
    
    constraints: PortfolioConstraints
    recommendations: List[StockRecommendation]
    
    total_investment: Decimal
    expected_return: Decimal  # Percentage
    portfolio_risk_score: float = Field(ge=0, le=1)
    diversification_score: float = Field(ge=0, le=1)
    
    sector_allocation: Dict[str, Decimal]
    cash_reserve: Decimal
    
    summary: str
    warnings: List[str] = []


# User Portfolio Tracking
class Position(BaseModel):
    """Current stock position"""
    symbol: str
    shares: int
    average_purchase_price: Decimal
    current_price: Decimal
    total_value: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_percent: Decimal


class Portfolio(BaseModel):
    """User's current portfolio"""
    user_id: str
    positions: List[Position]
    cash_balance: Decimal
    total_value: Decimal
    total_gain_loss: Decimal
    total_gain_loss_percent: Decimal
    last_updated: datetime


# Performance Tracking
class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    portfolio_id: str
    period: str  # "1d", "1w", "1m", "3m", "1y", "all"
    
    total_return: Decimal
    annualized_return: Decimal
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Decimal
    volatility: Decimal
    
    win_rate: float  # Percentage of winning trades
    average_gain: Decimal
    average_loss: Decimal
    
    benchmark_comparison: Optional[Decimal] = None  # vs ASX200


# Alert Models
class Alert(BaseModel):
    """Investment alert/notification"""
    alert_id: str
    user_id: str
    symbol: str
    alert_type: str  # "price_target", "recommendation_change", "news", etc.
    severity: str  # "info", "warning", "critical"
    message: str
    created_at: datetime
    is_read: bool = False
