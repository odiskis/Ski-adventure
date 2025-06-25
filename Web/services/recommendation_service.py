# services/recommendation_service.py
"""
Recommendation service that combines location, weather, and distance data
"""

import time
from services.weather_service import WeatherService
from utils.distance_calculator import calculate_distance, calculate_driving_time, get_max_distance_for_hours, is_within_driving_range
from utils.file_manager import load_destinations
import config

class RecommendationService:
    def __init__(self):
        self.weather_service = WeatherService()
    
    def find_best_destinations(self, starting_location, max_driving_hours, top_n=8):
        """
        Find best weather destinations within driving distance
        
        Args:
            starting_location (dict): Starting location with lat/lon
            max_driving_hours (int): Maximum driving hours
            top_n (int): Number of top recommendations to return
            
        Returns:
            list: List of recommendation dictionaries sorted by score
        """
        destinations = load_destinations()
        if not destinations:
            print("❌ No destinations loaded")
            return []
        
        max_distance_km = get_max_distance_for_hours(max_driving_hours)
        
        print(f"📊 Analyzing {len(destinations)} destinations...")
        
        recommendations = []
        
        for destination in destinations:
            # Calculate distance
            distance_km = calculate_distance(
                starting_location['lat'], starting_location['lon'],
                destination['lat'], destination['lon']
            )
            
            driving_time_hours = calculate_driving_time(distance_km)
            within_range = is_within_driving_range(distance_km, max_driving_hours)
            
            print(f"  🔍 Checking {destination['name']} ({distance_km:.0f}km away)...")
            
            # Get weather data
            weather_summary = self.weather_service.get_weather_data(
                destination['lat'], destination['lon'], destination['name']
            )
            
            if weather_summary:
                # Calculate scores
                weather_score = self.weather_service.calculate_weather_score(weather_summary)
                total_score = self.calculate_total_score(weather_score, distance_km, max_distance_km)
                
                # Create readable summary
                readable_summary = self.create_readable_summary(
                    weather_summary, distance_km, driving_time_hours
                )
                
                recommendation = {
                    'destination': destination['name'],
                    'type': destination['type'],
                    'coordinates': {'lat': destination['lat'], 'lon': destination['lon']},
                    'distance_km': distance_km,
                    'driving_time_hours': driving_time_hours,
                    'weather_score': weather_score,
                    'total_score': total_score,
                    'within_range': within_range,
                    'weather_summary': weather_summary,
                    'readable_summary': readable_summary
                }
                
                recommendations.append(recommendation)
            
            # Be respectful to APIs
            time.sleep(config.API_DELAY)
        
        # Sort by total score (higher is better)
        recommendations.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Filter and organize results
        within_range = [r for r in recommendations if r['within_range']]
        outside_range = [r for r in recommendations if not r['within_range']][:2]  # Top 2 outside range
        
        # Return top N within range plus some outside range for comparison
        final_recommendations = within_range[:top_n] + outside_range
        
        print(f"✅ Found {len(within_range)} destinations within range, {len(outside_range)} outside for comparison")
        
        return final_recommendations
    
    def calculate_total_score(self, weather_score, distance_km, max_distance_km):
        """
        Calculate total score combining weather quality and distance penalty
        
        Args:
            weather_score (int): Weather quality score (0-100)
            distance_km (float): Distance in kilometers
            max_distance_km (int): Maximum allowed distance
            
        Returns:
            float: Total score
        """
        if distance_km > max_distance_km:
            # Heavy penalty for destinations beyond driving limit
            distance_penalty = config.OUT_OF_RANGE_PENALTY  # Large negative score
        else:
            # Gentle penalty for distance within limit (closer is better)
            distance_factor = distance_km / max_distance_km
            distance_penalty = config.DISTANCE_PENALTY_MAX * distance_factor  # Max penalty points
        
        total_score = weather_score - distance_penalty
        
        return max(0, total_score)  # Don't go below 0
    
    def create_readable_summary(self, weather_summary, distance_km, driving_time_hours):
        """
        Create human-readable summary including weather and distance
        
        Args:
            weather_summary (dict): Weather data
            distance_km (float): Distance in kilometers
            driving_time_hours (float): Driving time in hours
            
        Returns:
            str: Human-readable summary
        """
        if not weather_summary:
            return "Weather data unavailable"
        
        temp = weather_summary.get('avg_temp_24h')
        max_temp = weather_summary.get('max_temp_24h')
        min_temp = weather_summary.get('min_temp_24h')
        precip = weather_summary.get('total_precipitation_24h', 0)
        wind = weather_summary.get('current_wind_speed', 0)
        
        summary_parts = []
        
        # Distance
        summary_parts.append(f"🚗 {distance_km:.0f}km ({driving_time_hours:.1f}h drive)")
        
        # Temperature
        if temp:
            summary_parts.append(f"🌡️ {temp:.1f}°C")
            if max_temp and min_temp:
                summary_parts.append(f"({min_temp:.1f}-{max_temp:.1f}°C)")
        
        # Precipitation
        if precip == 0:
            summary_parts.append("☀️ No rain")
        elif precip < 1:
            summary_parts.append("🌦️ Light rain")
        elif precip < 5:
            summary_parts.append(f"🌧️ Rain ({precip:.1f}mm)")
        else:
            summary_parts.append(f"⛈️ Heavy rain ({precip:.1f}mm)")
        
        # Wind
        if wind:
            if wind < 3:
                summary_parts.append("🍃 Light breeze")
            elif wind < 8:
                summary_parts.append("💨 Moderate wind")
            else:
                summary_parts.append(f"🌪️ Windy ({wind:.1f} m/s)")
        
        return " • ".join(summary_parts)