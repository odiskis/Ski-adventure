# api_clients/kartverket_client.py
"""
Kartverket API client for Norwegian place name lookup
"""

import requests
import config

class KartverketClient:
    def __init__(self):
        self.api_url = config.KARTVERKET_STEDSNAVN_API
    
    def search_place(self, place_name, max_results=None):
        """
        Search for a Norwegian place name using Kartverket's API
        
        Args:
            place_name (str): Name of the place to search for
            max_results (int): Maximum number of results to return
            
        Returns:
            dict: Location data with coordinates, or None if not found
        """
        if max_results is None:
            max_results = config.DEFAULT_KARTVERKET_RESULTS
            
        try:
            params = {
                'sok': place_name,
                'treffPerSide': max_results,
                'side': 1
            }
            
            print(f"🔍 Searching for '{place_name}' using Kartverket...")
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('navn'):
                print(f"❌ No results found for '{place_name}'")
                return None
            
            # Get the first (most relevant) result
            place = data['navn'][0]
            
            # Extract coordinates
            if 'representasjonspunkt' in place:
                coords = place['representasjonspunkt']
                lat = coords['nord']
                lon = coords['øst']
                
                result = {
                    'name': place['skrivemåte'],
                    'lat': lat,
                    'lon': lon,
                    'municipality': place.get('kommunenavn', ''),
                    'county': place.get('fylkesnavn', ''),
                    'place_type': place.get('navneobjekttype', ''),
                    'original_search': place_name
                }
                
                print(f"✅ Found: {result['name']} in {result['municipality']}, {result['county']}")
                print(f"📍 Coordinates: {lat:.4f}, {lon:.4f}")
                
                return result
            else:
                print(f"❌ No coordinates found for '{place_name}'")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"🚫 Error searching for location: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"🚫 Error parsing location data: {e}")
            return None
    
    def get_multiple_results(self, place_name, max_results=5):
        """
        Get multiple search results for a place name
        
        Args:
            place_name (str): Name of the place to search for
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of location dictionaries
        """
        try:
            params = {
                'sok': place_name,
                'treffPerSide': max_results,
                'side': 1
            }
            
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('navn'):
                return []
            
            results = []
            for place in data['navn']:
                if 'representasjonspunkt' in place:
                    coords = place['representasjonspunkt']
                    result = {
                        'name': place['skrivemåte'],
                        'lat': coords['nord'],
                        'lon': coords['øst'],
                        'municipality': place.get('kommunenavn', ''),
                        'county': place.get('fylkesnavn', ''),
                        'place_type': place.get('navneobjekttype', ''),
                        'original_search': place_name
                    }
                    results.append(result)
            
            return results
                
        except requests.exceptions.RequestException as e:
            print(f"Error searching for locations: {e}")
            return []
        except (KeyError, IndexError) as e:
            print(f"Error parsing location data: {e}")
            return []