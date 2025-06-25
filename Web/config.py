# config.py
"""
Configuration file for Norway Ski Touring Planner
Enhanced with snow and avalanche API settings
"""

# API Configuration
USER_AGENT = "NorwaySkiTouringPlanner/2.0 (odinbo@stud.ntnu.no)"  # UPDATE THIS!

# API URLs
KARTVERKET_STEDSNAVN_API = "https://ws.geonorge.no/stedsnavn/v1/navn"
YR_WEATHER_API = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# New APIs for ski touring
SENORGE_THREDDS_BASE = "https://thredds.met.no/thredds"
REGOBS_API_BASE = "https://api.regobs.no/v5"
AVALANCHE_FORECAST_API = "https://api01.nve.no/hydrology/forecast/avalanche/v6.0.1"

# Driving distance estimates (hours: max km)
DRIVING_DISTANCES = {
    1: 90,   # 1 hour = max 90km
    3: 225,  # 3 hours = max 225km  
    5: 350   # 5 hours = max 350km
}

# Average driving speed for time estimates (km/h)
AVERAGE_DRIVING_SPEED = 70

# Scoring parameters - Enhanced for ski touring
WEATHER_SCORE_MAX = 100
SNOW_SCORE_MAX = 100
AVALANCHE_SCORE_MAX = 100
VIEW_TERRAIN_SCORE_MAX = 100
DISTANCE_PENALTY_MAX = 20
OUT_OF_RANGE_PENALTY = 30  # Reduced penalty for ski touring (more willing to travel)

# Temperature preferences for ski touring (Celsius)
OPTIMAL_SKI_TEMP_RANGE = (-5, 5)    # Perfect ski touring temps
GOOD_SKI_TEMP_RANGE = (-10, 10)     # Good skiing conditions
ACCEPTABLE_SKI_TEMP_RANGE = (-15, 15)  # Still workable

# Snow depth preferences (cm)
MINIMUM_SAFE_SNOW_DEPTH = 50  # Minimum to avoid rocks
GOOD_SNOW_DEPTH = 75          # Comfortable base
EXCELLENT_SNOW_DEPTH = 100    # Excellent coverage

# Fresh snow preferences (cm in last 3 days)
EPIC_POWDER_THRESHOLD = 30    # Epic powder day
GOOD_FRESH_SNOW = 15          # Good fresh snow
SOME_FRESH_SNOW = 5           # Some recent snow

# Wind thresholds (m/s)
CALM_WIND = 3                 # Calm conditions
MODERATE_WIND = 8             # Moderate wind
STRONG_WIND = 15              # Strong wind (concerning for avalanches)

# Avalanche danger level penalties (applied to safety score)
AVALANCHE_PENALTIES = {
    1: 0,    # Low danger - no penalty
    2: -5,   # Moderate danger - small penalty
    3: -20,  # Considerable danger - significant penalty
    4: -40,  # High danger - major penalty
    5: -60   # Very high danger - severe penalty
}

# File paths
DESTINATIONS_FILE = "data/ski_destinations.json"
TERRAIN_TYPES_FILE = "data/terrain_types.json"
RESULTS_DIR = "data/results"

# API rate limiting (seconds between requests)
API_DELAY = 0.7  # Slightly longer for multiple APIs

# Default search parameters
DEFAULT_MAX_RESULTS = 8
DEFAULT_KARTVERKET_RESULTS = 5

# User profile defaults
DEFAULT_USER_PROFILE = {
    'powder_priority': 5,
    'view_priority': 5,
    'safety_priority': 5,
    'adventure_seeking': 5,
    'social_preference': 5,
    'terrain_preference': 'balanced',
    'risk_tolerance': 'moderate',
    'experience_level': 'intermediate'
}

# Personality quiz settings
QUIZ_TIME_LIMIT_MINUTES = 5   # Suggested time limit
MIN_QUIZ_QUESTIONS = 5        # Minimum questions for valid profile
MAX_QUIZ_QUESTIONS = 10       # Maximum to avoid fatigue

# Scoring weight ranges (for personality adjustments)
MIN_SNOW_WEIGHT = 0.20        # Minimum snow importance
MAX_SNOW_WEIGHT = 0.55        # Maximum snow importance
MIN_WEATHER_WEIGHT = 0.15     # Minimum weather importance  
MAX_WEATHER_WEIGHT = 0.40     # Maximum weather importance
MIN_AVALANCHE_WEIGHT = 0.15   # Minimum safety importance
MAX_AVALANCHE_WEIGHT = 0.40   # Maximum safety importance

# Flask web app settings (for future web version)
FLASK_SECRET_KEY = "your-secret-key-here"  # Change this!
FLASK_DEBUG = True
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000

# CGI settings for university server
CGI_MODE = False              # Set to True when running on university server
CGI_SCRIPT_PATH = "/cgi-bin"  # Path where CGI scripts are located

# Logging settings
LOG_LEVEL = "INFO"            # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/ski_touring.log"
ENABLE_API_LOGGING = True     # Log API calls for debugging

# Cache settings (for production)
ENABLE_CACHING = False        # Enable caching to reduce API calls
CACHE_DURATION_MINUTES = 30   # How long to cache weather/snow data
CACHE_DIR = "cache"

# Development/testing settings
MOCK_API_DATA = False          # Use mock data instead of real API calls (for testing)
ENABLE_PROFILING = False      # Enable performance profiling
TEST_LOCATIONS = [            # Test locations for development
    {"name": "Trondheim", "lat": 63.4305, "lon": 10.3951},
    {"name": "Tromsø", "lat": 69.6492, "lon": 18.9553},
    {"name": "Oslo", "lat": 59.9139, "lon": 10.7522}
]

""" 
Old configuration file for Norway Weather Project 
# config.py

# API Configuration
USER_AGENT = "NorwayWeatherTips/1.0 (odinbo@stud.ntnu.no)"  # UPDATE THIS!

# API URLs
KARTVERKET_STEDSNAVN_API = "https://ws.geonorge.no/stedsnavn/v1/navn"
YR_WEATHER_API = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# Driving distance estimates (hours: max km)
DRIVING_DISTANCES = {
    1: 90,   # 1 hour = max 90km
    3: 225,  # 3 hours = max 225km  
    5: 350   # 5 hours = max 350km
}

# Average driving speed for time estimates (km/h)
AVERAGE_DRIVING_SPEED = 70

# Scoring parameters
WEATHER_SCORE_MAX = 100
DISTANCE_PENALTY_MAX = 20
OUT_OF_RANGE_PENALTY = 50

# Temperature preferences (Celsius)
OPTIMAL_TEMP_RANGE = (15, 25)
GOOD_TEMP_RANGE = (10, 30)
ACCEPTABLE_TEMP_RANGE = (5, 35)

# File paths
DESTINATIONS_FILE = "data/destinations.json"
RESULTS_DIR = "data/results"

# API rate limiting (seconds between requests)
API_DELAY = 0.5

# Default search parameters
DEFAULT_MAX_RESULTS = 8
DEFAULT_KARTVERKET_RESULTS = 5
"""