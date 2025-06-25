# services/enhanced_snow_depth_service.py
"""
Enhanced snow depth analysis for ski touring recommendations
Handles walking requirements and snow depth validation throughout trip elevation
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SnowDepthAnalysis:
    """Results of snow depth analysis for a ski destination"""
    destination_name: str
    base_snow_depth: float  # Snow depth at parking/start
    mid_elevation_snow_depth: float  # Snow depth at middle elevation
    summit_snow_depth: float  # Snow depth at summit
    min_snow_depth: float  # Minimum depth along route
    
    is_skiable: bool  # Can you ski the majority of the route?
    walking_required: bool  # Do you need to walk from parking?
    walking_distance_km: float  # Distance you need to walk
    walking_time_hours: float  # Time to walk to snow
    walking_elevation_gain: float  # Elevation gain while walking
    
    damage_risk: bool  # Risk of damaging skis due to rocks
    snow_warnings: List[str]  # List of warnings about snow conditions
    recommendation_notes: str  # Human-readable summary

class EnhancedSnowDepthService:
    def __init__(self):
        # Snow depth requirements
        self.MIN_SKIABLE_DEPTH = 25  # cm - minimum for skiing without damage
        self.PARKING_MIN_DEPTH = 10  # cm - minimum to even consider destination
        self.SAFE_SKIING_DEPTH = 50  # cm - safe skiing with no rock damage risk
        
        # Walking pace assumptions
        self.WALKING_SPEED_KMH = 3.5  # km/hour on flat terrain
        self.ELEVATION_GAIN_PER_15MIN = 100  # meters elevation gain every 15 minutes
        self.PACE_BUFFER_FACTOR = 1.2  # 20% buffer for slower hikers
    
    def analyze_destination_snow(self, destination: Dict, snow_data: Dict, 
                                max_walking_hours: float = 0) -> SnowDepthAnalysis:
        """
        Analyze snow conditions for a ski destination throughout the elevation profile
        
        Args:
            destination: Destination data including elevation profile
            snow_data: Snow data from SeNorge or similar service
            max_walking_hours: Maximum hours user is willing to walk (0 = no walking)
            
        Returns:
            SnowDepthAnalysis: Comprehensive analysis of snow conditions
        """
        dest_name = destination.get('name', 'Unknown')
        base_elevation = destination.get('start_elevation', 500)
        summit_elevation = destination.get('summit_elevation', 1200)
        trip_distance = destination.get('distance_km', 5)
        
        # Calculate elevations for analysis
        mid_elevation = (base_elevation + summit_elevation) / 2
        
        # Get snow depths at different elevations
        base_snow = self._estimate_snow_at_elevation(snow_data, base_elevation)
        mid_snow = self._estimate_snow_at_elevation(snow_data, mid_elevation)
        summit_snow = self._estimate_snow_at_elevation(snow_data, summit_elevation)
        min_snow = min(base_snow, mid_snow, summit_snow)
        
        # Determine if walking is required
        walking_required = base_snow < self.PARKING_MIN_DEPTH
        walking_distance = 0
        walking_time = 0
        walking_elevation = 0
        
        if walking_required:
            # Calculate where adequate snow starts
            snow_start_elevation = self._find_snow_start_elevation(
                snow_data, base_elevation, summit_elevation, self.PARKING_MIN_DEPTH
            )
            
            # Calculate walking requirements
            walking_elevation = snow_start_elevation - base_elevation
            walking_distance = self._calculate_walking_distance(walking_elevation, trip_distance)
            walking_time = self._calculate_walking_time(walking_distance, walking_elevation)
        
        # Determine if destination is skiable
        skiing_portion_snow = max(mid_snow, summit_snow)  # Best snow in skiing area
        is_skiable = (
            skiing_portion_snow >= self.MIN_SKIABLE_DEPTH and 
            (not walking_required or walking_time <= max_walking_hours)
        )
        
        # Check for damage risk
        damage_risk = min_snow < self.SAFE_SKIING_DEPTH
        
        # Generate warnings
        warnings = self._generate_snow_warnings(
            base_snow, mid_snow, summit_snow, walking_required, damage_risk
        )
        
        # Create recommendation notes
        notes = self._create_recommendation_notes(
            base_snow, mid_snow, summit_snow, walking_required, 
            walking_time, damage_risk, dest_name
        )
        
        return SnowDepthAnalysis(
            destination_name=dest_name,
            base_snow_depth=base_snow,
            mid_elevation_snow_depth=mid_snow,
            summit_snow_depth=summit_snow,
            min_snow_depth=min_snow,
            is_skiable=is_skiable,
            walking_required=walking_required,
            walking_distance_km=walking_distance,
            walking_time_hours=walking_time,
            walking_elevation_gain=walking_elevation,
            damage_risk=damage_risk,
            snow_warnings=warnings,
            recommendation_notes=notes
        )
    
    def _estimate_snow_at_elevation(self, snow_data: Dict, elevation: float) -> float:
        """
        Estimate snow depth at a specific elevation
        Uses base snow data and elevation-based adjustments
        """
        base_snow_depth = snow_data.get('snow_depth_cm', 0)
        reference_elevation = snow_data.get('elevation', 500)  # Elevation where measurement was taken
        
        # Snow generally increases with elevation (roughly 5-10cm per 100m)
        elevation_diff = elevation - reference_elevation
        snow_increase_rate = 7  # cm per 100m elevation gain
        
        estimated_snow = base_snow_depth + (elevation_diff / 100) * snow_increase_rate
        
        return max(0, estimated_snow)  # Snow can't be negative
    
    def _find_snow_start_elevation(self, snow_data: Dict, base_elevation: float, 
                                  summit_elevation: float, min_required_depth: float) -> float:
        """
        Find the elevation where adequate snow depth begins
        """
        # Binary search for snow start elevation
        low_elev = base_elevation
        high_elev = summit_elevation
        
        for _ in range(10):  # Max 10 iterations for precision
            mid_elev = (low_elev + high_elev) / 2
            snow_depth = self._estimate_snow_at_elevation(snow_data, mid_elev)
            
            if snow_depth >= min_required_depth:
                high_elev = mid_elev
            else:
                low_elev = mid_elev
            
            if abs(high_elev - low_elev) < 10:  # 10m precision
                break
        
        return high_elev
    
    def _calculate_walking_distance(self, elevation_gain: float, total_trip_distance: float) -> float:
        """
        Estimate horizontal walking distance based on elevation gain and trip profile
        """
        # Assume moderate trail grade (typically 8-15% for ski approaches)
        average_grade = 0.12  # 12% grade
        walking_distance = elevation_gain / average_grade / 1000  # Convert to km
        
        # Don't exceed half the total trip distance
        max_walking = total_trip_distance * 0.4
        
        return min(walking_distance, max_walking)
    
    def _calculate_walking_time(self, distance_km: float, elevation_gain: float) -> float:
        """
        Calculate walking time including both distance and elevation components
        """
        # Time for horizontal distance
        horizontal_time = distance_km / self.WALKING_SPEED_KMH
        
        # Time for elevation gain (100m every 15 minutes = 400m/hour)
        elevation_time = elevation_gain / 400
        
        # Take the maximum (they're not additive since elevation affects horizontal speed)
        total_time = max(horizontal_time, elevation_time)
        
        # Apply pace buffer for realistic timing
        return total_time * self.PACE_BUFFER_FACTOR
    
    def _generate_snow_warnings(self, base_snow: float, mid_snow: float, 
                               summit_snow: float, walking_required: bool, 
                               damage_risk: bool) -> List[str]:
        """Generate list of warnings about snow conditions"""
        warnings = []
        
        if walking_required:
            warnings.append("⚠️ Walking required from parking to reach snow")
        
        if damage_risk:
            if min(base_snow, mid_snow, summit_snow) < 25:
                warnings.append("🪨 HIGH RISK: Very shallow snow - expect rocks and ski damage")
            elif min(base_snow, mid_snow, summit_snow) < 40:
                warnings.append("⚠️ MODERATE RISK: Shallow snow - careful route choice needed")
        
        if max(base_snow, mid_snow, summit_snow) < 30:
            warnings.append("❄️ Generally poor snow conditions throughout route")
        
        if abs(base_snow - summit_snow) > 100:
            warnings.append("🏔️ Highly variable snow conditions by elevation")
        
        return warnings
    
    def _create_recommendation_notes(self, base_snow: float, mid_snow: float, 
                                   summit_snow: float, walking_required: bool,
                                   walking_time: float, damage_risk: bool, 
                                   dest_name: str) -> str:
        """Create human-readable recommendation notes"""
        notes = []
        
        # Snow depth summary
        if base_snow >= 50 and mid_snow >= 50:
            notes.append(f"❄️ Excellent snow: {base_snow:.0f}cm base, {summit_snow:.0f}cm summit")
        elif mid_snow >= 30:
            notes.append(f"❄️ Adequate snow: {mid_snow:.0f}cm mid-route, {summit_snow:.0f}cm summit")
        else:
            notes.append(f"❄️ Limited snow: {base_snow:.0f}cm base, {summit_snow:.0f}cm summit")
        
        # Walking requirements
        if walking_required:
            if walking_time < 0.5:
                notes.append(f"🥾 Short walk required: {walking_time*60:.0f} min to snow")
            elif walking_time < 1.5:
                notes.append(f"🥾 Moderate approach: {walking_time:.1f}h walk to snow")
            else:
                notes.append(f"🥾 Long approach: {walking_time:.1f}h walk required")
        else:
            notes.append("🅿️ Ski from parking")
        
        # Damage risk
        if damage_risk:
            notes.append("⚠️ Bring old skis - rock damage likely")
        else:
            notes.append("✅ Safe for good skis")
        
        return " • ".join(notes)
    
    def filter_destinations_by_snow(self, destinations: List[Dict], snow_analyses: List[SnowDepthAnalysis],
                                   max_walking_hours: float = 0) -> Tuple[List[Dict], List[SnowDepthAnalysis]]:
        """
        Filter destinations based on snow depth requirements and walking tolerance
        
        Returns:
            Tuple of (filtered_destinations, filtered_analyses)
        """
        valid_destinations = []
        valid_analyses = []
        
        for dest, analysis in zip(destinations, snow_analyses):
            if analysis.is_skiable and analysis.walking_time_hours <= max_walking_hours:
                valid_destinations.append(dest)
                valid_analyses.append(analysis)
        
        return valid_destinations, valid_analyses
    
    def get_walking_tolerance_options(self) -> Dict[str, float]:
        """Get predefined walking tolerance options for user selection"""
        return {
            "No walking - ski from parking": 0,
            "Up to 30 minutes walking": 0.5,
            "Up to 1 hour walking": 1.0,
            "Up to 2 hours walking": 2.0,
            "Up to 3 hours walking": 3.0,
            "I'll walk as long as needed": 24.0  # Effectively unlimited
        }
    
    def ask_walking_tolerance(self) -> float:
        """
        Interactive prompt to ask user about walking tolerance
        when no good skiing options are found nearby
        """
        print("🥾 No good skiing destinations found within reasonable driving distance.")
        print("   However, there might be options if you're willing to walk/hike to reach snow.")
        print()
        
        options = self.get_walking_tolerance_options()
        
        print("How far are you willing to walk from parking to reach good snow?")
        for i, (description, hours) in enumerate(options.items(), 1):
            if hours == 24:
                print(f"   {i}. {description}")
            else:
                print(f"   {i}. {description} ({hours}h)")
        print()
        
        while True:
            try:
                choice = int(input("Your choice (enter number): "))
                if 1 <= choice <= len(options):
                    selected_hours = list(options.values())[choice - 1]
                    selected_desc = list(options.keys())[choice - 1]
                    print(f"✅ Selected: {selected_desc}")
                    return selected_hours
                else:
                    print(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                print("Please enter a valid number")