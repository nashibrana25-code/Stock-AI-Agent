"""
Capital-aware recommendation engine for ASX stocks

This engine provides personalized investment recommendations based on:
- Available capital ($50 - $10,000)
- Risk tolerance
- Investment strategy
- Market conditions
- AI predictions
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from loguru import logger
import uuid

from shared.models.financial_models import (
    PortfolioConstraints, StockRecommendation, PortfolioRecommendation,
    OrderType, RiskLevel, InvestmentStrategy, PricePrediction,
    TechnicalIndicators, SentimentAnalysis, AggregatedPrice
)
from shared.config.settings import recommendation_config


class CapitalAwareRecommendationEngine:
    """
    Generates investment recommendations tailored to specific capital amounts
    """
    
    def __init__(self):
        self.config = recommendation_config
    
    async def generate_recommendation(
        self,
        constraints: PortfolioConstraints,
        available_stocks: List[str],
        predictions: Dict[str, PricePrediction],
        current_prices: Dict[str, AggregatedPrice],
        technical_indicators: Dict[str, TechnicalIndicators],
        sentiment_data: Dict[str, SentimentAnalysis]
    ) -> PortfolioRecommendation:
        """
        Generate personalized portfolio recommendations
        
        Args:
            constraints: User's portfolio constraints and preferences
            available_stocks: List of stock symbols to consider
            predictions: AI price predictions for each stock
            current_prices: Current aggregated prices
            technical_indicators: Technical analysis data
            sentiment_data: Sentiment analysis data
        """
        logger.info(f"Generating recommendations for capital: ${constraints.total_capital}")
        
        # Determine portfolio tier and strategy
        tier = self._determine_capital_tier(constraints.total_capital)
        max_positions = self._get_max_positions(tier)
        
        # Score all available stocks
        stock_scores = await self._score_stocks(
            available_stocks,
            predictions,
            current_prices,
            technical_indicators,
            sentiment_data,
            constraints
        )
        
        # Select top stocks based on capital tier
        selected_stocks = self._select_stocks(
            stock_scores,
            max_positions,
            constraints
        )
        
        # Calculate position sizes
        recommendations = await self._calculate_positions(
            selected_stocks,
            constraints,
            current_prices,
            predictions,
            technical_indicators,
            sentiment_data
        )
        
        # Build portfolio recommendation
        portfolio_rec = await self._build_portfolio_recommendation(
            constraints,
            recommendations,
            current_prices
        )
        
        return portfolio_rec
    
    def _determine_capital_tier(self, capital: Decimal) -> int:
        """Determine which capital tier the portfolio falls into"""
        if capital <= self.config.tier_1_max:
            return 1  # $50-500: Micro portfolio
        elif capital <= self.config.tier_2_max:
            return 2  # $500-2000: Small portfolio
        elif capital <= self.config.tier_3_max:
            return 3  # $2000-5000: Medium portfolio
        else:
            return 4  # $5000-10000: Large portfolio
    
    def _get_max_positions(self, tier: int) -> int:
        """Get maximum number of positions for capital tier"""
        tier_limits = {
            1: self.config.tier_1_max_positions,  # 1 position
            2: self.config.tier_2_max_positions,  # 3 positions
            3: self.config.tier_3_max_positions,  # 7 positions
            4: self.config.tier_4_max_positions,  # 15 positions
        }
        return tier_limits.get(tier, 3)
    
    def _get_max_risk_for_tier(self, tier: int) -> float:
        """Get maximum risk score allowed for tier"""
        tier_risks = {
            1: self.config.tier_1_max_risk_score,  # 0.5
            2: self.config.tier_2_max_risk_score,  # 0.6
            3: self.config.tier_3_max_risk_score,  # 0.7
            4: self.config.tier_4_max_risk_score,  # 0.8
        }
        return tier_risks.get(tier, 0.6)
    
    async def _score_stocks(
        self,
        symbols: List[str],
        predictions: Dict[str, PricePrediction],
        prices: Dict[str, AggregatedPrice],
        indicators: Dict[str, TechnicalIndicators],
        sentiment: Dict[str, SentimentAnalysis],
        constraints: PortfolioConstraints
    ) -> Dict[str, Dict]:
        """
        Score each stock based on multiple factors
        
        Returns dict with symbol -> {score, details}
        """
        scores = {}
        
        for symbol in symbols:
            try:
                score_data = await self._calculate_stock_score(
                    symbol,
                    predictions.get(symbol),
                    prices.get(symbol),
                    indicators.get(symbol),
                    sentiment.get(symbol),
                    constraints
                )
                scores[symbol] = score_data
            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
        
        return scores
    
    async def _calculate_stock_score(
        self,
        symbol: str,
        prediction: Optional[PricePrediction],
        price: Optional[AggregatedPrice],
        indicator: Optional[TechnicalIndicators],
        sent: Optional[SentimentAnalysis],
        constraints: PortfolioConstraints
    ) -> Dict:
        """Calculate comprehensive score for a single stock"""
        
        if not price or not prediction:
            return {"score": 0, "reason": "Insufficient data"}
        
        scores = {}
        weights = {}
        
        # 1. AI Prediction Score (35% weight)
        pred_return = ((prediction.predicted_price - price.consensus_price) / 
                       price.consensus_price * 100)
        scores['prediction'] = min(float(pred_return) / 20.0, 1.0)  # Normalize to 0-1
        scores['prediction_confidence'] = prediction.confidence_score
        weights['prediction'] = 0.35
        
        # 2. Technical Analysis Score (25% weight)
        if indicator:
            tech_score = self._calculate_technical_score(indicator, price.consensus_price)
            scores['technical'] = tech_score
            weights['technical'] = 0.25
        else:
            scores['technical'] = 0.5
            weights['technical'] = 0.15
        
        # 3. Sentiment Score (20% weight)
        if sent:
            scores['sentiment'] = (sent.sentiment_score + 1) / 2  # Convert -1,1 to 0,1
            weights['sentiment'] = 0.20
        else:
            scores['sentiment'] = 0.5
            weights['sentiment'] = 0.10
        
        # 4. Risk Assessment (20% weight) - inverse score
        risk_score = await self._calculate_risk_score(symbol, indicator, price)
        scores['risk'] = 1 - risk_score  # Lower risk = higher score
        weights['risk'] = 0.20
        
        # Calculate weighted total score
        total_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        # Adjust based on investment strategy
        total_score = self._adjust_for_strategy(
            total_score, 
            risk_score, 
            pred_return,
            constraints.investment_strategy
        )
        
        return {
            "score": round(total_score, 4),
            "risk_score": round(risk_score, 4),
            "predicted_return": round(float(pred_return), 2),
            "confidence": prediction.confidence_score,
            "component_scores": scores,
            "reasoning": self._generate_reasoning(scores, pred_return, risk_score)
        }
    
    def _calculate_technical_score(
        self, 
        indicator: TechnicalIndicators, 
        current_price: Decimal
    ) -> float:
        """Calculate score based on technical indicators"""
        score = 0.5  # Neutral baseline
        signals = []
        
        # RSI analysis
        if indicator.rsi:
            rsi = float(indicator.rsi)
            if rsi < 30:
                signals.append(0.8)  # Oversold - bullish
            elif rsi > 70:
                signals.append(0.2)  # Overbought - bearish
            else:
                signals.append(0.5 + (50 - rsi) / 100)  # Normalize
        
        # Moving average analysis
        if indicator.sma_50 and indicator.sma_200:
            if indicator.sma_50 > indicator.sma_200:
                signals.append(0.7)  # Golden cross territory
            else:
                signals.append(0.3)  # Death cross territory
        
        # MACD
        if indicator.macd and indicator.macd_signal:
            if indicator.macd > indicator.macd_signal:
                signals.append(0.7)  # Bullish
            else:
                signals.append(0.3)  # Bearish
        
        # Bollinger Bands
        if indicator.bollinger_lower and indicator.bollinger_upper:
            bb_position = ((current_price - indicator.bollinger_lower) / 
                          (indicator.bollinger_upper - indicator.bollinger_lower))
            # Near lower band = oversold (bullish), near upper = overbought (bearish)
            signals.append(1 - float(bb_position))
        
        return sum(signals) / len(signals) if signals else 0.5
    
    async def _calculate_risk_score(
        self,
        symbol: str,
        indicator: Optional[TechnicalIndicators],
        price: AggregatedPrice
    ) -> float:
        """Calculate risk score (0 = low risk, 1 = high risk)"""
        risk_factors = []
        
        # Price variance risk
        variance_risk = min(float(price.price_variance) / 5.0, 1.0)
        risk_factors.append(variance_risk)
        
        # Volatility risk (ATR)
        if indicator and indicator.atr:
            atr_percent = float(indicator.atr) / float(price.consensus_price) * 100
            volatility_risk = min(atr_percent / 10.0, 1.0)
            risk_factors.append(volatility_risk)
        
        # Confidence risk
        confidence_risk = 1 - price.confidence_score
        risk_factors.append(confidence_risk)
        
        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.5
    
    def _adjust_for_strategy(
        self,
        base_score: float,
        risk_score: float,
        predicted_return: float,
        strategy: InvestmentStrategy
    ) -> float:
        """Adjust score based on investment strategy"""
        
        if strategy == InvestmentStrategy.CONSERVATIVE:
            # Penalize high risk, favor stability
            if risk_score > 0.6:
                base_score *= 0.7
            if predicted_return < 5:
                base_score *= 1.1  # Favor modest gains
        
        elif strategy == InvestmentStrategy.GROWTH:
            # Favor higher returns, tolerate more risk
            if predicted_return > 15:
                base_score *= 1.2
            if risk_score < 0.3:
                base_score *= 0.9  # Slightly penalize very low risk
        
        elif strategy == InvestmentStrategy.AGGRESSIVE:
            # Maximize returns, high risk tolerance
            if predicted_return > 20:
                base_score *= 1.3
            # Don't penalize high risk
        
        else:  # BALANCED
            # Keep balanced approach
            if 10 < predicted_return < 20 and 0.3 < risk_score < 0.6:
                base_score *= 1.1
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def _generate_reasoning(
        self,
        scores: Dict[str, float],
        predicted_return: float,
        risk_score: float
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        if scores.get('prediction', 0) > 0.7:
            reasons.append(f"Strong AI prediction (+{predicted_return:.1f}% expected return)")
        elif scores.get('prediction', 0) < 0.3:
            reasons.append("Weak growth outlook")
        
        if scores.get('technical', 0) > 0.6:
            reasons.append("Favorable technical indicators")
        elif scores.get('technical', 0) < 0.4:
            reasons.append("Bearish technical signals")
        
        if scores.get('sentiment', 0) > 0.6:
            reasons.append("Positive market sentiment")
        elif scores.get('sentiment', 0) < 0.4:
            reasons.append("Negative sentiment concerns")
        
        if risk_score < 0.3:
            reasons.append("Low risk profile")
        elif risk_score > 0.7:
            reasons.append("High volatility risk")
        
        return "; ".join(reasons) if reasons else "Neutral outlook"
    
    def _select_stocks(
        self,
        scored_stocks: Dict[str, Dict],
        max_positions: int,
        constraints: PortfolioConstraints
    ) -> List[Tuple[str, Dict]]:
        """Select top stocks for portfolio"""
        
        # Filter by maximum risk for capital tier
        tier = self._determine_capital_tier(constraints.total_capital)
        max_risk = self._get_max_risk_for_tier(tier)
        
        # Filter and sort
        eligible_stocks = [
            (symbol, data) for symbol, data in scored_stocks.items()
            if data.get('risk_score', 1.0) <= max_risk
            and data.get('score', 0) > 0.3  # Minimum score threshold
        ]
        
        # Sort by score descending
        eligible_stocks.sort(key=lambda x: x[1]['score'], reverse=True)
        
        # Apply sector diversification
        selected = self._apply_sector_diversification(
            eligible_stocks[:max_positions * 2],  # Consider 2x positions for diversity
            max_positions,
            constraints
        )
        
        return selected[:max_positions]
    
    def _apply_sector_diversification(
        self,
        candidates: List[Tuple[str, Dict]],
        max_positions: int,
        constraints: PortfolioConstraints
    ) -> List[Tuple[str, Dict]]:
        """Ensure sector diversification in selection"""
        # This is simplified - in production, would fetch actual sector data
        # For now, take top scored stocks
        return candidates[:max_positions]
    
    async def _calculate_positions(
        self,
        selected_stocks: List[Tuple[str, Dict]],
        constraints: PortfolioConstraints,
        prices: Dict[str, AggregatedPrice],
        predictions: Dict[str, PricePrediction],
        indicators: Dict[str, TechnicalIndicators],
        sentiment: Dict[str, SentimentAnalysis]
    ) -> List[StockRecommendation]:
        """Calculate position sizes for selected stocks"""
        
        recommendations = []
        total_capital = constraints.total_capital
        tier = self._determine_capital_tier(total_capital)
        
        # Account for transaction costs
        estimated_trades = len(selected_stocks)
        total_fees = Decimal(str(self.config.brokerage_fee_fixed * estimated_trades))
        investable_capital = total_capital - total_fees
        
        # Calculate allocations
        allocations = self._calculate_allocations(
            selected_stocks,
            investable_capital,
            constraints
        )
        
        for (symbol, score_data), allocation in zip(selected_stocks, allocations):
            price_data = prices[symbol]
            prediction = predictions[symbol]
            
            shares = int(allocation / price_data.consensus_price)
            
            if shares == 0:
                continue  # Skip if can't afford even 1 share
            
            actual_allocation = Decimal(shares) * price_data.consensus_price
            
            recommendation = StockRecommendation(
                symbol=symbol,
                company_name=f"Company {symbol}",  # Would fetch from database
                action=OrderType.BUY,
                current_price=price_data.consensus_price,
                target_price=prediction.predicted_price,
                predicted_return=Decimal(str(score_data['predicted_return'])),
                confidence_score=score_data['confidence'],
                risk_score=score_data['risk_score'],
                recommended_allocation=actual_allocation,
                recommended_shares=shares,
                reasoning=score_data['reasoning'],
                key_metrics={
                    "ai_score": score_data['score'],
                    "technical_score": score_data['component_scores'].get('technical', 0),
                    "sentiment_score": score_data['component_scores'].get('sentiment', 0)
                },
                sentiment_summary=self._get_sentiment_summary(sentiment.get(symbol)),
                technical_summary=self._get_technical_summary(indicators.get(symbol))
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_allocations(
        self,
        selected_stocks: List[Tuple[str, Dict]],
        investable_capital: Decimal,
        constraints: PortfolioConstraints
    ) -> List[Decimal]:
        """Calculate capital allocation for each stock"""
        
        tier = self._determine_capital_tier(constraints.total_capital)
        
        if tier == 1:
            # Micro portfolio: all-in on best pick
            return [investable_capital]
        
        elif tier == 2:
            # Small portfolio: equal weighting with slight tilt to top pick
            weights = [0.40, 0.35, 0.25][:len(selected_stocks)]
        
        elif tier in [3, 4]:
            # Medium/Large: Score-based weighting
            scores = [s[1]['score'] for s in selected_stocks]
            total_score = sum(scores)
            weights = [s / total_score for s in scores]
        
        else:
            # Default: equal weighting
            weights = [1.0 / len(selected_stocks)] * len(selected_stocks)
        
        # Apply max single stock percentage limit
        max_allocation = float(investable_capital) * constraints.max_single_stock_percentage
        allocations = [
            min(Decimal(str(w * float(investable_capital))), Decimal(str(max_allocation)))
            for w in weights
        ]
        
        return allocations
    
    def _get_sentiment_summary(self, sentiment: Optional[SentimentAnalysis]) -> str:
        """Generate sentiment summary"""
        if not sentiment:
            return "No sentiment data available"
        
        return f"{sentiment.overall_sentiment.value.replace('_', ' ').title()} " \
               f"({sentiment.news_count} news articles, " \
               f"{sentiment.social_media_mentions} social mentions)"
    
    def _get_technical_summary(self, indicator: Optional[TechnicalIndicators]) -> str:
        """Generate technical summary"""
        if not indicator:
            return "No technical data available"
        
        signals = []
        if indicator.rsi:
            if indicator.rsi < 30:
                signals.append("Oversold")
            elif indicator.rsi > 70:
                signals.append("Overbought")
        
        if indicator.macd and indicator.macd_signal:
            if indicator.macd > indicator.macd_signal:
                signals.append("MACD bullish")
            else:
                signals.append("MACD bearish")
        
        return ", ".join(signals) if signals else "Neutral technical outlook"
    
    async def _build_portfolio_recommendation(
        self,
        constraints: PortfolioConstraints,
        recommendations: List[StockRecommendation],
        prices: Dict[str, AggregatedPrice]
    ) -> PortfolioRecommendation:
        """Build final portfolio recommendation"""
        
        total_investment = sum(r.recommended_allocation for r in recommendations)
        cash_reserve = constraints.total_capital - total_investment
        
        # Calculate expected return
        weighted_returns = [
            float(r.predicted_return) * float(r.recommended_allocation) 
            for r in recommendations
        ]
        expected_return = Decimal(str(sum(weighted_returns) / float(total_investment))) \
            if total_investment > 0 else Decimal(0)
        
        # Calculate portfolio risk
        weighted_risks = [
            r.risk_score * float(r.recommended_allocation) 
            for r in recommendations
        ]
        portfolio_risk = sum(weighted_risks) / float(total_investment) \
            if total_investment > 0 else 0
        
        # Diversification score
        diversification = min(len(recommendations) / 10, 1.0)
        
        # Sector allocation (simplified)
        sector_allocation = {}  # Would calculate from actual data
        
        # Generate summary
        summary = self._generate_portfolio_summary(
            constraints,
            recommendations,
            expected_return,
            portfolio_risk
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            constraints,
            recommendations,
            total_investment,
            portfolio_risk
        )
        
        return PortfolioRecommendation(
            recommendation_id=str(uuid.uuid4()),
            generated_at=datetime.utcnow(),
            constraints=constraints,
            recommendations=recommendations,
            total_investment=total_investment,
            expected_return=expected_return,
            portfolio_risk_score=portfolio_risk,
            diversification_score=diversification,
            sector_allocation=sector_allocation,
            cash_reserve=cash_reserve,
            summary=summary,
            warnings=warnings
        )
    
    def _generate_portfolio_summary(
        self,
        constraints: PortfolioConstraints,
        recommendations: List[StockRecommendation],
        expected_return: Decimal,
        risk_score: float
    ) -> str:
        """Generate portfolio summary"""
        tier = self._determine_capital_tier(constraints.total_capital)
        tier_names = {1: "Micro", 2: "Small", 3: "Medium", 4: "Large"}
        
        return (
            f"{tier_names.get(tier, 'Standard')} portfolio for ${constraints.total_capital}. "
            f"Recommending {len(recommendations)} stock(s) with expected return of "
            f"{expected_return:.1f}% and {self._risk_level_name(risk_score)} risk profile. "
            f"Strategy: {constraints.investment_strategy.value}."
        )
    
    def _risk_level_name(self, risk_score: float) -> str:
        """Convert risk score to name"""
        if risk_score < 0.3:
            return "low"
        elif risk_score < 0.5:
            return "moderate"
        elif risk_score < 0.7:
            return "elevated"
        else:
            return "high"
    
    def _generate_warnings(
        self,
        constraints: PortfolioConstraints,
        recommendations: List[StockRecommendation],
        total_investment: Decimal,
        risk_score: float
    ) -> List[str]:
        """Generate portfolio warnings"""
        warnings = []
        
        if len(recommendations) < constraints.min_diversification:
            warnings.append(
                f"Limited diversification: only {len(recommendations)} stock(s)"
            )
        
        if risk_score > 0.7:
            warnings.append("High-risk portfolio - consider diversifying")
        
        cash_percent = float((constraints.total_capital - total_investment) / 
                            constraints.total_capital * 100)
        if cash_percent > 20:
            warnings.append(f"Large cash reserve: {cash_percent:.1f}% uninvested")
        
        return warnings
