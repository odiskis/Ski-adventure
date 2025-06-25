# config_web.py
"""
Web-specific configuration for Flask Ski Touring application
Extends the base config.py with web application settings
"""

import os
from datetime import timedelta

# Import base configuration
try:
    from config import *  # Import all base settings
except ImportError:
    # Fallback if base config not found
    USER_AGENT = "NorwaySkiTouringPlanner/2.0 (odinbo@stud.ntnu.no)"
    API_DELAY = 0.7
    MOCK_API_DATA = True

# Flask Web Application Settings
class Config:
    """Base configuration class"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production-2025'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 24 hour sessions
    
    # Security Settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = False  # Disabled for API endpoints, enable for forms if needed
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)  # Cache static files for 1 hour
    
    # Template Settings
    TEMPLATES_AUTO_RELOAD = True  # Reload templates automatically in development
    
    # API Settings (inherited from base config)
    API_TIMEOUT = 30  # seconds
    API_RETRIES = 3
    
    # Caching Settings
    CACHE_TYPE = 'simple'  # Use simple in-memory cache
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    
    # Development API settings
    MOCK_API_DATA = True  # Use mock data in development
    API_DELAY = 0.1  # Faster API calls in development
    
    # Development logging
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production security
    SESSION_COOKIE_SECURE = True  # HTTPS only
    WTF_CSRF_ENABLED = True
    
    # Production API settings
    MOCK_API_DATA = False  # Use real APIs in production
    API_DELAY = 0.7  # Respect API rate limits
    
    # Production caching
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = '/tmp/flask_cache'
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes
    
    # Production logging
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Testing settings
    WTF_CSRF_ENABLED = False
    MOCK_API_DATA = True
    API_DELAY = 0  # No delays in testing

# CGI/University Server specific settings
class CGIConfig(ProductionConfig):
    """Configuration for CGI deployment on university servers"""
    
    # CGI specific settings
    CGI_MODE = True
    DEBUG = False  # Never debug in CGI mode
    
    # File paths for CGI environment
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'
    
    # Cache in user directory (university servers often have restricted /tmp)
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = os.path.expanduser('~/cache/ski_app')
    
    # Conservative settings for shared hosting
    API_TIMEOUT = 10  # Shorter timeout
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
    
    # Log to user directory
    LOG_FILE = os.path.expanduser('~/logs/ski_app.log')
    
    # Session settings for CGI
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # Shorter sessions

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'cgi': CGIConfig,
    'default': DevelopmentConfig
}

# Web-specific constants
WEB_CONSTANTS = {
    # Pagination
    'RECOMMENDATIONS_PER_PAGE': 10,
    'QUIZ_QUESTIONS_PER_PAGE': 1,
    
    # UI Settings
    'DEFAULT_MAP_ZOOM': 7,
    'MAX_AUTOCOMPLETE_RESULTS': 8,
    'TOAST_DURATION_MS': 5000,
    
    # Form validation
    'MIN_LOCATION_CHARS': 2,
    'MAX_LOCATION_CHARS': 100,
    'VALID_DRIVING_HOURS': [1, 2, 3, 4, 5, 6],
    
    # File upload
    'ALLOWED_IMAGE_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif'},
    'MAX_IMAGE_SIZE_MB': 5,
    
    # Social sharing
    'SHARE_IMAGE_URL': '/static/images/share-image.jpg',
    'SHARE_DESCRIPTION': 'Find your perfect ski touring adventure in Norway',
    
    # Analytics (if enabled)
    'GOOGLE_ANALYTICS_ID': os.environ.get('GOOGLE_ANALYTICS_ID'),
    'ENABLE_ANALYTICS': os.environ.get('ENABLE_ANALYTICS', 'False').lower() == 'true'
}

# Error messages
ERROR_MESSAGES = {
    'location_not_found': 'Location not found. Please try a different Norwegian location.',
    'invalid_driving_hours': 'Invalid driving hours. Please select between 1-6 hours.',
    'quiz_session_expired': 'Your quiz session has expired. Please start over.',
    'api_error': 'Unable to fetch current conditions. Please try again later.',
    'network_error': 'Network error. Please check your connection and try again.',
    'server_error': 'Server error. Please try again later.',
    'invalid_input': 'Invalid input. Please check your entries and try again.',
    'session_expired': 'Your session has expired. Please start over.',
    'rate_limit_exceeded': 'Too many requests. Please wait a moment and try again.'
}

# Success messages
SUCCESS_MESSAGES = {
    'quiz_completed': 'Quiz completed successfully! Loading your recommendations...',
    'location_saved': 'Location saved successfully!',
    'preferences_updated': 'Your preferences have been updated.',
    'recommendations_refreshed': 'Recommendations updated with new preferences.',
    'profile_saved': 'Your profile has been saved for future use.',
    'tour_shared': 'Tour details shared successfully!'
}

# Navigation menu items
NAVIGATION_ITEMS = [
    {'name': 'Home', 'endpoint': 'index', 'icon': '🏠'},
    {'name': 'Plan Trip', 'endpoint': 'quiz', 'icon': '🎿'},
    {'name': 'My Recommendations', 'endpoint': 'recommendations', 'icon': '⭐', 'auth_required': True},
    {'name': 'About', 'endpoint': 'about', 'icon': 'ℹ️'}
]

# Footer links
FOOTER_LINKS = {
    'resources': [
        {'name': 'Varsom.no - Avalanche Warnings', 'url': 'https://varsom.no', 'external': True},
        {'name': 'SeNorge.no - Snow Conditions', 'url': 'https://senorge.no', 'external': True},
        {'name': 'Yr.no - Weather Forecasts', 'url': 'https://yr.no', 'external': True},
        {'name': 'UT.no - Trip Planning', 'url': 'https://ut.no', 'external': True}
    ],
    'safety': [
        {'name': 'Emergency Services: 112', 'url': 'tel:112'},
        {'name': 'Mountain Rescue Guide', 'url': 'https://www.rodekors.no/aktiviteter/redning/fjellredning/', 'external': True},
        {'name': 'Avalanche Safety Course', 'url': 'https://www.skiforeningen.no/', 'external': True}
    ],
    'data_sources': [
        {'name': 'MET Norway', 'url': 'https://met.no', 'external': True},
        {'name': 'SeNorge', 'url': 'https://senorge.no', 'external': True},
        {'name': 'Varsom', 'url': 'https://varsom.no', 'external': True},
        {'name': 'Kartverket', 'url': 'https://kartverket.no', 'external': True}
    ]
}

# Theme and styling
THEME_SETTINGS = {
    'primary_color': '#1e3c72',
    'secondary_color': '#2a5298',
    'accent_color': '#ff6b6b',
    'success_color': '#27ae60',
    'warning_color': '#f39c12',
    'error_color': '#e74c3c',
    'font_family': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    'border_radius': '10px',
    'box_shadow': '0 4px 15px rgba(0, 0, 0, 0.1)'
}

# API endpoints for frontend
API_ENDPOINTS = {
    'location_search': '/api/locations/search',
    'quiz_answer': '/api/quiz/answer',
    'recommendations_refresh': '/api/recommendations/refresh',
    'profile_save': '/api/profile/save',
    'profile_update': '/api/profile/update',
    'health_check': '/api/health'
}

# Default values
DEFAULTS = {
    'max_driving_hours': 3,
    'recommendations_per_page': 8,
    'quiz_timeout_minutes': 30,
    'session_lifetime_hours': 24,
    'cache_timeout_minutes': 5
}

# Feature flags
FEATURES = {
    'enable_user_accounts': False,  # Future feature
    'enable_trip_planning': False,  # Future feature
    'enable_social_sharing': True,
    'enable_offline_mode': False,  # Future feature
    'enable_push_notifications': False,  # Future feature
    'enable_advanced_filtering': True,
    'enable_map_integration': True,
    'enable_weather_alerts': True
}

# External service URLs
EXTERNAL_SERVICES = {
    'varsom_warning_url': 'https://varsom.no/en/',
    'senorge_snow_url': 'https://senorge.no/en',
    'yr_weather_url': 'https://yr.no/en',
    'ut_trip_url': 'https://ut.no/kart',
    'google_maps_api': 'https://maps.googleapis.com/maps/api',
    'emergency_services': {
        'general': '112',
        'medical': '113', 
        'fire': '110',
        'sea_rescue': '02800'
    }
}

# Utility functions for web app
def get_config():
    """Get the current configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    if os.environ.get('CGI_MODE'):
        return config['cgi']
    return config.get(env, config['default'])

