# services/ski_touring_service.py
"""
Main ski touring recommendation service that integrates all components
"""

import time
from typing import List, Dict, Optional
from services.weather_service import WeatherService
from services.dynamic_scoring_service import DynamicScoringService, ScoringResult
from services.user_personality_quiz import SkiTouringPersonalityQuiz, UserProfile
from api_clients.senorge_client import SeNorgeClient
from api_clients.varsom_client import VarsomClient
from utils.distance_calculator import calculate_distance, calculate_driving_time, get_max_distance_for_hours, is_within_driving_range
from utils.file_manager import load_json_file
from services.enhanced_snow_depth_service import EnhancedSnowDepthService 

import config

class SkiTouringRecommendationService:
    def __init__(self):
        self.weather_service = WeatherService()
        self.senorge_client = SeNorgeClient()
        self.varsom_client = VarsomClient()
        self.scoring_service = DynamicScoringService()
        self.personality_quiz = SkiTouringPersonalityQuiz()
        self.enhanced_snow_depth_service = EnhancedSnowDepthService()
    
    def get_personalized_recommendations(self, starting_location: dict, max_driving_hours: int, 
                                       user_profile: Optional[UserProfile] = None, 
                                       top_n: int = 8, max_walking_hours: float = 0) -> Dict:
        """
        Get personalized ski touring recommendations
        
        Args:
            starting_location: Starting location with lat/lon and name
            max_driving_hours: Maximum driving hours (1, 3, or 5)
            user_profile: User personality profile (if None, will run quiz)
            top_n: Number of recommendations to return
            
        Returns:
            Dict containing recommendations and metadata
        """
        
        print("🎿 === PERSONALIZED SKI TOURING RECOMMENDATIONS === 🎿")
        print()
        
        # Get or create user profile
        if user_profile is None:
            print("First, let's understand your skiing preferences...")
            print()
            user_profile = self.personality_quiz.conduct_quiz()
            print()
            print(self.personality_quiz.get_profile_summary(user_profile))
            print()
        
        # Load ski touring destinations
        destinations = self._load_ski_destinations()
        if not destinations:
            return {'error': 'No ski destinations found'}
        
        max_distance_km = get_max_distance_for_hours(max_driving_hours)
        
        print(f"🔍 Analyzing {len(destinations)} ski touring destinations...")
        print(f"📍 From: {starting_location['name']}")
        print(f"⏰ Within {max_driving_hours}h drive ({max_distance_km}km)")
        if max_walking_hours > 0:
            print(f"🥾 Willing to walk up to {max_walking_hours}h to reach snow")
        print()
        print(self.scoring_service.get_scoring_explanation(user_profile))
        print()
        
        # Analyze each destination
        scoring_results = []
        destinations_analyzed = []
        
        for destination in destinations:
            try:
                print(f"  🔍 Analyzing {destination['name']}...")
                
                # Calculate distance
                distance_km = calculate_distance(
                    starting_location['lat'], starting_location['lon'],
                    destination['lat'], destination['lon']
                )
                
                # Get all data sources
                weather_data = self.weather_service.get_weather_data(
                    destination['lat'], destination['lon'], destination['name']
                )
                
                snow_data = self.senorge_client.get_snow_data(
                    destination['lat'], destination['lon'], destination['name']
                )
                
                avalanche_data = self.varsom_client.get_avalanche_warning(
                    destination['lat'], destination['lon'], destination['name']
                )
                
                # Calculate personalized score
                scoring_result = self.scoring_service.calculate_personalized_score(
                    destination, weather_data, snow_data, avalanche_data,
                    distance_km, max_distance_km, user_profile, max_walking_hours
                )
                
                scoring_results.append(scoring_result)
                destinations_analyzed.append(destination)
                
                # Be respectful to APIs
                time.sleep(config.API_DELAY)
                
            except Exception as e:
                print(f"    ❌ Error analyzing {destination['name']}: {e}")
                continue
        
            # Check if we found any skiable destinations
        skiable_destinations = [
            (dest, result) for dest, result in zip(destinations_analyzed, scoring_results)
            if not result.snow_depth_analysis or result.snow_depth_analysis.is_skiable
        ]
    
        # If no skiable destinations and user hasn't set walking tolerance, offer walking options
        if not skiable_destinations and max_walking_hours == 0:
            print("🥾 No immediately skiable destinations found.")
            print("   However, some destinations might be accessible with walking...")
            print()
        
            walking_tolerance = self.snow_depth_service.ask_walking_tolerance()
        
            if walking_tolerance > 0:
                print(f"\n🔄 Re-analyzing with {walking_tolerance}h walking tolerance...")
                return self.get_personalized_recommendations(
                    starting_location, max_driving_hours, user_profile, top_n, walking_tolerance
                )
            
        # Rank destinations by personalized scores
        ranked_destinations = self.scoring_service.rank_destinations(
            destinations_analyzed, scoring_results, user_profile
        )
        
        # Prepare results
        within_range_count = sum(1 for _, result in ranked_destinations if result.within_range)
        skiable_count = sum(1 for _, result in ranked_destinations 
                       if not result.snow_depth_analysis or result.snow_depth_analysis.is_skiable)
        
        # Check if any destinations had avalanche data
        avalanche_data_available = any(result.avalanche_data_available for _, result in ranked_destinations)
        
        print(f"✅ Found {within_range_count} destinations within range")
        print(f"🎿 Found {skiable_count} skiable destinations")
        if not avalanche_data_available:
            print("📅 Note: No avalanche warnings currently available (likely out of season)")
        print(f"📊 Showing top {min(top_n, len(ranked_destinations))} recommendations")
        print()
        
        return {
            'user_profile': user_profile.to_dict(),
            'search_info': {
                'starting_location': starting_location,
                'max_driving_hours': max_driving_hours,
                'max_distance_km': max_distance_km,
                'total_analyzed': len(destinations_analyzed),
                'within_range_count': within_range_count,
                'skiable_count': skiable_count,
                'avalanche_data_available': avalanche_data_available
            },
            'recommendations': ranked_destinations[:top_n],
            'scoring_explanation': self.scoring_service.get_scoring_explanation(user_profile, avalanche_data_available)
        }
    
    def _load_ski_destinations(self) -> List[dict]:
        """Load ski touring destinations from JSON file"""
        try:
            return load_json_file("data/ski_destinations.json")
        except Exception as e:
            print(f"❌ Error loading ski destinations: {e}")
            return []
    
    def display_recommendations(self, results: Dict):
        """Display recommendations in a formatted way, with snow depth information"""
        
        recommendations = results.get('recommendations', [])
        search_info = results.get('search_info', {})
        user_profile_dict = results.get('user_profile', {})
        
        print("🌟 === YOUR PERSONALIZED SKI TOURING RECOMMENDATIONS === 🌟")
        print(f"📍 From: {search_info.get('starting_location', {}).get('name', 'Unknown')}")
        print(f"⏱️ Within {search_info.get('max_driving_hours', 0)}h drive")
        print()
        
        max_walking_hours = search_info.get('max_walking_hours', 0)
        if max_walking_hours > 0:
            print(f"🥾 Walking tolerance: {max_walking_hours}h")
        print()

        within_range_count = search_info.get('within_range_count', 0)
        skiable_count = search_info.get('skiable_count', 0)

        print(f"📊 Analysis: {skiable_count} skiable of {search_info.get('total_analyzed', 0)} destinations")
        print()
        
        for i, (destination, scoring_result) in enumerate(recommendations, 1):
        # Determine status
            if not scoring_result.within_range:
                if i == within_range_count + 1 and within_range_count > 0:
                    print("--- Outside driving range (for comparison) ---")
                    print()
                range_icon = "❌"
            elif scoring_result.snow_depth_analysis and not scoring_result.snow_depth_analysis.is_skiable:
                range_icon = "🚫"  # Not skiable
            else:
                range_icon = "✅" # Status icons
            
            #Terrain icons
            terrain_icons = {
                'coastal_alpine': '🌊',
                'high_alpine': '🏔️',
                'forest_valley': '🌲',
                'plateau_ridge': '🌬️',
                'fjord_valley': '🏞️'
            }
            terrain_icon = terrain_icons.get(destination.get('terrain_type', ''), '⛰️')
            
            print(f"{i}. {range_icon} {terrain_icon} {destination['name']}")
            print(f"   Score: {scoring_result.total_score:.0f}/100 • {destination.get('difficulty', 'Unknown').title()} • {destination.get('terrain_type', '').replace('_', ' ').title()}")
            print(f"   {scoring_result.personalized_summary}")

            # Shiw sniw depth analysis if available
            if i <= 3 and scoring_result.snow_depth_analysis:
                analysis = scoring_result.snow_depth_analysis
                if analysis.snow_warnings:
                    print(f"   ⚠️ Snow warnings: {', '.join(analysis.snow_warnings)}")
                print(f"   📝 Snow analysis: {analysis.recommendation_notes}") 

            # Show component breakdown for top 3
            if i <= 3:
                components = scoring_result.component_scores
                if scoring_result.avalanche_data_available:
                    breakdown = f"   📊 Snow: {components['snow']:.0f} • Weather: {components['weather']:.0f} • Safety: {components['avalanche']:.0f} • Views: {components['view_terrain']:.0f}"
                else:
                    breakdown = f"   📊 Snow: {components['snow']:.0f} • Weather: {components['weather']:.0f} • Views: {components['view_terrain']:.0f} • (No avalanche data)"
                print(breakdown)
            
            print()
        
        # Show personalization summary
        personality_summary = self._get_personality_summary(user_profile_dict)
        print(f"🎯 {personality_summary}")
        print()
        
        print("💡 Tips:")
        print("   • Snow depth considered for skiability")
        print("   • Trip duration are estimates - actual conditions may vary")
        print("   • Always check current avalanche conditions at varsom.no")
        print("   • Ask locals about conditions and consider hiring a local guide for unfamiliar terrain")
        print("   • Weather in the mountains can change rapidly - be prepared to adjust plans")
    
    def _get_personality_summary(self, user_profile_dict: dict) -> str:
        """Generate a brief personality summary"""
        powder_priority = user_profile_dict.get('powder_priority', 5)
        view_priority = user_profile_dict.get('view_priority', 5)
        safety_priority = user_profile_dict.get('safety_priority', 5)
        terrain_pref = user_profile_dict.get('terrain_preference', 'balanced')
        
        if powder_priority >= 7:
            main_trait = "Powder Hunter"
        elif view_priority >= 7:
            main_trait = "View Seeker"  
        elif safety_priority >= 8:
            main_trait = "Safety-First Tourer"
        else:
            main_trait = "Balanced Tourer"
        
        terrain_names = {
            'coastal_alpine': 'coastal alpine terrain',
            'high_alpine': 'high alpine challenges',
            'forest_valley': 'peaceful forest skiing',
            'plateau_ridge': 'open plateau exploration',
            'fjord_valley': 'scenic fjord valleys'
        }
        
        terrain_desc = terrain_names.get(terrain_pref, 'varied terrain')
        
        return f"Your profile: {main_trait} who prefers {terrain_desc}"
    
    def update_user_preferences(self, user_profile: UserProfile, 
                              preference_updates: Dict) -> UserProfile:
        """
        Update user preferences without re-running full quiz
        
        Args:
            user_profile: Current user profile
            preference_updates: Dict of preferences to update
            
        Returns:
            Updated UserProfile
        """
        
        for key, value in preference_updates.items():
            if hasattr(user_profile, key):
                setattr(user_profile, key, value)
        
        return user_profile
    
    def get_destination_details(self, destination_name: str) -> Optional[Dict]:
        """Get detailed information about a specific destination"""
        destinations = self._load_ski_destinations()
        
        for dest in destinations:
            if dest['name'].lower() == destination_name.lower():
                return {
                    'destination': dest,
                    'terrain_info': self._get_terrain_details(dest.get('terrain_type', '')),
                    'seasonal_info': self._get_seasonal_details(dest.get('season', '')),
                    'safety_info': self._get_safety_details(dest.get('avalanche_exposure', ''))
                }
        
        return None
    
    def _get_terrain_details(self, terrain_type: str) -> Dict:
        """Get detailed terrain information"""
        terrain_types = self.scoring_service.terrain_types.get('terrain_types', {})
        return terrain_types.get(terrain_type, {})
    
    def _get_seasonal_details(self, season: str) -> Dict:
        """Get seasonal information"""
        terrain_types = self.scoring_service.terrain_types.get('seasonal_windows', {})
        return terrain_types.get(season, {})
    
    def _get_safety_details(self, avalanche_exposure: str) -> Dict:
        """Get safety/avalanche exposure details"""
        terrain_types = self.scoring_service.terrain_types.get('avalanche_exposure', {})
        return terrain_types.get(avalanche_exposure, {})