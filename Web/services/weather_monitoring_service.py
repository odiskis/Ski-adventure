# services/weather_monitoring_service.py
"""
Weather monitoring service that uses a grid of DNT cabins and strategic points
to assess regional weather patterns for ski touring
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from services.weather_service import WeatherService
from utils.file_manager import load_json_file
import config

@dataclass
class WeatherPoint:
    """A single weather monitoring point"""
    name: str
    lat: float
    lon: float
    elevation: int
    type: str  # 'dnt_cabin', 'peak', 'strategic_point'
    region: str
    weather_data: Optional[Dict] = None
    weather_score: Optional[float] = None

@dataclass
class RegionalWeather:
    """Weather summary for a region"""
    region_name: str
    avg_score: float
    point_count: int
    best_points: List[WeatherPoint]
    weather_summary: str
    conditions: Dict

class WeatherMonitoringService:
    def __init__(self):
        self.weather_service = WeatherService()
        self.monitoring_points = []
        self.regional_summaries = {}
        
    def load_monitoring_grid(self):
        """Load weather monitoring points from multiple sources"""
        print("🌐 Loading weather monitoring grid...")
        
        # Load DNT cabins
        dnt_cabins = self._load_dnt_cabins()
        print(f"   📍 Loaded {len(dnt_cabins)} DNT cabins")
        
        # Load strategic weather points
        strategic_points = self._load_strategic_points()
        print(f"   📍 Loaded {len(strategic_points)} strategic points")
        
        # Combine all monitoring points
        self.monitoring_points = dnt_cabins + strategic_points
        print(f"   ✅ Total monitoring grid: {len(self.monitoring_points)} points")
        
        return len(self.monitoring_points)
    
    def _load_dnt_cabins(self) -> List[WeatherPoint]:
        """Load DNT cabin locations from UT.no API or local cache"""
        try:
            # For now, use a representative sample of key DNT cabins
            # In production, you'd query the UT.no API
            key_cabins = [
                # Lyngen Alps region
                {"name": "Lyngstuva", "lat": 69.583, "lon": 20.133, "elevation": 400, "region": "Lyngen"},
                {"name": "Taskekjøten", "lat": 69.650, "lon": 20.200, "elevation": 800, "region": "Lyngen"},
                
                # Lofoten region  
                {"name": "Munkebu", "lat": 68.100, "lon": 13.083, "elevation": 200, "region": "Lofoten"},
                {"name": "Reine", "lat": 67.934, "lon": 13.088, "elevation": 50, "region": "Lofoten"},
                
                # Jotunheimen region
                {"name": "Spiterstulen", "lat": 61.617, "lon": 8.383, "elevation": 1100, "region": "Jotunheimen"},
                {"name": "Glitterheim", "lat": 61.683, "lon": 8.333, "elevation": 1350, "region": "Jotunheimen"},
                {"name": "Gjendesheim", "lat": 61.500, "lon": 8.650, "elevation": 990, "region": "Jotunheimen"},
                {"name": "Leirvassbu", "lat": 61.550, "lon": 8.183, "elevation": 1400, "region": "Jotunheimen"},
                
                # Hemsedal/Hallingdal region
                {"name": "Grøndalen", "lat": 60.867, "lon": 8.550, "elevation": 650, "region": "Hemsedal"},
                {"name": "Ustaoset", "lat": 60.517, "lon": 7.533, "elevation": 990, "region": "Hemsedal"},
                
                # Sognefjord region
                {"name": "Årdal", "lat": 61.250, "lon": 7.683, "elevation": 50, "region": "Sognefjord"},
                {"name": "Turtagrø", "lat": 61.500, "lon": 7.750, "elevation": 884, "region": "Sognefjord"},
                
                # Romsdalen region
                {"name": "Åndalsnes", "lat": 62.567, "lon": 7.683, "elevation": 50, "region": "Romsdalen"},
                {"name": "Trollstigen", "lat": 62.450, "lon": 7.650, "elevation": 700, "region": "Romsdalen"},
                
                # Sunnmøre Alps
                {"name": "Stranda", "lat": 62.317, "lon": 6.933, "elevation": 50, "region": "Sunnmore"},
                {"name": "Hjørundfjord", "lat": 62.183, "lon": 7.000, "elevation": 100, "region": "Sunnmore"},
                
                # Narvik region
                {"name": "Narvikfjellet", "lat": 68.438, "lon": 17.427, "elevation": 200, "region": "Narvik"},
                {"name": "Abisko", "lat": 68.350, "lon": 18.783, "elevation": 400, "region": "Narvik"},
                
                # Oppdal/Trollheimen
                {"name": "Oppdal", "lat": 62.583, "lon": 9.683, "elevation": 600, "region": "Trollheimen"},
                {"name": "Gjevilvasshytta", "lat": 62.600, "lon": 9.400, "elevation": 900, "region": "Trollheimen"},
                
                # Lillehammer region
                {"name": "Lillehammer", "lat": 61.115, "lon": 10.466, "elevation": 200, "region": "Lillehammer"},
                {"name": "Sjusjøen", "lat": 61.233, "lon": 10.550, "elevation": 800, "region": "Lillehammer"},
                
                # Vesterålen
                {"name": "Andøya", "lat": 69.117, "lon": 16.133, "elevation": 50, "region": "Vesteralen"},
                {"name": "Sortland", "lat": 68.700, "lon": 15.417, "elevation": 100, "region": "Vesteralen"}
            ]
            
            weather_points = []
            for cabin in key_cabins:
                point = WeatherPoint(
                    name=cabin["name"],
                    lat=cabin["lat"],
                    lon=cabin["lon"],
                    elevation=cabin["elevation"],
                    type="dnt_cabin",
                    region=cabin["region"]
                )
                weather_points.append(point)
                
            return weather_points
            
        except Exception as e:
            print(f"❌ Error loading DNT cabins: {e}")
            return []
    
    def _load_strategic_points(self) -> List[WeatherPoint]:
        """Load strategic weather monitoring points (peaks, passes, etc.)"""
        strategic_points = [
            # Major peaks for altitude weather
            {"name": "Galdhøpiggen", "lat": 61.636, "lon": 8.313, "elevation": 2469, "region": "Jotunheimen"},
            {"name": "Glittertind", "lat": 61.683, "lon": 8.347, "elevation": 2452, "region": "Jotunheimen"},
            
            # Weather transition zones
            {"name": "Dovre Pass", "lat": 62.283, "lon": 9.333, "elevation": 1000, "region": "Dovre"},
            {"name": "Saltfjellet", "lat": 66.900, "lon": 15.150, "elevation": 1200, "region": "Saltfjellet"},
            
            # Coastal weather reference points
            {"name": "Ålesund Coast", "lat": 62.472, "lon": 6.155, "elevation": 0, "region": "Coast"},
            {"name": "Bodø Coast", "lat": 67.280, "lon": 14.404, "elevation": 0, "region": "Coast"},
            {"name": "Tromsø Coast", "lat": 69.649, "lon": 18.955, "elevation": 0, "region": "Coast"}
        ]
        
        weather_points = []
        for point in strategic_points:
            wp = WeatherPoint(
                name=point["name"],
                lat=point["lat"],
                lon=point["lon"],
                elevation=point["elevation"],
                type="strategic_point",
                region=point["region"]
            )
            weather_points.append(wp)
            
        return weather_points
    
    def analyze_regional_weather(self, max_points_per_region: int = 5) -> Dict[str, RegionalWeather]:
        """
        Analyze weather across all regions and return regional summaries
        
        Args:
            max_points_per_region: Maximum weather points to check per region
            
        Returns:
            Dict mapping region names to RegionalWeather objects
        """
        print("🌤️ Analyzing regional weather patterns...")
        
        if not self.monitoring_points:
            self.load_monitoring_grid()
        
        # Group points by region
        regions = {}
        for point in self.monitoring_points:
            if point.region not in regions:
                regions[point.region] = []
            regions[point.region].append(point)
        
        regional_weather = {}
        
        for region_name, points in regions.items():
            print(f"   🔍 Analyzing {region_name} ({len(points)} points)")
            
            # Limit points per region to avoid API overload
            selected_points = points[:max_points_per_region]
            
            # Get weather data for each point
            for point in selected_points:
                try:
                    weather_data = self.weather_service.get_weather_data(
                        point.lat, point.lon, point.name
                    )
                    point.weather_data = weather_data
                    point.weather_score = self._calculate_point_weather_score(weather_data)
                    
                    # API rate limiting
                    time.sleep(config.API_DELAY)
                    
                except Exception as e:
                    print(f"      ❌ Failed to get weather for {point.name}: {e}")
                    point.weather_score = 0
            
            # Calculate regional summary
            regional_summary = self._create_regional_summary(region_name, selected_points)
            regional_weather[region_name] = regional_summary
        
        self.regional_summaries = regional_weather
        return regional_weather
    
    def _calculate_point_weather_score(self, weather_data: Dict) -> float:
        """Calculate weather score for a single point"""
        if not weather_data:
            return 0
        
        score = 0
        
        # Temperature (40 points max)
        temp = weather_data.get('avg_temp_24h', 0) #returns 0 if data not available
        if -10 <= temp <= 1:
            score += 40  # Perfect ski touring temps
        elif -15 <= temp <= 6:
            score += 30  # Good temps
        elif -20 <= temp <= 10:
            score += 20  # Acceptable
        else:
            score += 10  # Challenging
        
        # Precipitation (30 points max)
        precip = weather_data.get('total_precipitation_24h', 0)
        if precip == 0:
            score += 30  # Clear
        elif precip < 2:
            score += 20  # Light
        elif precip < 5:
            score += 10  # Moderate
        # Heavy precip gets 0 points
        
        # Wind (20 points max)
        wind = weather_data.get('current_wind_speed', 0)
        if wind < 5:
            score += 20  # Calm
        elif wind < 10:
            score += 10  # Light
        elif wind < 15:
           score += 5  # Strong
        # Very strong wind gets 0 points
        
        # Visibility/Cloud cover (10 points max)
        cloud_cover = weather_data.get('cloud_cover_percentage', 50) #returns 50% if data not available
        if cloud_cover < 25:
            score += 10  # Clear
        elif cloud_cover < 50:
            score += 7   # Partly cloudy
        elif cloud_cover < 75:
            score += 4   # Mostly cloudy
        # Overcast gets 0 points
        
        return min(score, 100)
    
    def _create_regional_summary(self, region_name: str, points: List[WeatherPoint]) -> RegionalWeather:
        """Create a summary of weather conditions for a region"""
        
        # Calculate average score
        valid_scores = [p.weather_score for p in points if p.weather_score is not None]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        # Find best points in region
        sorted_points = sorted(points, key=lambda p: p.weather_score or 0, reverse=True)
        best_points = sorted_points[:3]  # Top 3 points
        
        # Generate weather summary
        if avg_score >= 80:
            weather_summary = "Excellent conditions"
        elif avg_score >= 65:
            weather_summary = "Good conditions"
        elif avg_score >= 50:
            weather_summary = "Fair conditions"
        elif avg_score >= 35:
            weather_summary = "Marginal conditions"
        else:
            weather_summary = "Poor conditions"
        
        # Aggregate conditions from best point
        best_point = best_points[0] if best_points else None
        conditions = best_point.weather_data if best_point and best_point.weather_data else {}
        
        return RegionalWeather(
            region_name=region_name,
            avg_score=avg_score,
            point_count=len(points),
            best_points=best_points,
            weather_summary=weather_summary,
            conditions=conditions
        )
    
    def get_best_weather_regions(self, top_n: int = 5) -> List[RegionalWeather]:
        """Get the regions with the best weather conditions"""
        if not self.regional_summaries:
            self.analyze_regional_weather()
        
        # Sort regions by average weather score
        sorted_regions = sorted(
            self.regional_summaries.values(),
            key=lambda r: r.avg_score,
            reverse=True
        )
        
        return sorted_regions[:top_n]
    
    def find_weather_points_near_location(self, lat: float, lon: float, 
                                        radius_km: float = 50) -> List[WeatherPoint]:
        """Find weather monitoring points near a specific location"""
        from utils.distance_calculator import calculate_distance
        
        nearby_points = []
        for point in self.monitoring_points:
            distance = calculate_distance(lat, lon, point.lat, point.lon)
            if distance <= radius_km:
                nearby_points.append((point, distance))
        
        # Sort by distance
        nearby_points.sort(key=lambda x: x[1])
        return [point for point, distance in nearby_points]
    
    def get_monitoring_grid_summary(self) -> Dict:
        """Get summary statistics about the monitoring grid"""
        if not self.monitoring_points:
            self.load_monitoring_grid()
        
        regions = {}
        types = {}
        
        for point in self.monitoring_points:
            # Count by region
            regions[point.region] = regions.get(point.region, 0) + 1
            
            # Count by type
            types[point.type] = types.get(point.type, 0) + 1
        
        return {
            'total_points': len(self.monitoring_points),
            'regions': regions,
            'types': types,
            'coverage': f"{len(regions)} regions covered"
        }