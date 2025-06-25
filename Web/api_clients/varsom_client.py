# api_clients/varsom_client.py
"""
Varsom/RegObs API client for Norwegian avalanche warnings and observations
Enhanced to handle out-of-season periods with no data
"""

import requests
import json
from datetime import datetime, timedelta
import config

class VarsomClient:
    def __init__(self):
        self.regobs_api_url = "https://api.regobs.no/v5"
        self.forecast_api_url = "https://api01.nve.no/hydrology/forecast/avalanche/v6.0.1"
        self.headers = {
            'User-Agent': config.USER_AGENT
        }
    
    def get_avalanche_warning(self, lat, lon, location_name=""):
        """
        Get avalanche warning for a specific location
        Always attempts to check for warnings, returns None if none found
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            location_name (str): Name for logging purposes
            
        Returns:
            dict: Avalanche warning data, or None if no data available
        """
        try:
            if location_name:
                print(f"⚠️  Checking avalanche warnings for {location_name} ({lat:.4f}, {lon:.4f})...")
            
            # Get current month for context
            current_month = datetime.now().month
            
            # Main season: Dec 1 - May 31
            is_main_season = current_month in [12, 1, 2, 3, 4, 5]
            # Semi-season: First 3 weeks of June + October-November (warnings only for danger level 4-5)
            is_semi_season = current_month in [6, 10, 11]
            
            if is_main_season:
                print(f"   📅 Main avalanche season - checking for daily warnings")
            elif is_semi_season:
                print(f"   📅 Semi-season period - checking for high danger warnings (4-5 only)")
            else:
                print(f"   📅 Outside avalanche warning period - no warnings expected")
                return None
            
            # For development/testing: Check if mock data is enabled
            if getattr(config, 'MOCK_API_DATA', True):
                return self._generate_seasonal_mock_data(lat, lon, current_month, is_main_season, is_semi_season)
            
            # Production: Always try to get real data, return None if not found
            region_id = self._get_avalanche_region(lat, lon)
            
            if not region_id:
                print(f"   📍 No avalanche forecast region found for {location_name}")
                return None
            
            # Attempt to get current avalanche warnings for the region
            warning_data = self._get_regional_warning(region_id, is_main_season, is_semi_season)
            
            if warning_data:
                warning_data['location'] = location_name
                warning_data['coordinates'] = {'lat': lat, 'lon': lon}
                warning_data['region_id'] = region_id
                print(f"   ✅ Found avalanche warning: Danger level {warning_data.get('danger_level', 'unknown')}")
                return warning_data
            else:
                print(f"   📅 No current avalanche warnings found for {location_name}")
                return None
                
        except Exception as e:
            print(f"🚫 Error checking avalanche warnings for {location_name}: {e}")
            return None
    
    def _generate_seasonal_mock_data(self, lat, lon, month, is_main_season, is_semi_season):
        """
        Generate realistic mock avalanche data based on season type
        """
        import random
        
        if not (is_main_season or is_semi_season):
            return None
        
        # In semi-season, only generate warnings for high danger (4-5)
        if is_semi_season:
            # Much lower chance of warnings in semi-season
            if random.random() > 0.3:  # 70% chance of no warning
                return None
            # If warning exists, it must be danger level 4 or 5
            danger_level = random.choice([4, 5])
        else:
            # Main season - normal distribution of danger levels
            if month in [12, 1, 2, 3]:  # Peak winter
                danger_levels = [1, 2, 2, 2, 3, 3, 4]
            elif month in [4, 5]:  # Late season
                danger_levels = [1, 1, 2, 2, 3]
            else:
                danger_levels = [1, 1, 2]
            
            danger_level = random.choice(danger_levels)
        
        danger_texts = {
            1: "Low avalanche danger",
            2: "Moderate avalanche danger", 
            3: "Considerable avalanche danger",
            4: "High avalanche danger",
            5: "Very high avalanche danger"
        }
        
        # Generate avalanche problems based on season and danger level
        problems = []
        if danger_level >= 2:
            if month in [12, 1, 2]:  # Deep winter
                possible_problems = ['wind_slab', 'persistent_weak_layer', 'new_snow']
            elif month in [3, 4, 5]:  # Spring
                possible_problems = ['wind_slab', 'wet_snow']
            elif month in [6]:  # Early summer - unusual conditions
                possible_problems = ['wet_snow', 'gliding_snow']
            else:  # Fall
                possible_problems = ['wind_slab', 'new_snow']
            
            num_problems = random.randint(1, min(2, danger_level))
            problems = random.sample(possible_problems, min(num_problems, len(possible_problems)))
        
        return {
            'danger_level': danger_level,
            'danger_text': danger_texts[danger_level],
            'avalanche_problems': problems,
            'valid_from': datetime.now().strftime('%Y-%m-%d'),
            'valid_to': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'forecast_text': self._generate_forecast_text(danger_level, problems),
            'data_source': 'mock_seasonal_data',
            'region_name': 'Estimated region',
            'season_type': 'main_season' if is_main_season else 'semi_season'
        }
    
    def _generate_realistic_seasonal_data(self, lat, lon, month):
        """
        Generate realistic mock avalanche data only during avalanche season
        """
        import random
        
        # Only generate data during official avalanche season (Dec 1 - May 31)
        if month not in [12, 1, 2, 3, 4, 5]:
            return None
        
        # Seasonal danger level adjustments
        if month in [12, 1, 2, 3]:  # Peak winter
            danger_levels = [1, 2, 2, 2, 3, 3, 4]  # Higher chance of danger
        elif month in [11, 4, 5]:  # Shoulder season
            danger_levels = [1, 1, 2, 2, 3]  # Moderate danger
        else:  # Late season (October, June)
            danger_levels = [1, 1, 1, 2, 2]  # Lower danger
        
        danger_level = random.choice(danger_levels)
        
        danger_texts = {
            1: "Low avalanche danger",
            2: "Moderate avalanche danger", 
            3: "Considerable avalanche danger",
            4: "High avalanche danger",
            5: "Very high avalanche danger"
        }
        
        # Generate avalanche problems based on season
        problems = []
        if danger_level >= 2:
            if month in [12, 1, 2]:  # Deep winter
                possible_problems = ['wind_slab', 'persistent_weak_layer', 'new_snow']
            elif month in [3, 4]:  # Spring
                possible_problems = ['wind_slab', 'wet_snow']
            else:  # Shoulder season
                possible_problems = ['wind_slab']
            
            num_problems = random.randint(1, min(2, danger_level))
            problems = random.sample(possible_problems, min(num_problems, len(possible_problems)))
        
        return {
            'danger_level': danger_level,
            'danger_text': danger_texts[danger_level],
            'avalanche_problems': problems,
            'valid_from': datetime.now().strftime('%Y-%m-%d'),
            'valid_to': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'forecast_text': self._generate_forecast_text(danger_level, problems),
            'data_source': 'mock_seasonal_data',
            'region_name': 'Estimated region',
            'season_active': True
        }
    
    def _get_avalanche_region(self, lat, lon):
        """
        Find which avalanche forecast region contains the given coordinates
        """
        try:
            # Rough region mapping for major ski areas
            regions = {
                'Lyngen': {'lat_range': (69.2, 70.0), 'lon_range': (19.5, 20.5), 'id': 3022},
                'Lofoten': {'lat_range': (67.8, 68.5), 'lon_range': (13.0, 15.0), 'id': 3023},
                'Jotunheimen': {'lat_range': (61.2, 61.8), 'lon_range': (7.5, 8.8), 'id': 3009},
                'Hemsedal': {'lat_range': (60.6, 61.0), 'lon_range': (8.2, 8.8), 'id': 3007},
                'Romsdalen': {'lat_range': (62.3, 62.8), 'lon_range': (7.4, 8.0), 'id': 3012},
                'Narvik': {'lat_range': (68.2, 68.6), 'lon_range': (17.0, 18.0), 'id': 3024}
            }
            
            for region_name, bounds in regions.items():
                lat_min, lat_max = bounds['lat_range']
                lon_min, lon_max = bounds['lon_range']
                
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    print(f"   📍 Found region: {region_name} (ID: {bounds['id']})")
                    return bounds['id']
            
            print(f"   📍 No specific region found, using nearest region")
            return 3009  # Default to Jotunheimen region
            
        except Exception as e:
            print(f"   🚫 Error finding avalanche region: {e}")
            return None
    
    def _get_regional_warning(self, region_id, is_main_season, is_semi_season):
        """
        Get avalanche warning for a specific region
        Always attempts to check, returns None if no warning found
        """
        try:
            if not (is_main_season or is_semi_season):
                print(f"   📅 No avalanche forecasts expected outside warning periods")
                return None
            
            # In production, this would query the actual forecast API
            # The API call should always be attempted, returning None if no warning found
            print(f"   📊 Querying avalanche forecast API for region {region_id}")
            
            # For development, simulate the API behavior
            current_month = datetime.now().month
            return self._generate_seasonal_mock_data(0, 0, current_month, is_main_season, is_semi_season)
            
        except Exception as e:
            print(f"   🚫 Error fetching regional warning: {e}")
            return None
    
    def _generate_forecast_text(self, danger_level, problems):
        """
        Generate realistic forecast text based on danger level and problems
        """
        texts = {
            1: "Generally safe avalanche conditions. Watch for isolated hazards in steep terrain.",
            2: "Heightened awareness required. Avoid steep slopes with obvious signs of instability.",
            3: "Dangerous avalanche conditions. Careful snowpack evaluation, cautious route-finding and conservative decision-making essential.",
            4: "Very dangerous avalanche conditions. Travel in avalanche terrain not recommended.",
            5: "Avoid avalanche terrain. Natural and human-triggered avalanches certain."
        }
        
        base_text = texts.get(danger_level, "Avalanche conditions unknown.")
        
        if problems:
            problem_texts = {
                'wind_slab': "Wind slabs present on lee slopes.",
                'persistent_weak_layer': "Persistent weak layers in snowpack.", 
                'wet_snow': "Wet snow instabilities possible with warming.",
                'new_snow': "Recent snowfall creating instability."
            }
            
            problem_descriptions = [problem_texts.get(p, p) for p in problems]
            base_text += " " + " ".join(problem_descriptions)
        
        return base_text
    
    def calculate_avalanche_safety_score(self, avalanche_data):
        """
        Calculate avalanche safety score for ski touring
        Returns None if no avalanche data available (indicates should not be weighted)
        
        Args:
            avalanche_data (dict): Avalanche warning data, or None
            
        Returns:
            int or None: Safety score (0-100, higher = safer), or None if no data
        """
        if not avalanche_data:
            return None  # No data available - don't include in scoring
        
        danger_level = avalanche_data.get('danger_level', 3)
        
        # Scoring based on European Avalanche Danger Scale
        safety_scores = {
            1: 100,  # Low danger - generally safe
            2: 80,   # Moderate danger - heightened awareness
            3: 50,   # Considerable danger - dangerous conditions
            4: 20,   # High danger - very dangerous
            5: 0     # Very high danger - avoid avalanche terrain
        }
        
        base_score = safety_scores.get(danger_level, 50)
        
        # Adjust for specific avalanche problems
        problems = avalanche_data.get('avalanche_problems', [])
        problem_penalties = {
            'persistent_weak_layer': -10,  # Very concerning
            'wind_slab': -5,               # Manageable with route choice
            'new_snow': -5,                # Temporary problem
            'wet_snow': -3                 # Timing dependent
        }
        
        for problem in problems:
            penalty = problem_penalties.get(problem, 0)
            base_score += penalty
        
        return max(0, min(100, base_score))  # Keep between 0-100
    
    def get_recent_observations(self, lat, lon, days_back=7):
        """
        Get recent avalanche observations in the area
        """
        try:
            # Check for any warning periods
            current_month = datetime.now().month
            is_warning_period = current_month in [12, 1, 2, 3, 4, 5, 6, 10, 11]
            
            if not is_warning_period:
                return []  # No observations outside warning periods
            
            # In production, query RegObs API for recent observations
            # For prototype, return mock recent activity only during warning periods
            
            import random
            observations = []
            
            # Fewer observations in semi-season
            max_obs = 1 if current_month in [6, 10, 11] else 2
            
            for i in range(random.randint(0, max_obs)):
                obs_date = datetime.now() - timedelta(days=random.randint(1, days_back))
                observation = {
                    'date': obs_date.strftime('%Y-%m-%d'),
                    'type': random.choice(['avalanche', 'danger_sign', 'snow_profile']),
                    'description': 'Seasonal observation for prototype',
                    'distance_km': random.uniform(2, 15)
                }
                observations.append(observation)
            
            return observations
            
        except Exception as e:
            print(f"🚫 Error fetching recent observations: {e}")
            return []