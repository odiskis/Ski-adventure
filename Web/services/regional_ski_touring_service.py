# services/regional_ski_touring_service.py
"""
Enhanced ski touring service that:
1. Uses weather monitoring grid to identify best regions
2. Finds specific ski tours within those regions  
3. Provides detailed recommendations based on conditions
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

from services.weather_monitoring_service import WeatherMonitoringService, RegionalWeather
from services.user_personality_quiz import UserProfile, SkiTouringPersonalityQuiz
from services.dynamic_scoring_service import DynamicScoringService, ScoringResult
from api_clients.senorge_client import SeNorgeClient
from api_clients.varsom_client import VarsomClient
from utils.distance_calculator import calculate_distance
from utils.file_manager import load_json_file

@dataclass
class SkiTour:
    """Individual ski tour with detailed information"""
    name: str
    lat: float
    lon: float
    region: str
    elevation_range: List[int]
    difficulty: str
    duration_hours: str
    approach: str
    description: str
    features: List[str]
    avalanche_exposure: str
    technical_grade: int
    distance_from_start: Optional[float] = None
    current_conditions: Optional[Dict] = None
    total_score: Optional[float] = None

@dataclass
class RegionalRecommendation:
    """Recommendation for a specific region"""
    region_name: str
    weather_summary: RegionalWeather
    recommended_tours: List[Tuple[SkiTour, ScoringResult]]
    region_score: float
    accessibility_from_start: str
    why_recommended: str

class RegionalSkiTouringService:
    def __init__(self):
        self.weather_monitor = WeatherMonitoringService()
        self.quiz_service = SkiTouringPersonalityQuiz()
        self.scoring_service = DynamicScoringService()
        self.snow_client = SeNorgeClient()
        self.avalanche_client = VarsomClient()
        self.ski_tours_data = {}
        
    def load_ski_tours_database(self):
        """Load the enhanced ski tours database"""
        try:
            self.ski_tours_data = load_json_file("data/enhanced_ski_tours.json")
            total_tours = sum(len(region_data['ski_tours']) 
                            for region_data in self.ski_tours_data.get('regions', {}).values())
            print(f"📊 Loaded {total_tours} ski tours across {len(self.ski_tours_data.get('regions', {}))} regions")
            return True
        except Exception as e:
            print(f"❌ Error loading ski tours database: {e}")
            return False
    
    def get_regional_recommendations(self, starting_location: Dict, max_driving_hours: int,
                                   user_profile: Optional[UserProfile] = None, 
                                   top_regions: int = 3, tours_per_region: int = 3) -> Dict:
        """
        Get ski touring recommendations by:
        1. Analyzing regional weather patterns
        2. Finding best weather regions within driving distance  
        3. Selecting specific tours within those regions
        
        Args:
            starting_location: Dict with 'lat', 'lon', 'name'
            max_driving_hours: Maximum driving time 
            user_profile: User preferences (or will run quiz)
            top_regions: Number of regions to recommend
            tours_per_region: Number of tours per region
            
        Returns:
            Comprehensive regional recommendations
        """
        
        print("🎯 === ENHANCED REGIONAL SKI TOURING ANALYSIS === 🎯")
        print()
        
        # Step 1: Load data
        if not self.ski_tours_data:
            if not self.load_ski_tours_database():
                return {'error': 'Failed to load ski tours database'}
        
        # Step 2: Get user preferences
        if user_profile is None:
            print("🧠 Running personality assessment...")
            user_profile = self.quiz_service.conduct_quiz()
            print()
        
        # Step 3: Analyze regional weather patterns
        print("🌤️ Analyzing weather across Norwegian ski regions...")
        regional_weather = self.weather_monitor.analyze_regional_weather(max_points_per_region=3)
        print()
        
        # Step 4: Filter regions by driving distance
        accessible_regions = self._filter_regions_by_distance(
            starting_location, max_driving_hours, regional_weather
        )
        
        if not accessible_regions:
            return {'error': 'No ski regions found within driving distance'}
        
        print(f"🚗 Found {len(accessible_regions)} regions within {max_driving_hours}h drive")
        print()
        
        # Step 5: Score and rank regions
        print("📊 Scoring regional recommendations...")
        regional_recommendations = self._create_regional_recommendations(
            accessible_regions, starting_location, user_profile, tours_per_region
        )
        
        # Step 6: Sort and select top regions
        sorted_recommendations = sorted(
            regional_recommendations, 
            key=lambda r: r.region_score, 
            reverse=True
        )[:top_regions]
        
        return {
            'user_profile': user_profile.to_dict(),
            'search_info': {
                'starting_location': starting_location,
                'max_driving_hours': max_driving_hours,
                'regions_analyzed': len(accessible_regions),
                'total_tours_considered': sum(len(self.ski_tours_data['regions'][region]['ski_tours']) 
                                            for region in accessible_regions.keys()),
                'methodology': 'weather_grid_analysis'
            },
            'regional_recommendations': sorted_recommendations,
            'weather_grid_summary': self.weather_monitor.get_monitoring_grid_summary()
        }
    
    def _filter_regions_by_distance(self, starting_location: Dict, max_hours: int, 
                                   regional_weather: Dict[str, RegionalWeather]) -> Dict[str, RegionalWeather]:
        """Filter regions that are within driving distance"""
        
        max_distance_km = max_hours * 70  # Assume 70 km/h average
        accessible_regions = {}
        
        for region_name, weather_summary in regional_weather.items():
            if region_name in self.ski_tours_data.get('regions', {}):
                # Use the first ski tour in the region as a reference point
                region_data = self.ski_tours_data['regions'][region_name]
                if region_data['ski_tours']:
                    ref_tour = region_data['ski_tours'][0]
                    distance = calculate_distance(
                        starting_location['lat'], starting_location['lon'],
                        ref_tour['lat'], ref_tour['lon']
                    )
                    
                    if distance <= max_distance_km:
                        accessible_regions[region_name] = weather_summary
                        print(f"   ✅ {region_name}: {distance:.0f}km ({distance/70:.1f}h) - {weather_summary.weather_summary}")
                    else:
                        print(f"   ❌ {region_name}: {distance:.0f}km (too far)")
        
        return accessible_regions
    
    def _create_regional_recommendations(self, accessible_regions: Dict[str, RegionalWeather],
                                       starting_location: Dict, user_profile: UserProfile,
                                       tours_per_region: int) -> List[RegionalRecommendation]:
        """Create detailed recommendations for each accessible region"""
        
        recommendations = []
        
        for region_name, weather_summary in accessible_regions.items():
            print(f"   🔍 Analyzing {region_name}...")
            
            # Get ski tours for this region
            region_data = self.ski_tours_data['regions'][region_name]
            ski_tours = self._load_ski_tours_for_region(region_name, region_data)
            
            # Score each tour in the region
            scored_tours = []
            for tour in ski_tours:
                tour_score = self._score_individual_tour(tour, user_profile, starting_location)
                if tour_score:
                    scored_tours.append((tour, tour_score))
            
            # Select best tours in region
            scored_tours.sort(key=lambda x: x[1].total_score, reverse=True)
            recommended_tours = scored_tours[:tours_per_region]
            
            # Calculate overall region score
            region_score = self._calculate_region_score(weather_summary, recommended_tours, user_profile)
            
            # Generate recommendation
            recommendation = RegionalRecommendation(
                region_name=region_name,
                weather_summary=weather_summary,
                recommended_tours=recommended_tours,
                region_score=region_score,
                accessibility_from_start=self._describe_accessibility(region_name, starting_location),
                why_recommended=self._generate_region_rationale(region_name, weather_summary, user_profile)
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _load_ski_tours_for_region(self, region_name: str, region_data: Dict) -> List[SkiTour]:
        """Convert JSON ski tour data to SkiTour objects"""
        
        tours = []
        for tour_data in region_data.get('ski_tours', []):
            tour = SkiTour(
                name=tour_data['name'],
                lat=tour_data['lat'],
                lon=tour_data['lon'],
                region=region_name,
                elevation_range=tour_data['elevation_range'],
                difficulty=tour_data['difficulty'],
                duration_hours=tour_data['duration_hours'],
                approach=tour_data['approach'],
                description=tour_data['description'],
                features=tour_data['features'],
                avalanche_exposure=tour_data['avalanche_exposure'],
                technical_grade=tour_data['technical_grade']
            )
            tours.append(tour)
        
        return tours
    
    def _score_individual_tour(self, tour: SkiTour, user_profile: UserProfile, 
                             starting_location: Dict) -> Optional[ScoringResult]:
        """Score an individual ski tour based on current conditions"""
        
        try:
            # Calculate distance
            distance = calculate_distance(
                starting_location['lat'], starting_location['lon'],
                tour.lat, tour.lon
            )
            tour.distance_from_start = distance
            
            # Get current conditions (using mock data for now)
            weather_data = self._get_mock_weather_for_tour(tour)
            snow_data = self._get_mock_snow_for_tour(tour)
            avalanche_data = self.avalanche_client.get_avalanche_warning(tour.lat, tour.lon, tour.name)
            
            # Convert tour to destination format for scoring
            destination = {
                'name': tour.name,
                'lat': tour.lat,
                'lon': tour.lon,
                'type': 'ski_touring',
                'terrain_type': self._map_region_to_terrain_type(tour.region),
                'view_score': self._estimate_view_score(tour),
                'technical_level': tour.technical_grade,
                'accessibility': self._estimate_accessibility_score(tour),
                'avalanche_exposure': tour.avalanche_exposure
            }
            
            # Score the tour
            scoring_result = self.scoring_service.calculate_personalized_score(
                destination, weather_data, snow_data, avalanche_data,
                distance, 1000,  # Large max distance since we pre-filtered
                user_profile
            )
            
            return scoring_result
            
        except Exception as e:
            print(f"      ❌ Error scoring {tour.name}: {e}")
            return None
    
    def _get_mock_weather_for_tour(self, tour: SkiTour) -> Dict:
        """Generate realistic mock weather data for a tour"""
        import random
        
        # Seasonal adjustments
        current_month = datetime.now().month
        
        if current_month in [12, 1, 2]:  # Winter
            temp_range = (-10, 5)
            precip_chance = 0.3
        elif current_month in [3, 4]:  # Spring
            temp_range = (-5, 8)
            precip_chance = 0.4
        elif current_month in [5, 6]:  # Late spring
            temp_range = (0, 12)
            precip_chance = 0.5
        else:  # Summer/Fall
            temp_range = (5, 15)
            precip_chance = 0.6
        
        return {
            'avg_temp_24h': random.uniform(*temp_range),
            'total_precipitation_24h': random.uniform(0, 8) if random.random() < precip_chance else 0,
            'current_wind_speed': random.uniform(2, 12),
            'current_humidity': random.uniform(40, 80),
            'cloud_cover_percentage': random.randint(0, 100)
        }
    
    def _get_mock_snow_for_tour(self, tour: SkiTour) -> Dict:
        """Generate realistic mock snow data for a tour"""
        import random
        
        # Base snow depth varies by elevation and region
        base_depth = min(tour.elevation_range) * 0.1  # Rough estimate
        if tour.region in ['Jotunheimen', 'Lyngen']:
            base_depth += 30  # Higher elevation regions
        
        return {
            'snow_depth_cm': max(0, base_depth + random.uniform(-20, 40)),
            'snowfall_3days_cm': random.uniform(0, 25),
            'temperature_trend': random.choice(['cooling', 'stable', 'warming']),
            'wind_effect': random.choice(['minimal', 'moderate', 'significant'])
        }
    
    def _map_region_to_terrain_type(self, region: str) -> str:
        """Map region to terrain type for scoring"""
        terrain_mapping = {
            'Lyngen': 'coastal_alpine',
            'Lofoten': 'coastal_alpine',
            'Jotunheimen': 'high_alpine',
            'Hemsedal': 'forest_valley',
            'Sognefjord': 'fjord_valley',
            'Romsdalen': 'fjord_valley',
            'Sunnmore': 'coastal_alpine',
            'Narvik': 'coastal_alpine',
            'Trollheimen': 'plateau_ridge',
            'Lillehammer': 'forest_valley',
            'Vesteralen': 'coastal_alpine'
        }
        return terrain_mapping.get(region, 'balanced')
    
    def _estimate_view_score(self, tour: SkiTour) -> int:
        """Estimate view score based on tour characteristics"""
        base_score = 70
        
        # Elevation bonus
        max_elevation = max(tour.elevation_range)
        if max_elevation > 2000:
            base_score += 25
        elif max_elevation > 1500:
            base_score += 15
        elif max_elevation > 1000:
            base_score += 10
        
        # Feature bonuses
        if 'epic_views' in tour.features or 'panoramic_views' in tour.features:
            base_score += 20
        if 'fjord_views' in tour.features or 'ocean_views' in tour.features:
            base_score += 15
        if 'iconic_views' in tour.features:
            base_score += 10
        
        return min(base_score, 100)
    
    def _estimate_accessibility_score(self, tour: SkiTour) -> int:
        """Estimate accessibility score based on approach"""
        access_scores = {
            'road_access': 9,
            'lift_access': 10,
            'hut_access': 6,
            'boat_access': 4,
            'boat_or_snowmobile': 3,
            'technical_approach': 2
        }
        return access_scores.get(tour.approach, 5)
    
    def _calculate_region_score(self, weather_summary: RegionalWeather, 
                              recommended_tours: List[Tuple[SkiTour, ScoringResult]],
                              user_profile: UserProfile) -> float:
        """Calculate overall score for a region"""
        
        # Weather component (50% weight)
        weather_score = weather_summary.avg_score * 0.5
        
        # Best tour score component (30% weight)
        if recommended_tours:
            best_tour_score = recommended_tours[0][1].total_score * 0.3
        else:
            best_tour_score = 0
        
        # Tour variety component (20% weight)
        variety_score = min(len(recommended_tours) * 20, 100) * 0.2
        
        return weather_score + best_tour_score + variety_score
    
    def _describe_accessibility(self, region_name: str, starting_location: Dict) -> str:
        """Describe how accessible a region is from the starting location"""
        # This would calculate actual driving routes in production
        distances = {
            'Lillehammer': 'Easy highway access',
            'Hemsedal': 'Good road connections',
            'Jotunheimen': 'Mountain road access',
            'Lyngen': 'Long drive but spectacular',
            'Lofoten': 'Remote but accessible by car',
        }
        return distances.get(region_name, 'Accessible by car')
    
    def _generate_region_rationale(self, region_name: str, weather_summary: RegionalWeather,
                                 user_profile: UserProfile) -> str:
        """Generate explanation for why this region is recommended"""
        
        reasons = []
        
        # Weather-based reasons
        if weather_summary.avg_score >= 80:
            reasons.append("excellent weather conditions")
        elif weather_summary.avg_score >= 65:
            reasons.append("good weather outlook")
        
        # User preference matching
        region_terrain = self._map_region_to_terrain_type(region_name)
        if region_terrain == user_profile.terrain_preference:
            reasons.append("matches your terrain preference")
        
        # Regional characteristics
        regional_features = {
            'Lyngen': 'epic summit-to-sea skiing',
            'Lofoten': 'iconic island scenery',
            'Jotunheimen': 'high alpine challenges',
            'Hemsedal': 'family-friendly terrain',
            'Sognefjord': 'dramatic fjord walls'
        }
        
        if region_name in regional_features:
            reasons.append(regional_features[region_name])
        
        if not reasons:
            reasons.append("good overall conditions")
        
        return f"Recommended for {', '.join(reasons)}"
    
    def display_regional_recommendations(self, results: Dict):
        """Display the regional recommendations in a user-friendly format"""
        
        if 'error' in results:
            print(f"❌ {results['error']}")
            return
        
        print("🎯 === REGIONAL SKI TOURING RECOMMENDATIONS === 🎯")
        print()
        
        search_info = results['search_info']
        print(f"📍 From: {search_info['starting_location']['name']}")
        print(f"🚗 Max drive: {search_info['max_driving_hours']} hours")
        print(f"📊 Analysis: {search_info['regions_analyzed']} regions, {search_info['total_tours_considered']} tours")
        print()
        
        # Display each regional recommendation
        for i, recommendation in enumerate(results['regional_recommendations'], 1):
            self._display_single_regional_recommendation(i, recommendation)
        
        # Display methodology info
        grid_summary = results['weather_grid_summary']
        print("🌐 === ANALYSIS METHODOLOGY === 🌐")
        print(f"Weather monitoring grid: {grid_summary['total_points']} points across {grid_summary['coverage']}")
        print(f"Regional weather analysis + specific tour selection within best regions")
        print()
    
    def _display_single_regional_recommendation(self, rank: int, recommendation: RegionalRecommendation):
        """Display a single regional recommendation"""
        
        print(f"🏔️ === REGION {rank}: {recommendation.region_name.upper()} === 🏔️")
        print(f"Overall Score: {recommendation.region_score:.1f}/100")
        print(f"Weather: {recommendation.weather_summary.weather_summary} (avg {recommendation.weather_summary.avg_score:.1f}/100)")
        print(f"Access: {recommendation.accessibility_from_start}")
        print(f"Why: {recommendation.why_recommended}")
        print()
        
        print("🎿 Recommended Tours:")
        for j, (tour, score_result) in enumerate(recommendation.recommended_tours, 1):
            print(f"   {j}. {tour.name} ({tour.difficulty}) - Score: {score_result.total_score:.1f}/100")
            print(f"      📍 {tour.distance_from_start:.0f}km • ⏱️ {tour.duration_hours} • ⛰️ {tour.elevation_range[0]}-{tour.elevation_range[1]}m")
            print(f"      {tour.description}")
            
            # Show specific conditions summary
            if score_result.avalanche_data_available:
                print(f"      📊 Snow: {score_result.snow_score:.0f} • Weather: {score_result.weather_score:.0f} • Safety: {score_result.avalanche_score:.0f} • Views: {score_result.view_terrain_score:.0f}")
            else:
                print(f"      📊 Snow: {score_result.snow_score:.0f} • Weather: {score_result.weather_score:.0f} • Views: {score_result.view_terrain_score:.0f} • (No avalanche data)")
            print()
        
        print()


def create_enhanced_main_function():
    """Updated main function for the enhanced regional system"""
    
    def main_enhanced():
        """Enhanced main function using regional analysis"""
        print("🎿 === ENHANCED NORWAY SKI TOURING PLANNER === 🎿")
        print("Now with regional weather analysis and specific tour recommendations!")
        print()
        
        # Get user input
        starting_place = input("Enter your starting location in Norway: ").strip()
        if not starting_place:
            print("❌ No starting location provided")
            return
        
        try:
            max_hours = int(input("Maximum driving hours (1, 3, or 5): "))
            if max_hours not in [1, 3, 5]:
                print("⚠️ Using closest valid option...")
                max_hours = min([1, 3, 5], key=lambda x: abs(x - max_hours))
        except ValueError:
            print("⚠️ Invalid input, using 3 hours as default")
            max_hours = 3
        
        print()
        
        # Initialize services
        from services.location_service import LocationService
        location_service = LocationService()
        regional_service = RegionalSkiTouringService()
        
        try:
            # Get starting location coordinates
            start_location = location_service.get_location_coordinates(starting_place)
            if not start_location:
                print("❌ Could not find starting location")
                return
            
            # Run enhanced regional analysis
            results = regional_service.get_regional_recommendations(
                start_location, max_hours, user_profile=None, top_regions=3, tours_per_region=3
            )
            
            if 'error' in results:
                print(f"❌ {results['error']}")
                return
            
            # Display results
            regional_service.display_regional_recommendations(results)
            
            # Ask if user wants to save results
            save_choice = input("💾 Save results to file? (y/n): ").strip().lower()
            if save_choice in ['y', 'yes']:
                from utils.file_manager import save_recommendations
                filename = save_recommendations(results, results['search_info'])
                if filename:
                    print(f"✅ Results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("Please check your internet connection and API configuration.")
    return main_enhanced
    