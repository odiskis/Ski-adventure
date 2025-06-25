# services/location_service.py
"""
High-level location services
"""

from api_clients.kartverket_client import KartverketClient

class LocationService:
    def __init__(self):
        self.kartverket_client = KartverketClient()
    
    def get_location_coordinates(self, location_input):
        """
        Get coordinates for a location input (string or dict)
        
        Args:
            location_input: Either a place name string or dict with coordinates
            
        Returns:
            dict: Location data with coordinates, or None if failed
        """
        if isinstance(location_input, str):
            # String input - look up using Kartverket
            return self.kartverket_client.search_place(location_input)
        elif isinstance(location_input, dict):
            # Dict input - validate it has required fields
            if 'lat' in location_input and 'lon' in location_input:
                # Ensure name field exists
                if 'name' not in location_input:
                    location_input['name'] = f"Custom Location ({location_input['lat']:.4f}, {location_input['lon']:.4f})"
                return location_input
            else:
                print("❌ Dict input missing 'lat' or 'lon' fields")
                return None
        else:
            print("❌ Invalid location input type. Use string or dict.")
            return None
    
    def search_multiple_locations(self, place_name, max_results=5):
        """
        Search for multiple possible locations
        
        Args:
            place_name (str): Place name to search for
            max_results (int): Maximum number of results
            
        Returns:
            list: List of location dictionaries
        """
        return self.kartverket_client.get_multiple_results(place_name, max_results)
    
    def validate_coordinates(self, lat, lon):
        """
        Validate that coordinates are within Norway's bounds (approximately)
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            bool: True if coordinates seem to be in Norway
        """
        # Rough bounds for Norway (including Svalbard)
        # Latitude: approximately 58°N to 81°N
        # Longitude: approximately 4°E to 32°E
        if not (58 <= lat <= 81):
            return False
        if not (4 <= lon <= 32):
            return False
        return True