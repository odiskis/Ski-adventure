# api_clients/senorge_client.py
"""
SeNorge API client for Norwegian snow depth and conditions data
Uses the THREDDS Data Server from MET Norway
"""

import requests
import json
from datetime import datetime, timedelta
import config

class SeNorgeClient:
    def __init__(self):
        self.thredds_base_url = "https://thredds.met.no/thredds"
        self.catalog_url = f"{self.thredds_base_url}/catalog/senorge/catalog.html"
        self.opendap_base = f"{self.thredds_base_url}/dodsC/senorge"
        
    def get_snow_data(self, lat, lon, location_name=""):
        """
        Get snow depth data for a specific location from SeNorge
        
        Args:
            lat (float): Latitude
            lon (float): Longitude  
            location_name (str): Name for logging purposes
            
        Returns:
            dict: Snow data summary, or None if failed
        """
        try:
            if location_name:
                print(f"❄️  Fetching snow data for {location_name} ({lat:.4f}, {lon:.4f})...")
            
            # Get current date and recent dates for snowfall analysis
            today = datetime.now()
            recent_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(4)]
            
            snow_data = {
                'location': location_name,
                'coordinates': {'lat': lat, 'lon': lon},
                'snow_depth_cm': None,
                'snowfall_3days_cm': 0,
                'data_timestamp': today.isoformat(),
                'data_quality': 'estimated'  # Since we're using mock data for now
            }
            
            # For prototype: Generate realistic snow data based on location
            # In production, this would query the actual THREDDS server
            snow_data.update(self._generate_mock_snow_data(lat, lon, today))
            
            return snow_data
            
        except Exception as e:
            print(f"🚫 Error fetching snow data for {location_name}: {e}")
            return None
    
    def _generate_mock_snow_data(self, lat, lon, date):
        """
        Generate realistic mock snow data for prototype
        In production, replace with actual THREDDS/OPeNDAP queries
        """
        import random
        
        # Base snow depth varies by elevation and latitude
        # Higher latitude and elevation = more snow
        base_depth = max(0, (lat - 58) * 15 + random.randint(-20, 50))
        
        # Coastal areas (western longitudes) get more precipitation
        if lon < 8:  # Western coastal areas
            base_depth += random.randint(10, 40)
        
        # Seasonal adjustment (more snow in winter months)
        month = date.month
        if month in [12, 1, 2, 3]:  # Winter peak
            seasonal_factor = 1.5
        elif month in [11, 4]:  # Shoulder season  
            seasonal_factor = 1.0
        elif month in [5, 10]:  # Late/early season
            seasonal_factor = 0.5
        else:  # Summer
            seasonal_factor = 0.1
            
        snow_depth = int(base_depth * seasonal_factor)
        
        # Recent snowfall (0-3 days)
        recent_snowfall = random.randint(0, 25) if snow_depth > 20 else 0
        
        return {
            'snow_depth_cm': max(0, snow_depth),
            'snowfall_3days_cm': recent_snowfall,
            'temperature_trend': random.choice(['stable', 'warming', 'cooling']),
            'wind_effect': random.choice(['minimal', 'moderate', 'significant'])
        }
    
    def _query_thredds_server(self, lat, lon, date):
        """
        Query actual THREDDS server for snow data
        This is the real implementation for production use
        """
        try:
            # Construct OPeNDAP URL for snow depth data
            dataset_url = f"{self.opendap_base}/seNorge_2018/Archive/seNorge2018_{date.strftime('%Y')}.nc"
            
            # Parameters for spatial subset
            params = {
                'var': 'snow_depth',
                'north': lat + 0.01,
                'south': lat - 0.01, 
                'east': lon + 0.01,
                'west': lon - 0.01,
                'time': date.strftime('%Y-%m-%d')
            }
            
            # This would be the actual implementation
            # response = requests.get(dataset_url, params=params)
            # return self._parse_netcdf_response(response)
            
            print("   📊 THREDDS query constructed (using mock data for prototype)")
            return None
            
        except Exception as e:
            print(f"   🚫 THREDDS query failed: {e}")
            return None
    
    def get_snow_forecast(self, lat, lon, days_ahead=3):
        """
        Get snow forecast for the coming days
        """
        forecasts = []
        
        for day in range(1, days_ahead + 1):
            future_date = datetime.now() + timedelta(days=day)
            forecast = self._generate_mock_snow_data(lat, lon, future_date)
            forecast['forecast_date'] = future_date.strftime('%Y-%m-%d')
            forecast['forecast_day'] = day
            forecasts.append(forecast)
            
        return forecasts
    
    def calculate_snow_quality_score(self, snow_data):
        """
        Calculate snow quality score based on ski touring preferences
        
        Args:
            snow_data (dict): Snow data from get_snow_data()
            
        Returns:
            int: Snow quality score (0-100)
        """
        if not snow_data:
            return 0
            
        score = 0
        
        # Snow Depth (40 points max) - More is always better!
        snow_depth = snow_data.get('snow_depth_cm', 0)
        if snow_depth >= 50:
            score += 40  # Excellent base - no rocks!
        elif snow_depth >= 30:
            score += 25  # Marginal - some rocks possible
        elif snow_depth >= 20:
            score += 10  # Poor - very rocky
        # else: 0 points - too dangerous
        
        # Recent Snowfall (30 points max) - Fresh powder bonus
        recent_snow = snow_data.get('snowfall_3days_cm', 0)
        if recent_snow >= 30:
            score += 30  # Epic powder day!
        elif recent_snow >= 15:
            score += 20  # Good fresh snow
        elif recent_snow >= 5:
            score += 10  # Some fresh snow
        # else: 0 points for old snow
        
        # Temperature Stability (20 points max)
        temp_trend = snow_data.get('temperature_trend', 'stable')
        if temp_trend == 'stable':
            score += 20  # Stable conditions
        elif temp_trend == 'cooling':
            score += 15  # Getting more stable
        elif temp_trend == 'warming':
            score += 5   # Less stable, potential for wet avalanches
        
        # Wind Impact (10 points max)
        wind_effect = snow_data.get('wind_effect', 'minimal')
        if wind_effect == 'minimal':
            score += 10  # No wind loading issues
        elif wind_effect == 'moderate':
            score += 5   # Some wind redistribution
        # significant wind gets 0 points - dangerous wind slabs
        
        return min(score, 100)  # Cap at 100