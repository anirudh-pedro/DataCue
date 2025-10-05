"""
Time Series Forecaster
Provides time series forecasting using ARIMA, SARIMA, and Prophet.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeSeriesForecaster:
    """
    Time series forecasting with automatic model selection.
    
    Supported Models:
    - ARIMA (AutoRegressive Integrated Moving Average)
    - SARIMA (Seasonal ARIMA)
    - Prophet (Facebook's forecasting library)
    - Exponential Smoothing
    """
    
    def __init__(self):
        """Initialize time series forecaster"""
        self.statsmodels_available = self._check_statsmodels()
        self.prophet_available = self._check_prophet()
    
    def _check_statsmodels(self) -> bool:
        """Check if statsmodels is available"""
        try:
            import statsmodels.api as sm
            return True
        except ImportError:
            logger.warning("statsmodels not installed. Install with: pip install statsmodels")
            return False
    
    def _check_prophet(self) -> bool:
        """Check if Prophet is available"""
        try:
            import prophet
            return True
        except ImportError:
            logger.info("Prophet not installed. Install with: pip install prophet")
            return False
    
    def forecast(
        self,
        data: pd.Series,
        periods: int,
        method: str = 'auto',
        seasonal: bool = True,
        seasonal_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate time series forecast.
        
        Args:
            data: Time series data (pandas Series with datetime index)
            periods: Number of periods to forecast
            method: 'arima', 'sarima', 'prophet', 'exponential', or 'auto'
            seasonal: Whether to model seasonality
            seasonal_period: Seasonal period (auto-detected if None)
            
        Returns:
            Dictionary with forecasts and model info
        """
        # Auto-detect seasonality
        if seasonal and seasonal_period is None:
            seasonal_period = self._detect_seasonality(data)
        
        # Auto-select method
        if method == 'auto':
            method = self._select_method(data, seasonal, seasonal_period)
        
        logger.info(f"   Forecasting {periods} periods using {method}")
        
        # Generate forecast
        if method == 'arima':
            return self._forecast_arima(data, periods, seasonal=False)
        elif method == 'sarima':
            return self._forecast_sarima(data, periods, seasonal_period)
        elif method == 'prophet':
            return self._forecast_prophet(data, periods)
        elif method == 'exponential':
            return self._forecast_exponential(data, periods, seasonal, seasonal_period)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _forecast_arima(
        self,
        data: pd.Series,
        periods: int,
        seasonal: bool = False
    ) -> Dict[str, Any]:
        """Forecast using ARIMA"""
        if not self.statsmodels_available:
            return {'error': 'statsmodels not available'}
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller
            
            # Determine differencing order
            adf_result = adfuller(data.dropna())
            d = 0 if adf_result[1] < 0.05 else 1
            
            # Auto-select order (simple heuristic)
            order = (1, d, 1)
            
            logger.info(f"   Fitting ARIMA{order}")
            
            # Fit model
            model = ARIMA(data, order=order)
            fitted_model = model.fit()
            
            # Forecast
            forecast = fitted_model.forecast(steps=periods)
            
            # Get confidence intervals
            forecast_result = fitted_model.get_forecast(steps=periods)
            conf_int = forecast_result.conf_int()
            
            return {
                'method': 'arima',
                'order': order,
                'forecast': forecast.tolist(),
                'conf_lower': conf_int.iloc[:, 0].tolist(),
                'conf_upper': conf_int.iloc[:, 1].tolist(),
                'aic': float(fitted_model.aic),
                'bic': float(fitted_model.bic)
            }
            
        except Exception as e:
            logger.error(f"   ARIMA forecast failed: {str(e)}")
            return {'error': str(e)}
    
    def _forecast_sarima(
        self,
        data: pd.Series,
        periods: int,
        seasonal_period: Optional[int]
    ) -> Dict[str, Any]:
        """Forecast using SARIMA"""
        if not self.statsmodels_available:
            return {'error': 'statsmodels not available'}
        
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
            
            # Default seasonal period
            if seasonal_period is None:
                seasonal_period = 12
            
            # Simple order selection
            order = (1, 1, 1)
            seasonal_order = (1, 1, 1, seasonal_period)
            
            logger.info(f"   Fitting SARIMA{order}x{seasonal_order}")
            
            # Fit model
            model = SARIMAX(data, order=order, seasonal_order=seasonal_order)
            fitted_model = model.fit(disp=False)
            
            # Forecast
            forecast = fitted_model.forecast(steps=periods)
            forecast_result = fitted_model.get_forecast(steps=periods)
            conf_int = forecast_result.conf_int()
            
            return {
                'method': 'sarima',
                'order': order,
                'seasonal_order': seasonal_order,
                'forecast': forecast.tolist(),
                'conf_lower': conf_int.iloc[:, 0].tolist(),
                'conf_upper': conf_int.iloc[:, 1].tolist(),
                'aic': float(fitted_model.aic),
                'bic': float(fitted_model.bic)
            }
            
        except Exception as e:
            logger.error(f"   SARIMA forecast failed: {str(e)}")
            return {'error': str(e)}
    
    def _forecast_prophet(
        self,
        data: pd.Series,
        periods: int
    ) -> Dict[str, Any]:
        """Forecast using Facebook Prophet"""
        if not self.prophet_available:
            return {'error': 'Prophet not available'}
        
        try:
            from prophet import Prophet
            
            # Prepare data for Prophet
            df = pd.DataFrame({
                'ds': data.index,
                'y': data.values
            })
            
            # Fit model
            model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods)
            
            # Forecast
            forecast = model.predict(future)
            
            # Extract forecast values
            forecast_values = forecast['yhat'].iloc[-periods:].tolist()
            conf_lower = forecast['yhat_lower'].iloc[-periods:].tolist()
            conf_upper = forecast['yhat_upper'].iloc[-periods:].tolist()
            
            return {
                'method': 'prophet',
                'forecast': forecast_values,
                'conf_lower': conf_lower,
                'conf_upper': conf_upper,
                'trend': forecast['trend'].iloc[-periods:].tolist()
            }
            
        except Exception as e:
            logger.error(f"   Prophet forecast failed: {str(e)}")
            return {'error': str(e)}
    
    def _forecast_exponential(
        self,
        data: pd.Series,
        periods: int,
        seasonal: bool,
        seasonal_period: Optional[int]
    ) -> Dict[str, Any]:
        """Forecast using Exponential Smoothing"""
        if not self.statsmodels_available:
            return {'error': 'statsmodels not available'}
        
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # Configure model
            if seasonal and seasonal_period:
                model = ExponentialSmoothing(
                    data,
                    seasonal='add',
                    seasonal_periods=seasonal_period
                )
            else:
                model = ExponentialSmoothing(data)
            
            # Fit and forecast
            fitted_model = model.fit()
            forecast = fitted_model.forecast(steps=periods)
            
            return {
                'method': 'exponential_smoothing',
                'seasonal': seasonal,
                'seasonal_period': seasonal_period,
                'forecast': forecast.tolist()
            }
            
        except Exception as e:
            logger.error(f"   Exponential smoothing failed: {str(e)}")
            return {'error': str(e)}
    
    def _detect_seasonality(self, data: pd.Series) -> Optional[int]:
        """
        Auto-detect seasonal period using autocorrelation.
        """
        if not self.statsmodels_available:
            return None
        
        try:
            from statsmodels.tsa.stattools import acf
            
            # Calculate autocorrelation
            autocorr = acf(data.dropna(), nlags=min(len(data)//2, 100))
            
            # Find peaks
            peaks = []
            for i in range(2, len(autocorr) - 1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    if autocorr[i] > 0.3:  # Significant correlation
                        peaks.append(i)
            
            # Return most prominent period
            if peaks:
                return peaks[0]
            
            # Default periods based on data frequency
            if len(data) > 365:
                return 12  # Monthly
            elif len(data) > 52:
                return 7   # Weekly
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Seasonality detection failed: {str(e)}")
            return None
    
    def _select_method(
        self,
        data: pd.Series,
        seasonal: bool,
        seasonal_period: Optional[int]
    ) -> str:
        """Auto-select forecasting method"""
        # Prophet for complex patterns if available
        if self.prophet_available and len(data) > 100:
            return 'prophet'
        
        # SARIMA for seasonal data
        if seasonal and seasonal_period and self.statsmodels_available:
            return 'sarima'
        
        # ARIMA for non-seasonal
        if self.statsmodels_available:
            return 'arima'
        
        # Fallback to exponential smoothing
        return 'exponential'
