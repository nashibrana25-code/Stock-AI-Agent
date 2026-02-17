"""
Database models using SQLAlchemy ORM
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean, 
    Text, ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class OrderTypeDB(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class RiskLevelDB(str, enum.Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# Stock Information
class Stock(Base):
    __tablename__ = "stocks"
    
    symbol = Column(String(10), primary_key=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Numeric(20, 2))
    description = Column(Text)
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("StockPriceDB", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicatorDB", back_populates="stock")
    predictions = relationship("PricePredictionDB", back_populates="stock")
    
    __table_args__ = (
        Index('idx_stock_sector', 'sector'),
        Index('idx_stock_industry', 'industry'),
    )


# Price Data
class StockPriceDB(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    source = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    open = Column(Numeric(10, 4), nullable=False)
    high = Column(Numeric(10, 4), nullable=False)
    low = Column(Numeric(10, 4), nullable=False)
    close = Column(Numeric(10, 4), nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Numeric(10, 4))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    __table_args__ = (
        Index('idx_price_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_price_source', 'source'),
    )


class AggregatedPriceDB(Base):
    __tablename__ = "aggregated_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    consensus_price = Column(Numeric(10, 4), nullable=False)
    price_variance = Column(Numeric(10, 4))
    confidence_score = Column(Numeric(3, 2))
    source_count = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_agg_price_symbol_timestamp', 'symbol', 'timestamp'),
    )


# Technical Indicators
class TechnicalIndicatorDB(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    # Moving Averages
    sma_20 = Column(Numeric(10, 4))
    sma_50 = Column(Numeric(10, 4))
    sma_200 = Column(Numeric(10, 4))
    ema_12 = Column(Numeric(10, 4))
    ema_26 = Column(Numeric(10, 4))
    
    # Momentum
    rsi = Column(Numeric(5, 2))
    macd = Column(Numeric(10, 4))
    macd_signal = Column(Numeric(10, 4))
    stochastic = Column(Numeric(5, 2))
    
    # Volatility
    bollinger_upper = Column(Numeric(10, 4))
    bollinger_middle = Column(Numeric(10, 4))
    bollinger_lower = Column(Numeric(10, 4))
    atr = Column(Numeric(10, 4))
    
    # Volume
    obv = Column(Numeric(20, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="indicators")
    
    __table_args__ = (
        Index('idx_indicator_symbol_timestamp', 'symbol', 'timestamp'),
    )


# News and Sentiment
class NewsArticleDB(Base):
    __tablename__ = "news_articles"
    
    article_id = Column(String(255), primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime, nullable=False)
    url = Column(Text)
    
    sentiment_score = Column(Numeric(3, 2))  # -1 to +1
    sentiment_label = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    related_stocks = relationship("NewsStockRelation", back_populates="article")
    
    __table_args__ = (
        Index('idx_news_published', 'published_at'),
        Index('idx_news_source', 'source'),
    )


class NewsStockRelation(Base):
    __tablename__ = "news_stock_relations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(255), ForeignKey('news_articles.article_id'))
    symbol = Column(String(10), ForeignKey('stocks.symbol'))
    relevance_score = Column(Numeric(3, 2))
    
    # Relationships
    article = relationship("NewsArticleDB", back_populates="related_stocks")
    
    __table_args__ = (
        Index('idx_news_stock_symbol', 'symbol'),
    )


class SentimentAnalysisDB(Base):
    __tablename__ = "sentiment_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    overall_sentiment = Column(String(20))
    sentiment_score = Column(Numeric(3, 2))
    news_count = Column(Integer)
    social_media_mentions = Column(Integer)
    trending_topics = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_sentiment_symbol_timestamp', 'symbol', 'timestamp'),
    )


# ML Predictions
class PricePredictionDB(Base):
    __tablename__ = "price_predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    prediction_timestamp = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=False)
    
    predicted_price = Column(Numeric(10, 4), nullable=False)
    confidence_interval_lower = Column(Numeric(10, 4))
    confidence_interval_upper = Column(Numeric(10, 4))
    confidence_score = Column(Numeric(3, 2))
    
    model_name = Column(String(100))
    model_version = Column(String(50))
    features_used = Column(JSON)
    
    actual_price = Column(Numeric(10, 4))  # Filled in after target_date
    prediction_error = Column(Numeric(10, 4))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="predictions")
    
    __table_args__ = (
        Index('idx_prediction_symbol_target', 'symbol', 'target_date'),
        Index('idx_prediction_timestamp', 'prediction_timestamp'),
    )


# User and Portfolio Management
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    portfolios = relationship("PortfolioDB", back_populates="user")
    recommendations = relationship("PortfolioRecommendationDB", back_populates="user")


class PortfolioDB(Base):
    __tablename__ = "portfolios"
    
    portfolio_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    total_capital = Column(Numeric(10, 2), nullable=False)
    cash_balance = Column(Numeric(10, 2), nullable=False)
    
    risk_tolerance = Column(SQLEnum(RiskLevelDB))
    investment_strategy = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("PositionDB", back_populates="portfolio")


class PositionDB(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(255), ForeignKey('portfolios.portfolio_id'), nullable=False)
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    
    shares = Column(Integer, nullable=False)
    average_purchase_price = Column(Numeric(10, 4), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("PortfolioDB", back_populates="positions")


# Recommendations
class PortfolioRecommendationDB(Base):
    __tablename__ = "portfolio_recommendations"
    
    recommendation_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    
    total_capital = Column(Numeric(10, 2), nullable=False)
    risk_tolerance = Column(SQLEnum(RiskLevelDB))
    investment_strategy = Column(String(50))
    
    expected_return = Column(Numeric(5, 2))
    portfolio_risk_score = Column(Numeric(3, 2))
    diversification_score = Column(Numeric(3, 2))
    
    sector_allocation = Column(JSON)
    summary = Column(Text)
    warnings = Column(JSON)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    stock_recommendations = relationship("StockRecommendationDB", back_populates="portfolio_recommendation")


class StockRecommendationDB(Base):
    __tablename__ = "stock_recommendations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(String(255), ForeignKey('portfolio_recommendations.recommendation_id'))
    symbol = Column(String(10), ForeignKey('stocks.symbol'), nullable=False)
    
    action = Column(SQLEnum(OrderTypeDB))
    current_price = Column(Numeric(10, 4))
    target_price = Column(Numeric(10, 4))
    predicted_return = Column(Numeric(5, 2))
    
    confidence_score = Column(Numeric(3, 2))
    risk_score = Column(Numeric(3, 2))
    
    recommended_allocation = Column(Numeric(10, 2))
    recommended_shares = Column(Integer)
    
    reasoning = Column(Text)
    key_metrics = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio_recommendation = relationship("PortfolioRecommendationDB", back_populates="stock_recommendations")
