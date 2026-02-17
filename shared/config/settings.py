"""
Configuration management for the ASX AI Investment Platform
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "ASX AI Investment Platform"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "asx_platform"
    db_user: str = "asx_user"
    db_password: str = "changeme"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def database_url_sync(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_stock_data: str = "stock-data"
    kafka_topic_predictions: str = "predictions"
    kafka_topic_recommendations: str = "recommendations"
    
    # API Keys - Data Sources
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    twelve_data_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None
    
    # API Keys - Social Media
    twitter_bearer_token: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    
    # ML Configuration
    ml_model_path: str = "./ml-models/trained"
    ml_retrain_interval_hours: int = 24
    ml_min_training_samples: int = 1000
    
    # Recommendation Engine
    min_investment: int = 50
    max_investment: int = 10000
    max_positions_small_portfolio: int = 3
    max_positions_large_portfolio: int = 15
    risk_free_rate: float = 0.04
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Monitoring
    prometheus_port: int = 8000
    
    # AWS (Optional)
    aws_region: str = "ap-southeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    
    # Elasticsearch
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    
    @property
    def elasticsearch_url(self) -> str:
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Data Source Configuration
class DataSourceConfig(BaseSettings):
    """Configuration for data sources"""
    
    # Update intervals (in seconds)
    realtime_update_interval: int = 60  # 1 minute
    historical_update_interval: int = 3600  # 1 hour
    news_update_interval: int = 300  # 5 minutes
    
    # Data retention (in days)
    minute_data_retention: int = 7
    hourly_data_retention: int = 90
    daily_data_retention: int = 3650  # 10 years
    
    # ASX specific
    asx_trading_hours_start: str = "10:00"
    asx_trading_hours_end: str = "16:00"
    asx_timezone: str = "Australia/Sydney"
    
    # Data quality thresholds
    min_sources_for_consensus: int = 2
    max_price_variance_percent: float = 2.0  # Max 2% variance between sources
    min_confidence_score: float = 0.7
    
    class Config:
        env_file = ".env"


# ML Model Configuration
class MLConfig(BaseSettings):
    """Configuration for ML models"""
    
    # Model types to use
    use_lstm: bool = True
    use_transformer: bool = True
    use_xgboost: bool = True
    use_random_forest: bool = True
    
    # Training parameters
    train_test_split: float = 0.8
    validation_split: float = 0.1
    batch_size: int = 32
    epochs: int = 100
    early_stopping_patience: int = 10
    
    # Feature engineering
    lookback_periods: int = 60  # Days of historical data to use
    technical_indicators: List[str] = [
        "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26",
        "rsi", "macd", "bollinger_bands",
        "atr", "obv"
    ]
    
    # Prediction horizons
    prediction_horizons: List[int] = [1, 5, 10, 20]  # Days ahead
    
    # Ensemble weights (must sum to 1.0)
    lstm_weight: float = 0.30
    transformer_weight: float = 0.30
    xgboost_weight: float = 0.25
    random_forest_weight: float = 0.15
    
    @validator('lstm_weight', 'transformer_weight', 'xgboost_weight', 'random_forest_weight')
    def validate_weights(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Weights must be between 0 and 1")
        return v
    
    class Config:
        env_file = ".env"


# Capital-Aware Recommendation Configuration
class RecommendationConfig(BaseSettings):
    """Configuration for capital-aware recommendations"""
    
    # Capital tiers and strategies
    tier_1_max: int = 500  # Micro portfolio
    tier_2_max: int = 2000  # Small portfolio
    tier_3_max: int = 5000  # Medium portfolio
    # tier_4: 5000-10000  # Large portfolio
    
    # Position limits by tier
    tier_1_max_positions: int = 1  # $50-500: focus on single best pick
    tier_2_max_positions: int = 3  # $500-2000: basic diversification
    tier_3_max_positions: int = 7  # $2000-5000: moderate diversification
    tier_4_max_positions: int = 15  # $5000-10000: full diversification
    
    # Minimum investment per stock (to avoid excessive transaction costs)
    min_position_size: int = 50
    
    # Transaction costs
    brokerage_fee_fixed: float = 5.00  # Fixed fee per trade
    brokerage_fee_percent: float = 0.001  # 0.1% of trade value
    
    # Risk limits by capital size
    tier_1_max_risk_score: float = 0.5  # Lower risk for small capital
    tier_2_max_risk_score: float = 0.6
    tier_3_max_risk_score: float = 0.7
    tier_4_max_risk_score: float = 0.8  # Can take more risk with larger capital
    
    # Sector diversification
    max_sector_concentration: float = 0.40  # Max 40% in one sector
    min_sectors: int = 2  # Minimum sectors for diversification
    
    # Rebalancing thresholds
    rebalance_threshold_percent: float = 10.0  # Rebalance if position drifts >10%
    
    class Config:
        env_file = ".env"


# Global settings instances
settings = Settings()
data_source_config = DataSourceConfig()
ml_config = MLConfig()
recommendation_config = RecommendationConfig()