def is_production():
    """Check if running in production mode"""
    return isinstance(get_config(), (ProductionConfig, CGIConfig))

def is_cgi_mode():
    """Check if running in CGI mode"""
    return isinstance(get_config(), CGIConfig) or os.environ.get('CGI_MODE')

def get_feature_flag(feature_name):
    """Get feature flag value"""
    return FEATURES.get(feature_name, False)

def get_error_message(error_key):
    """Get localized error message"""
    return ERROR_MESSAGES.get(error_key, 'An unexpected error occurred.')

def get_success_message(success_key):
    """Get localized success message"""
    return SUCCESS_MESSAGES.get(success_key, 'Operation completed successfully.')

# Export commonly used items
__all__ = [
    'Config', 'DevelopmentConfig', 'ProductionConfig', 'TestingConfig', 'CGIConfig',
    'config', 'WEB_CONSTANTS', 'ERROR_MESSAGES', 'SUCCESS_MESSAGES',
    'NAVIGATION_ITEMS', 'FOOTER_LINKS', 'THEME_SETTINGS', 'API_ENDPOINTS',
    'DEFAULTS', 'FEATURES', 'EXTERNAL_SERVICES',
    'get_config', 'is_production', 'is_cgi_mode', 'get_feature_flag',
    'get_error_message', 'get_success_message'
]