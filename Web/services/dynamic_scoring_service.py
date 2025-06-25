# services/dynamic_scoring_service.py
"""
Dynamic scoring system that adapts to user preferences and handles missing data
Enhanced to work with enhanced_snow_depth_service and latest updates
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from services.user_personality_quiz import UserProfile
from services.enhanced_snow_depth_service import EnhancedSnowDepthService, SnowDepthAnalysis
from utils.file_manager import load_json_file

@dataclass
class ScoringResult:
    """Result of scoring calculation for a destination"""
    destination_name: str
    total_score: float
    component_scores: Dict[str, float]
    weather_score: float
    snow_score: float
    avalanche_score: Optional[float]  # Can be None if no avalanche data
    view_terrain_score: float
    distance_score: float
    within_range: bool
    personalized_summary: str
    avalanche_data_available: bool  # Track if avalanche data was available
    snow_depth_analysis: Optional[SnowDepthAnalysis] = None  # NEW: Enhanced snow analysis

class DynamicScoringService:
    def __init__(self):
        self.terrain_types = self._load_terrain_types()
        self.snow_depth_service = EnhancedSnowDepthService()  # NEW: Enhanced snow service
        self.base_weights = {
            'snow': 0.35,
            'weather': 0.25,
            'avalanche': 0.25,
            'view_terrain': 0.10,
            'distance': 0.05
        }
    
    def _load_terrain_types(self):
        """Load terrain types configuration"""
        try:
            return load_json_file("data/terrain_types.json")
        except:
            # Fallback terrain types if file not found
            return {
                "terrain_types": {
                    "coastal_alpine": {"view_score_multiplier": 1.2, "difficulty_modifier": 0.8},
                    "high_alpine": {"view_score_multiplier": 1.1, "difficulty_modifier": 1.2},
                    "forest_valley": {"view_score_multiplier": 0.8, "difficulty_modifier": 0.6},
                    "plateau_ridge": {"view_score_multiplier": 0.9, "difficulty_modifier": 0.7},
                    "fjord_valley": {"view_score_multiplier": 1.0, "difficulty_modifier": 0.9}
                }
            }
    
    def calculate_personalized_score(self, destination: dict, weather_data: dict, 
                                   snow_data: dict, avalanche_data: Optional[dict], 
                                   distance_km: float, max_distance_km: float,
                                   user_profile: UserProfile, 
                                   max_walking_hours: float = 0) -> ScoringResult:
        """
        Calculate personalized score for a destination based on user profile
        Enhanced with snow depth analysis and walking requirements
        
        Args:
            destination: Destination data from ski_destinations.json
            weather_data: Weather data from Yr.no
            snow_data: Snow data from SeNorge
            avalanche_data: Avalanche data from Varsom (can be None)
            distance_km: Distance to destination
            max_distance_km: Maximum allowed distance
            user_profile: User's personality profile
            max_walking_hours: Maximum hours user is willing to walk
            
        Returns:
            ScoringResult: Comprehensive scoring result
        """
        
        # Check if avalanche data is available
        avalanche_data_available = avalanche_data is not None
        
        # NEW: Enhanced snow depth analysis
        snow_depth_analysis = None
        if snow_data:
            # Convert destination to format expected by snow depth service
            dest_for_analysis = {
                'name': destination.get('name', 'Unknown'),
                'start_elevation': destination.get('elevation_range', [500, 1200])[0],
                'summit_elevation': destination.get('elevation_range', [500, 1200])[1],
                'distance_km': 5  # Default ski tour distance
            }
            
            snow_depth_analysis = self.snow_depth_service.analyze_destination_snow(
                dest_for_analysis, snow_data, max_walking_hours
            )
        
        # Get personalized weights and adjust for missing avalanche data
        weights = self._calculate_personalized_weights(user_profile, avalanche_data_available)
        
        # Calculate individual component scores with enhanced snow analysis
        weather_score = self._calculate_weather_score(weather_data, user_profile)
        snow_score = self._calculate_enhanced_snow_score(snow_data, snow_depth_analysis, user_profile)
        avalanche_score = self._calculate_avalanche_score(avalanche_data, user_profile) if avalanche_data_available else None
        view_terrain_score = self._calculate_view_terrain_score(destination, user_profile)
        distance_score = self._calculate_distance_score(distance_km, max_distance_km)
        
        # Check if within range and skiable
        within_range = distance_km <= max_distance_km
        
        # NEW: Apply penalties for poor snow conditions
        if snow_depth_analysis and not snow_depth_analysis.is_skiable:
            # Significant penalty if destination is not skiable
            snow_score *= 0.3
            within_range = False  # Treat as out of range if not skiable
        elif snow_depth_analysis and snow_depth_analysis.damage_risk:
            # Moderate penalty for rock damage risk
            snow_score *= 0.7
        
        # Apply personalized weighting (avalanche weight redistributed if no data)
        if avalanche_data_available:
            total_score = (
                weather_score * weights['weather'] +
                snow_score * weights['snow'] +
                avalanche_score * weights['avalanche'] +
                view_terrain_score * weights['view_terrain'] +
                distance_score * weights['distance']
            )
        else:
            # No avalanche data - redistribute weight to other components
            total_score = (
                weather_score * weights['weather'] +
                snow_score * weights['snow'] +
                view_terrain_score * weights['view_terrain'] +
                distance_score * weights['distance']
            )
        
        # Apply out-of-range penalty if needed
        if not within_range:
            total_score *= 0.7  # 30% penalty for out-of-range destinations
        
        # Create component scores dictionary
        component_scores = {
            'weather': weather_score,
            'snow': snow_score, 
            'avalanche': avalanche_score,
            'view_terrain': view_terrain_score,
            'distance': distance_score,
            'weights_applied': weights,
            'avalanche_data_available': avalanche_data_available,
            'snow_depth_analyzed': snow_depth_analysis is not None
        }
        
        # Generate personalized summary with enhanced snow info
        summary = self._generate_enhanced_personalized_summary(
            destination, weather_data, snow_data, avalanche_data, 
            distance_km, user_profile, component_scores, snow_depth_analysis
        )
        
        return ScoringResult(
            destination_name=destination['name'],
            total_score=total_score,
            component_scores=component_scores,
            weather_score=weather_score,
            snow_score=snow_score,
            avalanche_score=avalanche_score,
            view_terrain_score=view_terrain_score,
            distance_score=distance_score,
            within_range=within_range,
            personalized_summary=summary,
            avalanche_data_available=avalanche_data_available,
            snow_depth_analysis=snow_depth_analysis
        )
    
    def _calculate_personalized_weights(self, user_profile: UserProfile, 
                                      avalanche_data_available: bool) -> Dict[str, float]:
        """
        Calculate scoring weights based on user personality
        Redistributes avalanche weight if no avalanche data available
        """
        weights = self.base_weights.copy()
        
        # Adjust based on powder priority (0-10 scale)
        powder_adjustment = (user_profile.powder_priority - 5) * 0.02  # -0.1 to +0.1
        weights['snow'] += powder_adjustment
        weights['weather'] -= powder_adjustment * 0.5
        
        # Adjust based on view priority
        view_adjustment = (user_profile.view_priority - 5) * 0.02
        weights['weather'] += view_adjustment * 0.75  # Clear weather needed for views
        weights['view_terrain'] += view_adjustment * 0.5
        weights['snow'] -= view_adjustment * 0.5
        
        # Adjust based on safety priority
        safety_adjustment = (user_profile.safety_priority - 5) * 0.02
        weights['avalanche'] += safety_adjustment
        weights['distance'] += safety_adjustment * 0.3  # Prefer closer = safer
        weights['snow'] -= safety_adjustment * 0.3
        
        # Adjust based on adventure seeking
        adventure_adjustment = (user_profile.adventure_seeking - 5) * 0.01
        weights['view_terrain'] += adventure_adjustment
        weights['distance'] -= adventure_adjustment * 0.5  # Willing to travel farther
        
        # Handle missing avalanche data by redistributing weight
        if not avalanche_data_available:
            avalanche_weight = weights['avalanche']
            weights['avalanche'] = 0  # Set to 0 since no data
            
            # Redistribute avalanche weight proportionally to other components
            redistribution_factor = avalanche_weight / (1 - avalanche_weight)
            weights['snow'] += weights['snow'] * redistribution_factor * 0.4  # 40% to snow
            weights['weather'] += weights['weather'] * redistribution_factor * 0.3  # 30% to weather
            weights['view_terrain'] += weights['view_terrain'] * redistribution_factor * 0.2  # 20% to terrain
            weights['distance'] += weights['distance'] * redistribution_factor * 0.1  # 10% to distance
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights
    
    def _calculate_weather_score(self, weather_data: dict, user_profile: UserProfile) -> float:
        """Calculate weather score with user preference weighting"""
        if not weather_data:
            return 50.0
        
        # Base weather score (0-100)
        base_score = 0
        
        # Temperature scoring (enhanced for ski touring)
        temp = weather_data.get('avg_temp_24h', 0)
        if -5 <= temp <= 5:
            base_score += 40  # Perfect ski touring temps
        elif -10 <= temp <= 10:
            base_score += 30  # Good temps
        elif -15 <= temp <= 15:
            base_score += 20  # Acceptable
        else:
            base_score += 10  # Challenging conditions
        
        # Precipitation scoring (good visibility preferred)
        precip = weather_data.get('total_precipitation_24h', 0)
        if precip == 0:
            visibility_score = 30  # Clear skies
        elif precip < 2:
            visibility_score = 20  # Light precipitation
        elif precip < 5:
            visibility_score = 10  # Moderate precipitation
        else:
            visibility_score = 0   # Heavy precipitation
        
        # Adjust visibility importance based on user view priority
        view_multiplier = 0.5 + (user_profile.view_priority / 10) * 0.5  # 0.5 to 1.0
        base_score += visibility_score * view_multiplier
        
        # Wind scoring
        wind = weather_data.get('current_wind_speed', 0)
        if wind < 5:
            base_score += 15  # Calm
        elif wind < 10:
            base_score += 10  # Moderate
        elif wind < 15:
            base_score += 5   # Windy
        # Strong wind gets 0 points
        
        # Humidity comfort
        humidity = weather_data.get('current_humidity', 50)
        if 40 <= humidity <= 70:
            base_score += 15  # Comfortable
        
        return min(base_score, 100)
    
    def _calculate_enhanced_snow_score(self, snow_data: dict, snow_depth_analysis: Optional[SnowDepthAnalysis], 
                                     user_profile: UserProfile) -> float:
        """
        Calculate enhanced snow score using both basic snow data and detailed analysis
        """
        if not snow_data:
            return 30.0
        
        # Start with basic snow score
        base_score = self._calculate_basic_snow_score(snow_data, user_profile)
        
        # Apply enhancements from snow depth analysis
        if snow_depth_analysis:
            # Penalty for walking requirements
            if snow_depth_analysis.walking_required:
                if snow_depth_analysis.walking_time_hours > 2:
                    base_score *= 0.5  # Major penalty for long walks
                elif snow_depth_analysis.walking_time_hours > 1:
                    base_score *= 0.7  # Moderate penalty
                elif snow_depth_analysis.walking_time_hours > 0.5:
                    base_score *= 0.9  # Minor penalty
            
            # Penalty for damage risk
            if snow_depth_analysis.damage_risk:
                base_score *= 0.8  # Penalty for potential ski damage
            
            # Bonus for excellent snow coverage
            if (snow_depth_analysis.min_snow_depth > 75 and 
                not snow_depth_analysis.walking_required):
                base_score *= 1.1  # Bonus for excellent conditions
        
        return min(base_score, 100)
    
    def _calculate_basic_snow_score(self, snow_data: dict, user_profile: UserProfile) -> float:
        """Calculate basic snow score from snow data"""
        score = 0
        
        # Snow Depth (40 points max)
        snow_depth = snow_data.get('snow_depth_cm', 0)
        if snow_depth >= 50:
            score += 40  # Excellent base
        elif snow_depth >= 30:
            score += 25  # Marginal
        elif snow_depth >= 20:
            score += 10  # Poor
        
        # Recent Snowfall (30 points max) - Weighted by powder priority
        recent_snow = snow_data.get('snowfall_3days_cm', 0)
        powder_multiplier = 0.5 + (user_profile.powder_priority / 10) * 0.5
        
        if recent_snow >= 30:
            fresh_score = 30  # Epic powder day!
        elif recent_snow >= 15:
            fresh_score = 20  # Good fresh snow
        elif recent_snow >= 5:
            fresh_score = 10  # Some fresh snow
        else:
            fresh_score = 0   # Old snow
        
        score += fresh_score * powder_multiplier
        
        # Temperature Stability (20 points max)
        temp_trend = snow_data.get('temperature_trend', 'stable')
        if temp_trend == 'stable':
            score += 20
        elif temp_trend == 'cooling':
            score += 15
        elif temp_trend == 'warming':
            score += 5
        
        # Wind Impact (10 points max)
        wind_effect = snow_data.get('wind_effect', 'minimal')
        if wind_effect == 'minimal':
            score += 10
        elif wind_effect == 'moderate':
            score += 5
        
        return min(score, 100)
    
    def _calculate_avalanche_score(self, avalanche_data: Optional[dict], user_profile: UserProfile) -> Optional[float]:
        """
        Calculate avalanche safety score weighted by user risk tolerance
        Returns None if no avalanche data available
        """
        if not avalanche_data:
            return None  # No data available
        
        danger_level = avalanche_data.get('danger_level', 3)
        
        # Base safety scores by danger level
        base_safety_scores = {
            1: 100,  # Low danger - generally safe
            2: 80,   # Moderate danger - heightened awareness
            3: 50,   # Considerable danger - dangerous conditions
            4: 20,   # High danger - very dangerous
            5: 0     # Very high danger - avoid avalanche terrain
        }
        
        base_score = base_safety_scores.get(danger_level, 50)
        
        # Adjust based on user risk tolerance
        risk_adjustments = {
            'conservative': {'multiplier': 1.0, 'penalty_increase': 1.5},
            'moderate': {'multiplier': 1.0, 'penalty_increase': 1.0},
            'aggressive': {'multiplier': 0.8, 'penalty_increase': 0.7}
        }
        
        adjustment = risk_adjustments.get(user_profile.risk_tolerance, risk_adjustments['moderate'])
        
        # Apply risk tolerance multiplier
        if danger_level >= 3:  # Only apply to dangerous conditions
            penalty = (100 - base_score) * adjustment['penalty_increase']
            adjusted_score = 100 - penalty
        else:
            adjusted_score = base_score
        
        # Specific avalanche problems penalties
        problems = avalanche_data.get('avalanche_problems', [])
        problem_penalties = {
            'persistent_weak_layer': -15,  # Very concerning
            'wind_slab': -8,               # Manageable with route choice
            'new_snow': -8,                # Temporary problem
            'wet_snow': -5                 # Timing dependent
        }
        
        for problem in problems:
            penalty = problem_penalties.get(problem, 0)
            penalty *= adjustment['penalty_increase']  # Adjust penalty by risk tolerance
            adjusted_score += penalty
        
        return max(0, min(100, adjusted_score))
    
    def _calculate_view_terrain_score(self, destination: dict, user_profile: UserProfile) -> float:
        """Calculate view and terrain score based on user preferences"""
        base_view_score = destination.get('view_score', 70)
        terrain_type = destination.get('terrain_type', 'forest_valley')
        
        # Get terrain type multiplier
        terrain_config = self.terrain_types.get('terrain_types', {}).get(terrain_type, {})
        view_multiplier = terrain_config.get('view_score_multiplier', 1.0)
        
        # Apply terrain type multiplier
        terrain_adjusted_score = base_view_score * view_multiplier
        
        # Boost score if terrain matches user preference
        if terrain_type == user_profile.terrain_preference:
            terrain_adjusted_score += 15  # Significant boost for preferred terrain
        
        # Weight by user's view priority
        view_weight = 0.3 + (user_profile.view_priority / 10) * 0.7  # 0.3 to 1.0
        final_score = terrain_adjusted_score * view_weight
        
        # Add accessibility bonus/penalty based on user adventure seeking
        access_type = destination.get('access', 'road_access')
        adventure_factor = user_profile.adventure_seeking / 10  # 0.0 to 1.0
        
        access_adjustments = {
            'road_access': -5 + (adventure_factor * 10),  # Boring for adventurers
            'lift_access': 0,  # Neutral
            'hut_access': 5 * adventure_factor,  # Good for adventurers
            'boat_or_snowmobile': 10 * adventure_factor,  # Great for adventurers
            'road_closed_winter': 8 * adventure_factor  # Adventure bonus
        }
        
        access_bonus = access_adjustments.get(access_type, 0)
        final_score += access_bonus
        
        return max(0, min(100, final_score))
    
    def _calculate_distance_score(self, distance_km: float, max_distance_km: float) -> float:
        """Calculate distance score (closer is better)"""
        if distance_km <= max_distance_km:
            # Linear scoring: full points at 0km, 0 points at max distance
            return 100 * (1 - distance_km / max_distance_km)
        else:
            # Penalty for being outside range
            return 0
    
    def _generate_enhanced_personalized_summary(self, destination: dict, weather_data: dict,
                                              snow_data: dict, avalanche_data: Optional[dict], 
                                              distance_km: float, user_profile: UserProfile,
                                              component_scores: dict, 
                                              snow_depth_analysis: Optional[SnowDepthAnalysis]) -> str:
        """Generate enhanced personalized summary with snow depth analysis"""
        
        summary_parts = []
        
        # Distance and access
        driving_time = distance_km / 70  # Assume 70 km/h average
        summary_parts.append(f"🚗 {distance_km:.0f}km ({driving_time:.1f}h drive)")
        
        # Enhanced snow summary with depth analysis
        if snow_depth_analysis:
            if snow_depth_analysis.walking_required:
                if snow_depth_analysis.walking_time_hours > 1:
                    summary_parts.append(f"🥾 {snow_depth_analysis.walking_time_hours:.1f}h walk to snow")
                else:
                    summary_parts.append(f"🥾 {snow_depth_analysis.walking_time_hours*60:.0f}min walk to snow")
            else:
                summary_parts.append("🅿️ Ski from parking")
            
            if snow_depth_analysis.damage_risk:
                summary_parts.append("⚠️ Rock damage risk")
            elif snow_depth_analysis.min_snow_depth > 75:
                summary_parts.append("❄️ Excellent snow coverage")
            else:
                summary_parts.append(f"❄️ {snow_depth_analysis.min_snow_depth:.0f}cm min depth")
        elif snow_data:
            snow_depth = snow_data.get('snow_depth_cm', 0)
            recent_snow = snow_data.get('snowfall_3days_cm', 0)
            
            if user_profile.powder_priority >= 7:
                if recent_snow >= 15:
                    summary_parts.append(f"❄️ Fresh powder! ({recent_snow}cm recent)")
                elif snow_depth >= 50:
                    summary_parts.append(f"❄️ Good base ({snow_depth}cm)")
                else:
                    summary_parts.append("❄️ Limited snow conditions")
            else:
                if snow_depth >= 50:
                    summary_parts.append("❄️ Adequate snow coverage")
                else:
                    summary_parts.append("❄️ Watch for rocks")
        
        # Weather summary with user preference context
        if weather_data:
            temp = weather_data.get('avg_temp_24h', 0)
            precip = weather_data.get('total_precipitation_24h', 0)
            
            if user_profile.view_priority >= 7:
                if precip == 0:
                    summary_parts.append("☀️ Clear skies for epic views")
                else:
                    summary_parts.append(f"🌧️ Limited visibility ({precip:.1f}mm)")
            
            summary_parts.append(f"🌡️ {temp:.1f}°C")
        
        # Avalanche summary with risk tolerance context
        if avalanche_data:
            danger_level = avalanche_data.get('danger_level', 3)
            danger_text = avalanche_data.get('danger_text', 'Unknown')
            
            if user_profile.safety_priority >= 7:
                if danger_level <= 2:
                    summary_parts.append(f"✅ Avalanche danger {danger_level}/5 ({danger_text.replace('avalanche danger', '').strip()})")
                else:
                    summary_parts.append(f"⚠️ Avalanche danger {danger_level}/5 - Use caution")
            else:
                summary_parts.append(f"⚠️ Avalanche danger {danger_level}/5")
        else:
            summary_parts.append("📅 No avalanche warnings available")
        
        # Terrain match summary
        terrain_type = destination.get('terrain_type', 'unknown')
        if terrain_type == user_profile.terrain_preference:
            terrain_names = {
                'coastal_alpine': '🌊 Perfect coastal alpine terrain',
                'high_alpine': '🏔️ Ideal high alpine conditions',
                'forest_valley': '🌲 Your preferred forest terrain',
                'plateau_ridge': '🌬️ Open plateau as you like',
                'fjord_valley': '🏞️ Beautiful fjord valley setting'
            }
            summary_parts.append(terrain_names.get(terrain_type, '⛰️ Great terrain match'))
        
        # Add personality-specific highlights
        if user_profile.powder_priority >= 8 and snow_data and snow_data.get('snowfall_3days_cm', 0) >= 20:
            summary_parts.append("🎿 Powder hunter's paradise!")
        elif user_profile.view_priority >= 8 and destination.get('view_score', 0) >= 90:
            summary_parts.append("📸 Incredible scenic potential!")
        elif user_profile.adventure_seeking >= 8 and destination.get('technical_level', 0) >= 7:
            summary_parts.append("⚡ Epic adventure potential!")
        
        return " • ".join(summary_parts)
    
    def rank_destinations(self, destinations: List[dict], scoring_results: List[ScoringResult],
                         user_profile: UserProfile) -> List[Tuple[dict, ScoringResult]]:
        """
        Rank destinations by personalized scores and return sorted list
        Enhanced to consider snow depth analysis
        """
        # Combine destinations with their scores
        destination_scores = list(zip(destinations, scoring_results))
        
        # Sort by total score (highest first)
        ranked = sorted(destination_scores, key=lambda x: x[1].total_score, reverse=True)
        
        # Separate skiable vs non-skiable destinations
        skiable = []
        non_skiable = []
        
        for dest, score in ranked:
            if (score.snow_depth_analysis and 
                not score.snow_depth_analysis.is_skiable):
                non_skiable.append((dest, score))
            else:
                skiable.append((dest, score))
        
        # Separate within-range and out-of-range from skiable destinations
        within_range = [(dest, score) for dest, score in skiable if score.within_range]
        out_of_range = [(dest, score) for dest, score in skiable if not score.within_range]
        
        # Return skiable within-range first, then out-of-range, then non-skiable for reference
        return within_range + out_of_range[:2] + non_skiable[:1]
    
    def get_scoring_explanation(self, user_profile: UserProfile, avalanche_data_available: bool = True) -> str:
        """Generate explanation of how scoring works for this user"""
        weights = self._calculate_personalized_weights(user_profile, avalanche_data_available)
        
        explanations = []
        
        if weights['snow'] > 0.40:
            explanations.append(f"❄️ Snow conditions heavily weighted ({weights['snow']:.1%}) - you prioritize powder!")
        elif weights['snow'] < 0.30:
            explanations.append(f"❄️ Snow conditions moderately weighted ({weights['snow']:.1%}) - other factors matter more")
        
        if weights['weather'] > 0.30:
            explanations.append(f"🌤️ Weather/visibility strongly weighted ({weights['weather']:.1%}) - you want clear views!")
        
        if avalanche_data_available:
            if weights['avalanche'] > 0.30:
                explanations.append(f"⚠️ Safety heavily emphasized ({weights['avalanche']:.1%}) - conservative approach")
            elif weights['avalanche'] < 0.20:
                explanations.append(f"⚠️ Moderate safety weighting ({weights['avalanche']:.1%}) - calculated risks accepted")
        else:
            explanations.append("📅 Avalanche data not available - weights redistributed to other factors")
        
        if weights['view_terrain'] > 0.15:
            explanations.append(f"⛰️ Terrain/views important ({weights['view_terrain']:.1%}) - scenery matters!")
        
        # Add snow depth analysis note
        explanations.append("🎿 Enhanced with walking requirements and snow depth analysis")
        
        return "🎯 Your personalized scoring: " + " • ".join(explanations)