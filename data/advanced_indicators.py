"""
Advanced Technical Indicators and Market Microstructure Analysis
Includes VWAP, Order Flow, Volume Profile, and Market Regime Detection
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketMicrostructure:
    """Market microstructure metrics"""
    bid_ask_spread: float
    order_flow_imbalance: float
    volume_profile_poc: float  # Point of Control
    vwap: float
    twap: float
    depth_imbalance: float
    tick_rule: int  # 1 for uptick, -1 for downtick
    
@dataclass  
class MarketRegime:
    """Market regime classification"""
    regime: str  # 'trending_up', 'trending_down', 'ranging', 'volatile'
    strength: float
    volatility_percentile: float
    trend_strength: float

class AdvancedIndicators:
    """
    Professional-grade technical indicators for algorithmic trading
    """
    
    @staticmethod
    def calculate_vwap(prices: np.ndarray, 
                       volumes: np.ndarray, 
                       period: Optional[int] = None) -> float:
        """
        Calculate Volume Weighted Average Price
        
        VWAP = Σ(Price * Volume) / Σ(Volume)
        """
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0
            
        if period:
            prices = prices[-period:]
            volumes = volumes[-period:]
            
        total_volume = np.sum(volumes)
        if total_volume == 0:
            return np.mean(prices)
            
        return np.sum(prices * volumes) / total_volume
    
    @staticmethod
    def calculate_twap(prices: np.ndarray, period: Optional[int] = None) -> float:
        """
        Calculate Time Weighted Average Price
        """
        if len(prices) == 0:
            return 0.0
            
        if period:
            prices = prices[-period:]
            
        return np.mean(prices)
    
    @staticmethod
    def calculate_order_flow_imbalance(bid_volume: float, 
                                      ask_volume: float,
                                      delta_threshold: float = 0.3) -> Dict[str, float]:
        """
        Calculate order flow imbalance to detect buying/selling pressure
        
        Returns:
            Dictionary with imbalance metrics
        """
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return {'imbalance': 0, 'ratio': 0, 'signal': 0}
        
        # Raw imbalance (-1 to 1)
        imbalance = (bid_volume - ask_volume) / total_volume
        
        # Volume ratio
        ratio = bid_volume / ask_volume if ask_volume > 0 else float('inf')
        
        # Generate signal
        if abs(imbalance) > delta_threshold:
            signal = 1 if imbalance > 0 else -1
        else:
            signal = 0
            
        return {
            'imbalance': imbalance,
            'ratio': ratio,
            'signal': signal,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'total_volume': total_volume
        }
    
    @staticmethod
    def calculate_volume_profile(prices: np.ndarray, 
                                volumes: np.ndarray,
                                bins: int = 20) -> Dict[str, Union[float, np.ndarray]]:
        """
        Calculate volume profile to identify key price levels
        
        Returns:
            Dictionary with POC (Point of Control), VAH, VAL, and profile
        """
        if len(prices) == 0 or len(volumes) == 0:
            return {'poc': 0, 'vah': 0, 'val': 0, 'profile': np.array([])}
        
        # Create price bins
        price_range = np.linspace(prices.min(), prices.max(), bins)
        volume_profile = np.zeros(bins - 1)
        
        # Accumulate volume in each price bin
        for i, price in enumerate(prices):
            bin_idx = np.searchsorted(price_range, price) - 1
            if 0 <= bin_idx < len(volume_profile):
                volume_profile[bin_idx] += volumes[i]
        
        # Find Point of Control (price with highest volume)
        poc_idx = np.argmax(volume_profile)
        poc = (price_range[poc_idx] + price_range[poc_idx + 1]) / 2
        
        # Calculate Value Area (70% of volume)
        total_volume = np.sum(volume_profile)
        value_area_volume = total_volume * 0.7
        
        # Expand from POC to find value area
        cumulative_volume = volume_profile[poc_idx]
        upper_idx = poc_idx
        lower_idx = poc_idx
        
        while cumulative_volume < value_area_volume:
            # Check which side to expand
            upper_vol = volume_profile[upper_idx + 1] if upper_idx < len(volume_profile) - 1 else 0
            lower_vol = volume_profile[lower_idx - 1] if lower_idx > 0 else 0
            
            if upper_vol > lower_vol and upper_idx < len(volume_profile) - 1:
                upper_idx += 1
                cumulative_volume += upper_vol
            elif lower_idx > 0:
                lower_idx -= 1
                cumulative_volume += lower_vol
            else:
                break
        
        # Value Area High and Low
        vah = price_range[min(upper_idx + 1, len(price_range) - 1)]
        val = price_range[max(lower_idx, 0)]
        
        return {
            'poc': poc,
            'vah': vah,
            'val': val,
            'profile': volume_profile,
            'price_levels': price_range
        }
    
    @staticmethod
    def calculate_market_depth_imbalance(bid_depth: List[Tuple[float, float]], 
                                        ask_depth: List[Tuple[float, float]],
                                        levels: int = 5) -> float:
        """
        Calculate order book imbalance from market depth
        
        Args:
            bid_depth: List of (price, size) tuples
            ask_depth: List of (price, size) tuples
            levels: Number of levels to analyze
            
        Returns:
            Depth imbalance ratio (-1 to 1)
        """
        # Sum bid and ask volumes for top levels
        bid_volume = sum(size for _, size in bid_depth[:levels])
        ask_volume = sum(size for _, size in ask_depth[:levels])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0
            
        return (bid_volume - ask_volume) / total_volume
    
    @staticmethod
    def detect_market_regime(prices: np.ndarray, 
                           returns: np.ndarray,
                           lookback: int = 50) -> MarketRegime:
        """
        Detect current market regime using statistical methods
        """
        if len(prices) < lookback:
            return MarketRegime('unknown', 0, 0, 0)
        
        recent_prices = prices[-lookback:]
        recent_returns = returns[-lookback:]
        
        # Calculate trend using linear regression
        x = np.arange(len(recent_prices))
        slope, intercept, r_value, _, _ = stats.linregress(x, recent_prices)
        
        # Normalize slope by price level
        normalized_slope = slope / np.mean(recent_prices)
        
        # Calculate volatility
        volatility = np.std(recent_returns)
        historical_vol = np.std(returns) if len(returns) > lookback else volatility
        vol_percentile = stats.percentileofscore(
            returns[-252:] if len(returns) > 252 else returns, 
            volatility
        )
        
        # Determine regime
        trend_threshold = 0.001  # 0.1% per period
        r_squared = r_value ** 2
        
        if r_squared > 0.7:  # Strong trend
            if normalized_slope > trend_threshold:
                regime = 'trending_up'
            elif normalized_slope < -trend_threshold:
                regime = 'trending_down'
            else:
                regime = 'ranging'
        elif vol_percentile > 80:  # High volatility
            regime = 'volatile'
        else:
            regime = 'ranging'
        
        return MarketRegime(
            regime=regime,
            strength=r_squared,
            volatility_percentile=vol_percentile,
            trend_strength=abs(normalized_slope)
        )
    
    @staticmethod
    def calculate_tick_rule(current_price: float, 
                           previous_price: float,
                           current_tick: int = 0) -> int:
        """
        Lee-Ready tick rule for trade classification
        Returns: 1 for buy, -1 for sell, 0 for unchanged
        """
        if current_price > previous_price:
            return 1
        elif current_price < previous_price:
            return -1
        else:
            return current_tick  # Maintain previous tick
    
    @staticmethod
    def calculate_accumulation_distribution(high: np.ndarray,
                                          low: np.ndarray,
                                          close: np.ndarray,
                                          volume: np.ndarray) -> np.ndarray:
        """
        Calculate Accumulation/Distribution Line
        """
        if len(high) == 0:
            return np.array([])
            
        # Money Flow Multiplier
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = np.nan_to_num(mfm, 0)  # Handle division by zero
        
        # Money Flow Volume
        mfv = mfm * volume
        
        # Accumulation/Distribution Line
        ad_line = np.cumsum(mfv)
        
        return ad_line
    
    @staticmethod
    def calculate_obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Calculate On-Balance Volume
        """
        if len(close) < 2:
            return np.array([])
            
        # Price changes
        price_diff = np.diff(close)
        
        # Volume direction
        volume_direction = np.sign(price_diff)
        
        # OBV
        obv = np.concatenate([[0], np.cumsum(volume_direction * volume[1:])])
        
        return obv
    
    @staticmethod
    def calculate_market_microstructure(prices: np.ndarray,
                                       volumes: np.ndarray,
                                       bid_prices: np.ndarray,
                                       ask_prices: np.ndarray,
                                       bid_volumes: np.ndarray,
                                       ask_volumes: np.ndarray) -> MarketMicrostructure:
        """
        Calculate comprehensive market microstructure metrics
        """
        # Bid-ask spread
        current_bid = bid_prices[-1] if len(bid_prices) > 0 else 0
        current_ask = ask_prices[-1] if len(ask_prices) > 0 else 0
        spread = current_ask - current_bid
        
        # Order flow imbalance
        bid_vol = np.sum(bid_volumes[-10:]) if len(bid_volumes) >= 10 else np.sum(bid_volumes)
        ask_vol = np.sum(ask_volumes[-10:]) if len(ask_volumes) >= 10 else np.sum(ask_volumes)
        flow_imbalance = AdvancedIndicators.calculate_order_flow_imbalance(bid_vol, ask_vol)
        
        # Volume Profile
        vol_profile = AdvancedIndicators.calculate_volume_profile(prices, volumes)
        
        # VWAP and TWAP
        vwap = AdvancedIndicators.calculate_vwap(prices, volumes)
        twap = AdvancedIndicators.calculate_twap(prices)
        
        # Depth imbalance (simplified)
        depth_imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol) if (bid_vol + ask_vol) > 0 else 0
        
        # Tick rule
        tick = AdvancedIndicators.calculate_tick_rule(
            prices[-1] if len(prices) > 0 else 0,
            prices[-2] if len(prices) > 1 else 0
        )
        
        return MarketMicrostructure(
            bid_ask_spread=spread,
            order_flow_imbalance=flow_imbalance['imbalance'],
            volume_profile_poc=vol_profile['poc'],
            vwap=vwap,
            twap=twap,
            depth_imbalance=depth_imbalance,
            tick_rule=tick
        )
    
    @staticmethod
    def calculate_support_resistance(prices: np.ndarray, 
                                    volumes: np.ndarray,
                                    window: int = 20,
                                    num_levels: int = 3) -> Dict[str, List[float]]:
        """
        Identify support and resistance levels using volume and price action
        """
        if len(prices) < window:
            return {'support': [], 'resistance': []}
        
        # Find local maxima and minima
        from scipy.signal import argrelextrema
        
        local_max = argrelextrema(prices, np.greater, order=window//2)[0]
        local_min = argrelextrema(prices, np.less, order=window//2)[0]
        
        # Weight by volume
        resistance_levels = []
        for idx in local_max:
            if idx < len(volumes):
                level = prices[idx]
                volume_weight = volumes[idx] / np.mean(volumes)
                resistance_levels.append((level, volume_weight))
        
        support_levels = []
        for idx in local_min:
            if idx < len(volumes):
                level = prices[idx]
                volume_weight = volumes[idx] / np.mean(volumes)
                support_levels.append((level, volume_weight))
        
        # Sort by volume weight and get top levels
        resistance_levels.sort(key=lambda x: x[1], reverse=True)
        support_levels.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'resistance': [level for level, _ in resistance_levels[:num_levels]],
            'support': [level for level, _ in support_levels[:num_levels]]
        }
    
    @staticmethod
    def calculate_momentum_indicators(prices: np.ndarray, 
                                    volumes: np.ndarray,
                                    period: int = 14) -> Dict[str, float]:
        """
        Calculate advanced momentum indicators
        """
        if len(prices) < period:
            return {
                'roc': 0,
                'mfi': 50,
                'cmf': 0,
                'rvi': 0
            }
        
        # Rate of Change (ROC)
        roc = ((prices[-1] - prices[-period]) / prices[-period]) * 100 if prices[-period] != 0 else 0
        
        # Money Flow Index (MFI)
        typical_price = prices  # Simplified, should use (high+low+close)/3
        raw_money_flow = typical_price * volumes
        
        positive_flow = np.sum(raw_money_flow[prices > np.roll(prices, 1)])
        negative_flow = np.sum(raw_money_flow[prices < np.roll(prices, 1)])
        
        if negative_flow == 0:
            mfi = 100
        else:
            money_ratio = positive_flow / negative_flow
            mfi = 100 - (100 / (1 + money_ratio))
        
        # Chaikin Money Flow (CMF) - simplified
        cmf = np.sum(volumes * np.sign(prices - np.roll(prices, 1))) / np.sum(volumes) if np.sum(volumes) > 0 else 0
        
        # Relative Vigor Index (RVI) - simplified
        close_open = prices - np.roll(prices, 1)
        high_low = np.abs(close_open)  # Simplified
        
        rvi = np.sum(close_open[-period:]) / np.sum(high_low[-period:]) if np.sum(high_low[-period:]) > 0 else 0
        
        return {
            'roc': roc,
            'mfi': mfi,
            'cmf': cmf,
            'rvi': rvi
        }
