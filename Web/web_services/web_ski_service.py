# web_services/web_ski_service.py
"""
Web service adapter that bridges existing ski touring services with Flask web interface
"""

import sys
import os
from typing import Dict, List, Optional

# Add parent directory to path for service imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from services.regional_ski_touring_service import RegionalSkiTouringService
from services.ski_touring_service import SkiTouringRecommendationService
from services.user_personality_quiz import UserProfile
from services.location_service import LocationService

class WebSkiService:
    """
    Web-adapted ski touring service that provides clean data for templates
    """
    
    def __init__(self):
        self.regional_service = RegionalSkiTouringService()
        self.original_service = SkiTouringRecommendationService()
        self.location_service = LocationService()
    
    def get_web_recommendations(self, start_location: Dict, max_hours: int, 
                               user_profile: UserProfile, 
                               use_regional: bool = True) -> Dict:
        """
        Get ski touring recommendations formatted for web display
        
        Args:
            start_location: Starting location dictionary
            max_hours: Maximum driving hours
            user_profile: User personality profile
            use_regional: Whether to use regional analysis (default) or original service
            
        Returns:
            Dict formatted for web templates
        """
        
        try:
            if use_regional:
                # Use enhanced regional system
                raw_results = self.regional_service.get_regional_recommendations(
                    start_location, max_hours, user_profile, 
                    top_regions=3, tours_per_region=3
                )
            else:
                # Use original point-based system
                raw_results = self.original_service.get_personalized_recommendations(
                    start_location, max_hours, user_profile, top_n=8
                )
            
            if 'error' in raw_results:
                return raw_results
            
            # Format for web display
            web_formatted = self._format_for_web(raw_results, use_regional)
            
            return web_formatted
            
        except Exception as e:
            return {'error': f'Error generating recommendations: {str(e)}'}
    
    def _format_for_web(self, raw_results: Dict, is_regional: bool) -> Dict:
        """
        Format raw results for web template consumption
        """
        
        if is_regional:
            return self._format_regional_results(raw_results)
        else:
            return self._format_original_results(raw_results)
    
    def _format_regional_results(self, raw_results: Dict) -> Dict:
        """
        Format regional analysis results for web templates
        """
        
        formatted_regions = []
        
        for regional_rec in raw_results.get('regional_recommendations', []):
            # Format individual tours within region
            formatted_tours = []
            for tour, score_result in regional_rec.recommended_tours:
                tour_data = {
                    'name': tour.name,
                    'description': tour.description,
                    'difficulty': tour.difficulty.title(),
                    'duration': tour.duration_hours,
                    'elevation_range': f"{tour.elevation_range[0]}-{tour.elevation_range[1]}m",
                    'approach': tour.approach.replace('_', ' ').title(),
                    'features': tour.features,
                    'technical_grade': tour.technical_grade,
                    'distance_km': getattr(tour, 'distance_from_start', 0),
                    'scores': {
                        'total': round(score_result.total_score, 1),
                        'snow': round(score_result.snow_score, 0),
                        'weather': round(score_result.weather_score, 0),
                        'avalanche': round(score_result.avalanche_score, 0) if score_result.avalanche_score else None,
                        'views': round(score_result.view_terrain_score, 0),
                        'avalanche_available': score_result.avalanche_data_available
                    },
                    'summary': score_result.personalized_summary,
                    'within_range': score_result.within_range
                }
                formatted_tours.append(tour_data)
            
            # Format region summary
            region_data = {
                'name': regional_rec.region_name,
                'score': round(regional_rec.region_score, 1),
                'weather_summary': regional_rec.weather_summary.weather_summary,
                'weather_score': round(regional_rec.weather_summary.avg_score, 1),
                'accessibility': regional_rec.accessibility_from_start,
                'why_recommended': regional_rec.why_recommended,
                'tours': formatted_tours,
                'tour_count': len(formatted_tours)
            }
            formatted_regions.append(region_data)
        
        return {
            'type': 'regional',
            'user_profile': raw_results.get('user_profile', {}),
            'search_info': raw_results.get('search_info', {}),
            'regions': formatted_regions,
            'methodology': 'Enhanced Regional Weather Analysis',
            'total_regions': len(formatted_regions),
            'weather_grid_summary': raw_results.get('weather_grid_summary', {})
        }
    
    def _format_original_results(self, raw_results: Dict) -> Dict:
        """
        Format original point-based results for web templates
        """
        
        formatted_recommendations = []
        
        for destination, score_result in raw_results.get('recommendations', []):
            rec_data = {
                'name': destination['name'],
                'type': destination.get('type', 'ski_touring'),
                'terrain_type': destination.get('terrain_type', 'unknown').replace('_', ' ').title(),
                'difficulty': destination.get('difficulty', 'Unknown').title(),
                'elevation_range': f"{destination.get('elevation_range', [0, 1000])[0]}-{destination.get('elevation_range', [0, 1000])[1]}m",
                'season': destination.get('season', 'Unknown'),
                'description': destination.get('description', ''),
                'features': destination.get('features', []),
                'access': destination.get('access', 'unknown').replace('_', ' ').title(),
                'scores': {
                    'total': round(score_result.total_score, 1),
                    'snow': round(score_result.snow_score, 0),
                    'weather': round(score_result.weather_score, 0),
                    'avalanche': round(score_result.avalanche_score, 0) if score_result.avalanche_score else None,
                    'views': round(score_result.view_terrain_score, 0),
                    'distance': round(score_result.distance_score, 0),
                    'avalanche_available': score_result.avalanche_data_available
                },
                'summary': score_result.personalized_summary,
                'within_range': score_result.within_range,
                'technical_level': destination.get('technical_level', 5),
                'view_score': destination.get('view_score', 70),
                'avalanche_exposure': destination.get('avalanche_exposure', 'moderate').title()
            }
            formatted_recommendations.append(rec_data)
        
        # Split into within range and out of range
        within_range = [r for r in formatted_recommendations if r['within_range']]
        out_of_range = [r for r in formatted_recommendations if not r['within_range']]
        
        return {
            'type': 'original',
            'user_profile': raw_results.get('user_profile', {}),
            'search_info': raw_results.get('search_info', {}),
            'within_range': within_range,
            'out_of_range': out_of_range,
            'methodology': 'Point-based Weather Analysis',
            'total_analyzed': raw_results.get('search_info', {}).get('total_analyzed', 0),
            'scoring_explanation': raw_results.get('scoring_explanation', '')
        }
    
    def get_location_suggestions(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Get location suggestions for autocomplete
        """
        try:
            locations = self.location_service.search_multiple_locations(query, max_results)
            
            formatted_suggestions = []
            for location in locations:
                suggestion = {
                    'name': location['name'],
                    'display_name': f"{location['name']}, {location.get('municipality', '')} ({location.get('county', '')})",
                    'municipality': location.get('municipality', ''),
                    'county': location.get('county', ''),
                    'lat': location['lat'],
                    'lon': location['lon']
                }
                formatted_suggestions.append(suggestion)
            
            return formatted_suggestions
            
        except Exception as e:
            return []
    
    def validate_location_input(self, location_input: str) -> Dict:
        """
        Validate and process location input
        """
        try:
            location_result = self.location_service.get_location_coordinates(location_input)
            
            if location_result:
                return {
                    'valid': True,
                    'location': location_result,
                    'display_name': f"{location_result['name']}, {location_result.get('municipality', '')} ({location_result.get('county', '')})"
                }
            else:
                return {
                    'valid': False,
                    'error': 'Location not found. Please try a different location name.'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error processing location: {str(e)}'
            }
    
    def get_profile_display_data(self, user_profile: UserProfile) -> Dict:
        """
        Get user profile data formatted for display
        """
        
        # Determine primary personality traits
        traits = []
        if user_profile.powder_priority >= 7:
            traits.append("Powder Hunter")
        if user_profile.view_priority >= 7:
            traits.append("View Seeker")
        if user_profile.safety_priority >= 8:
            traits.append("Safety-First")
        if user_profile.adventure_seeking >= 8:
            traits.append("Adventure Seeker")
        
        if not traits:
            traits.append("Balanced Tourer")
        
        # Terrain preference display
        terrain_names = {
            'coastal_alpine': 'Coastal Alpine (Summit-to-Sea)',
            'high_alpine': 'High Alpine (Glaciated Peaks)',
            'forest_valley': 'Forest Valley (Gentle Touring)',
            'plateau_ridge': 'Plateau Ridge (Wide Open)',
            'fjord_valley': 'Fjord Valley (Scenic Corridors)'
        }
        
        return {
            'personality_type': ' & '.join(traits),
            'terrain_preference': terrain_names.get(user_profile.terrain_preference, 'Balanced'),
            'risk_tolerance': user_profile.risk_tolerance.title(),
            'experience_level': user_profile.experience_level.title(),
            'priorities': {
                'powder': user_profile.powder_priority,
                'views': user_profile.view_priority,
                'safety': user_profile.safety_priority,
                'adventure': user_profile.adventure_seeking,
                'social': user_profile.social_preference
            },
            'priority_labels': {
                'powder': 'Fresh Snow Priority',
                'views': 'Scenic Views Priority', 
                'safety': 'Safety Priority',
                'adventure': 'Adventure Seeking',
                'social': 'Social Preference'
            }
        }