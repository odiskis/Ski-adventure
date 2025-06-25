# utils/distance_calculator.py
"""
Geographic distance calculation utilities
"""

import math
import config

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points using Haversine formula
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        float: Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def calculate_driving_time(distance_km, speed_kmh=None):
    """
    Calculate estimated driving time
    
    Args:
        distance_km (float): Distance in kilometers
        speed_kmh (float): Average speed in km/h (uses config default if None)
        
    Returns:
        float: Driving time in hours
    """
    if speed_kmh is None:
        speed_kmh = config.AVERAGE_DRIVING_SPEED
    
    return distance_km / speed_kmh

def get_max_distance_for_hours(hours):
    """
    Get maximum driving distance for given hours
    
    Args:
        hours (int): Number of driving hours
        
    Returns:
        int: Maximum distance in kilometers
    """
    return config.DRIVING_DISTANCES.get(hours, hours * config.AVERAGE_DRIVING_SPEED)

def is_within_driving_range(distance_km, max_hours):
    """
    Check if distance is within driving range
    
    Args:
        distance_km (float): Distance in kilometers
        max_hours (int): Maximum driving hours
        
    Returns:
        bool: True if within range
    """
    max_distance = get_max_distance_for_hours(max_hours)
    return distance_km <= max_distance