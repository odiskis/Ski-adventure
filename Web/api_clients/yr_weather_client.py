# api_clients/yr_weather_client.py
"""
Yr.no weather API client
"""

import requests
import config

class YrWeatherClient:
    def __init__(self):
        self.api_url = config.YR_WEATHER_API
        self.headers = {
            'User-Agent': config.USER_AGENT
        }
        self.last_modified = {}  # Cache for If-Modified-Since headers
    
    def get_weather_forecast(self, lat, lon, location_name=""):
        """
        Get weather forecast for a specific location using Yr.no API
        
        Args:
            lat (float): Latitude (max 4 decimals as per API requirements)
            lon (float): Longitude (max 4 decimals as per API requirements)
            location_name (str): Name for logging purposes
            
        Returns:
            dict: Weather data from API, or None if failed
        """
        # Round coordinates to 4 decimals as required by API
        lat = round(float(lat), 4)
        lon = round(float(lon), 4)
        
        try:
            params = {
                'lat': lat,
                'lon': lon
            }
            
            # Add If-Modified-Since header if we have cached data
            cache_key = f"{lat},{lon}"
            headers = self.headers.copy()
            if cache_key in self.last_modified:
                headers['If-Modified-Since'] = self.last_modified[cache_key]
            
            if location_name:
                print(f"🌤️  Fetching weather for {location_name} ({lat}, {lon})...")
            
            response = requests.get(self.api_url, headers=headers, params=params)
            
            if response.status_code == 304:
                if location_name:
                    print(f"   Data not modified for {location_name}")
                return None  # Data hasn't changed
            
            response.raise_for_status()
            
            # Store Last-Modified header for future requests
            if 'Last-Modified' in response.headers:
                self.last_modified[cache_key] = response.headers['Last-Modified']
            
            # Check if this is beta/deprecated (status 203)
            if response.status_code == 203:
                print(f"⚠️  Warning: API returned 203 for {location_name} - product may be beta/deprecated")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"🚫 Error fetching weather data for {location_name}: {e}")
            return None
    
    def extract_weather_summary(self, weather_data):
        """
        Extract useful weather information from Yr.no API response
        
        Args:
            weather_data (dict): Raw weather data from API
            
        Returns:
            dict: Processed weather summary, or None if failed
        """
        try:
            timeseries = weather_data['properties']['timeseries']
            
            # Get current weather (first time point)
            current = timeseries[0]['data']['instant']['details']
            
            # Get next 24 hours for daily summary
            next_24h = timeseries[:24] if len(timeseries) >= 24 else timeseries
            
            # Calculate averages for next 24 hours
            temps = [t['data']['instant']['details']['air_temperature'] for t in next_24h]
            precip = []
            
            for t in next_24h:
                if 'next_1_hours' in t['data']:
                    precip_amount = t['data']['next_1_hours']['details'].get('precipitation_amount', 0)
                    precip.append(precip_amount)
            
            summary = {
                'current_temp': current.get('air_temperature'),
                'current_humidity': current.get('relative_humidity'),
                'current_wind_speed': current.get('wind_speed'),
                'avg_temp_24h': sum(temps) / len(temps) if temps else None,
                'max_temp_24h': max(temps) if temps else None,
                'min_temp_24h': min(temps) if temps else None,
                'total_precipitation_24h': sum(precip) if precip else 0,
                'precipitation_hours': len([p for p in precip if p > 0]) if precip else 0
            }
            
            return summary
            
        except (KeyError, IndexError, TypeError) as e:
            print(f"🚫 Error extracting weather summary: {e}")
            return None