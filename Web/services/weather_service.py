# services/weather_service.py
"""
Weather data processing and scoring services
"""

from api_clients.yr_weather_client import YrWeatherClient
import config

class WeatherService:
    def __init__(self):
        self.yr_client = YrWeatherClient()
    
    def get_weather_data(self, lat, lon, location_name=""):
        """
        Get and process weather data for a location
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            location_name (str): Name for logging
            
        Returns:
            dict: Processed weather summary, or None if failed
        """
        raw_weather = self.yr_client.get_weather_forecast(lat, lon, location_name)
        if raw_weather:
            return self.yr_client.extract_weather_summary(raw_weather)
        return None
    
    def calculate_weather_score(self, weather_summary):
        """
        Calculate weather score based on Norwegian preferences
        
        Args:
            weather_summary (dict): Weather data summary
            
        Returns:
            int: Weather score (0-100)
        """
        if not weather_summary:
            return 0
        
        score = 0
        
        # Temperature scoring
        temp = weather_summary.get('avg_temp_24h', 0)
        if temp:
            optimal_min, optimal_max = config.OPTIMAL_TEMP_RANGE
            good_min, good_max = config.GOOD_TEMP_RANGE
            acceptable_min, acceptable_max = config.ACCEPTABLE_TEMP_RANGE
            
            if optimal_min <= temp <= optimal_max:
                score += 40  # Perfect temperature
            elif good_min <= temp <= good_max:
                score += 30  # Good temperature
            elif acceptable_min <= temp <= acceptable_max:
                score += 20  # Acceptable
            else:
                score += 10  # Not ideal
        
        # Precipitation scoring (less is better)
        precip = weather_summary.get('total_precipitation_24h', 0)
        precip_hours = weather_summary.get('precipitation_hours', 0)
        
        if precip == 0:
            score += 30  # No rain
        elif precip < 2:
            score += 20  # Light rain
        elif precip < 5:
            score += 10  # Moderate rain
        # Heavy rain gets 0 points
        
        if precip_hours <= 2:
            score += 10  # Rain only for short periods
        
        # Wind scoring (gentle breeze is nice, storms are not)
        wind = weather_summary.get('current_wind_speed', 0)
        if wind:
            if 1 <= wind <= 5:
                score += 15  # Pleasant breeze
            elif wind <= 8:
                score += 10  # Moderate wind
            elif wind <= 12:
                score += 5   # Bit windy
            # Strong wind gets 0 points
        
        # Humidity bonus (not too humid)
        humidity = weather_summary.get('current_humidity', 50)
        if humidity and 40 <= humidity <= 70:
            score += 5  # Comfortable humidity
        
        return min(score, config.WEATHER_SCORE_MAX)  # Cap at max
    
    def create_weather_description(self, weather_summary):
        """
        Create human-readable weather description
        
        Args:
            weather_summary (dict): Weather data summary
            
        Returns:
            str: Human-readable weather description
        """