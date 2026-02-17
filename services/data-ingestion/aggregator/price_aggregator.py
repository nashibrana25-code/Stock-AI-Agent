"""
Price aggregator - combines data from multiple sources to get consensus price
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from statistics import mean, stdev
from loguru import logger

from shared.models.financial_models import StockPrice, AggregatedPrice
from shared.config.settings import data_source_config


class PriceAggregator:
    """Aggregates prices from multiple sources to determine consensus"""
    
    def __init__(self):
        self.min_sources = data_source_config.min_sources_for_consensus
        self.max_variance_percent = data_source_config.max_price_variance_percent
        self.min_confidence = data_source_config.min_confidence_score
    
    def aggregate_prices(self, prices: List[StockPrice]) -> Optional[AggregatedPrice]:
        """
        Aggregate prices from multiple sources into a consensus price
        
        Args:
            prices: List of StockPrice objects from different sources
            
        Returns:
            AggregatedPrice with consensus data or None if insufficient data
        """
        if not prices:
            logger.warning("No prices to aggregate")
            return None
        
        if len(prices) < self.min_sources:
            logger.warning(f"Insufficient sources: {len(prices)} < {self.min_sources}")
            # Still process but with lower confidence
        
        # Extract closing prices
        close_prices = [float(p.close) for p in prices]
        symbol = prices[0].symbol
        
        # Calculate consensus price (weighted average - can be customized)
        consensus = self._calculate_consensus(prices)
        
        # Calculate variance
        variance = self._calculate_variance(close_prices)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(prices, variance)
        
        # Check for outliers
        filtered_prices = self._remove_outliers(prices)
        
        return AggregatedPrice(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            consensus_price=Decimal(str(consensus)),
            price_variance=Decimal(str(variance)),
            confidence_score=confidence,
            source_count=len(prices),
            individual_prices=prices
        )
    
    def _calculate_consensus(self, prices: List[StockPrice]) -> float:
        """
        Calculate consensus price using weighted average
        
        Source weights (can be configured):
        - yahoo_finance: 0.35 (most reliable for ASX)
        - alpha_vantage: 0.30
        - twelve_data: 0.25
        - others: 0.10
        """
        source_weights = {
            'yahoo_finance': 0.35,
            'alpha_vantage': 0.30,
            'twelve_data': 0.25,
            'finnhub': 0.20,
            'default': 0.10
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for price in prices:
            weight = source_weights.get(price.source, source_weights['default'])
            weighted_sum += float(price.close) * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else mean([float(p.close) for p in prices])
    
    def _calculate_variance(self, prices: List[float]) -> float:
        """Calculate price variance as percentage"""
        if len(prices) < 2:
            return 0.0
        
        avg_price = mean(prices)
        std_dev = stdev(prices)
        
        # Return variance as percentage
        return (std_dev / avg_price * 100) if avg_price > 0 else 0.0
    
    def _calculate_confidence(self, prices: List[StockPrice], variance: float) -> float:
        """
        Calculate confidence score (0-1) based on:
        - Number of sources
        - Price variance
        - Recency of data
        """
        # Base confidence from number of sources
        source_score = min(len(prices) / 5.0, 1.0)  # Max at 5 sources
        
        # Variance penalty (higher variance = lower confidence)
        if variance > self.max_variance_percent:
            variance_score = max(0, 1.0 - (variance / self.max_variance_percent - 1))
        else:
            variance_score = 1.0
        
        # Recency score (data should be recent)
        now = datetime.utcnow()
        recency_scores = []
        for price in prices:
            age_seconds = (now - price.timestamp).total_seconds()
            # Penalize data older than 5 minutes
            if age_seconds < 300:  # 5 minutes
                recency_scores.append(1.0)
            elif age_seconds < 3600:  # 1 hour
                recency_scores.append(0.8)
            else:
                recency_scores.append(0.5)
        
        recency_score = mean(recency_scores) if recency_scores else 0.5
        
        # Weighted combination
        confidence = (source_score * 0.4) + (variance_score * 0.4) + (recency_score * 0.2)
        
        return round(confidence, 2)
    
    def _remove_outliers(self, prices: List[StockPrice]) -> List[StockPrice]:
        """Remove statistical outliers from price list"""
        if len(prices) < 3:
            return prices
        
        close_prices = [float(p.close) for p in prices]
        avg = mean(close_prices)
        std = stdev(close_prices)
        
        # Remove prices more than 2 standard deviations from mean
        threshold = 2 * std
        filtered = []
        
        for price in prices:
            if abs(float(price.close) - avg) <= threshold:
                filtered.append(price)
            else:
                logger.warning(f"Removed outlier price {price.close} from {price.source} for {price.symbol}")
        
        return filtered if filtered else prices
    
    def validate_aggregated_price(self, agg_price: AggregatedPrice) -> bool:
        """Validate that aggregated price meets quality thresholds"""
        if agg_price.source_count < self.min_sources:
            logger.warning(f"Low source count: {agg_price.source_count}")
        
        if float(agg_price.price_variance) > self.max_variance_percent:
            logger.warning(f"High variance: {agg_price.price_variance}%")
            return False
        
        if agg_price.confidence_score < self.min_confidence:
            logger.warning(f"Low confidence: {agg_price.confidence_score}")
            return False
        
        return True
    
    async def aggregate_multi_symbol(
        self, 
        price_dict: Dict[str, List[StockPrice]]
    ) -> Dict[str, Optional[AggregatedPrice]]:
        """Aggregate prices for multiple symbols"""
        results = {}
        
        for symbol, prices in price_dict.items():
            if prices:
                agg = self.aggregate_prices(prices)
                results[symbol] = agg
            else:
                results[symbol] = None
        
        return results
