# utils/file_manager.py
"""
Enhanced file management utilities for ski touring planner
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import config

def load_destinations():
    """
    Load ski touring destinations from JSON file
    
    Returns:
        list: List of destination dictionaries
    """
    return load_json_file(config.DESTINATIONS_FILE)

def load_json_file(filepath: str) -> List[Dict] | Dict:
    """
    Load any JSON file with error handling
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded JSON data or empty list/dict
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📁 Loaded {filepath}")
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return [] if filepath.endswith('destinations.json') else {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON file {filepath}: {e}")
        return [] if filepath.endswith('destinations.json') else {}

def save_recommendations(recommendations: Dict, search_info: Dict, filename: Optional[str] = None) -> Optional[str]:
    """
    Save ski touring recommendations to JSON file
    
    Args:
        recommendations: Full recommendations data
        search_info: Search parameters and metadata
        filename: Optional custom filename
        
    Returns:
        str: Path to saved file, or None if failed
    """
    # Create results directory if it doesn't exist
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        starting_location = search_info.get('starting_location', {})
        if isinstance(starting_location, dict):
            location_name = starting_location.get('name', 'unknown')
        else:
            location_name = str(starting_location)
        
        # Clean filename of special characters
        clean_location = "".join(c for c in location_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"ski_touring_{clean_location}_{timestamp}.json"
    
    filepath = os.path.join(config.RESULTS_DIR, filename)
    
    try:
        # Ensure the data is JSON serializable
        serializable_data = _make_json_serializable(recommendations)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return None

def _make_json_serializable(data: Any) -> Any:
    """
    Recursively convert data to JSON-serializable format
    
    Args:
        data: Data that might contain non-serializable objects
        
    Returns:
        JSON-serializable version of the data
    """
    if isinstance(data, dict):
        return {key: _make_json_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_make_json_serializable(item) for item in data]
    elif isinstance(data, tuple):
        return [_make_json_serializable(item) for item in data]
    elif hasattr(data, '__dict__'):
        # Convert objects with __dict__ to dictionaries
        return _make_json_serializable(data.__dict__)
    elif hasattr(data, 'to_dict'):
        # Use to_dict method if available
        return _make_json_serializable(data.to_dict())
    else:
        # For basic types (str, int, float, bool, None)
        return data

def load_recommendations(filepath: str) -> Optional[Dict]:
    """
    Load ski touring recommendations from JSON file
    
    Args:
        filepath: Path to recommendations file
        
    Returns:
        dict: Loaded recommendations data, or None if failed
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing file {filepath}: {e}")
        return None

def list_recommendation_files() -> List[str]:
    """
    List all ski touring recommendation files in the results directory
    
    Returns:
        list: List of filenames, sorted by date (most recent first)
    """
    try:
        if not os.path.exists(config.RESULTS_DIR):
            return []
        
        files = [f for f in os.listdir(config.RESULTS_DIR) 
                if f.endswith('.json') and (f.startswith('ski_touring_') or f.startswith('recommendations_'))]
        return sorted(files, reverse=True)  # Most recent first
        
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def save_user_profile(user_profile: Dict, profile_name: Optional[str] = None) -> Optional[str]:
    """
    Save user personality profile for future use
    
    Args:
        user_profile: User profile dictionary
        profile_name: Optional name for the profile
        
    Returns:
        str: Path to saved profile, or None if failed
    """
    profiles_dir = os.path.join(config.RESULTS_DIR, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    
    if profile_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        profile_name = f"profile_{timestamp}"
    
    # Clean profile name
    clean_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{clean_name}.json"
    filepath = os.path.join(profiles_dir, filename)
    
    try:
        profile_data = {
            'profile': user_profile,
            'created_at': datetime.now().isoformat(),
            'profile_name': profile_name
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"👤 Profile saved to: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        return None

def load_user_profile(profile_name: str) -> Optional[Dict]:
    """
    Load a saved user profile
    
    Args:
        profile_name: Name of the profile file (with or without .json)
        
    Returns:
        dict: User profile data, or None if failed
    """
    profiles_dir = os.path.join(config.RESULTS_DIR, "profiles")
    
    if not profile_name.endswith('.json'):
        profile_name += '.json'
    
    filepath = os.path.join(profiles_dir, profile_name)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('profile', {})
        
    except FileNotFoundError:
        print(f"❌ Profile not found: {profile_name}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing profile {profile_name}: {e}")
        return None

def list_user_profiles() -> List[str]:
    """
    List all saved user profiles
    
    Returns:
        list: List of profile filenames
    """
    profiles_dir = os.path.join(config.RESULTS_DIR, "profiles")
    
    try:
        if not os.path.exists(profiles_dir):
            return []
        
        files = [f for f in os.listdir(profiles_dir) if f.endswith('.json')]
        return sorted(files)
        
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")
        return []

def create_directory_structure():
    """
    Create the full directory structure for the ski touring planner
    """
    directories = [
        config.RESULTS_DIR,
        os.path.join(config.RESULTS_DIR, "profiles"),
        "data",
        "logs",
        "cache"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        except Exception as e:
            print(f"❌ Error creating directory {directory}: {e}")

def ensure_data_files_exist():
    """
    Ensure all required data files exist, create defaults if missing
    """
    # Check if ski destinations file exists
    if not os.path.exists(config.DESTINATIONS_FILE):
        print(f"⚠️ Creating default destinations file: {config.DESTINATIONS_FILE}")
        create_default_destinations_file()
    
    # Check if terrain types file exists  
    if not os.path.exists(config.TERRAIN_TYPES_FILE):
        print(f"⚠️ Creating default terrain types file: {config.TERRAIN_TYPES_FILE}")
        create_default_terrain_types_file()

def create_default_destinations_file():
    """Create a minimal default destinations file if none exists"""
    default_destinations = [
        {
            "name": "Lyngen Alps - Test Location",
            "lat": 69.8567,
            "lon": 20.3833,
            "type": "ski_touring",
            "terrain_type": "coastal_alpine",
            "elevation_range": [0, 1800],
            "difficulty": "intermediate",
            "access": "road_access",
            "season": "February-May",
            "description": "Test destination for development",
            "features": ["test_location"],
            "view_score": 80,
            "technical_level": 6,
            "accessibility": 7,
            "avalanche_exposure": "moderate"
        }
    ]
    
    try:
        os.makedirs(os.path.dirname(config.DESTINATIONS_FILE), exist_ok=True)
        with open(config.DESTINATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_destinations, f, indent=2, ensure_ascii=False)
        print(f"✅ Created default destinations file")
    except Exception as e:
        print(f"❌ Error creating default destinations: {e}")

def create_default_terrain_types_file():
    """Create a minimal default terrain types file if none exists"""
    default_terrain_types = {
        "terrain_types": {
            "coastal_alpine": {
                "name": "Coastal Alpine",
                "view_score_multiplier": 1.2,
                "difficulty_modifier": 0.8
            },
            "high_alpine": {
                "name": "High Alpine", 
                "view_score_multiplier": 1.1,
                "difficulty_modifier": 1.2
            }
        }
    }
    
    try:
        os.makedirs(os.path.dirname(config.TERRAIN_TYPES_FILE), exist_ok=True)
        with open(config.TERRAIN_TYPES_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_terrain_types, f, indent=2, ensure_ascii=False)
        print(f"✅ Created default terrain types file")
    except Exception as e:
        print(f"❌ Error creating default terrain types: {e}")

def get_file_stats(filepath: str) -> Optional[Dict]:
    """
    Get file statistics and metadata
    
    Args:
        filepath: Path to file
        
    Returns:
        dict: File statistics or None if error
    """
    try:
        stat = os.stat(filepath)
        return {
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'exists': True
        }
    except Exception as e:
        return {'exists': False, 'error': str(e)}