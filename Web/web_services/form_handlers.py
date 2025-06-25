# web_services/form_handlers.py
"""
Form handlers for processing quiz answers and user input
"""

import sys 
import os
from typing import Dict, Any, List # Adjust imports as needed

# Add parent directory to path for service imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from services.user_personality_quiz import SkiTouringPersonalityQuiz, UserProfile
from services.location_service import LocationService

class QuizFormHandler:
    """
    Handles quiz form processing and session management
    """
    
    def __init__(self):
        self.quiz_service = SkiTouringPersonalityQuiz()
        self.questions = self.quiz_service.questions
    
    def process_answer(self, session: Dict, question_id: int, answer_index: int) -> Dict:
        """
        Process a quiz answer and update session data
        
        Args:
            session: Flask session dictionary
            question_id: Current question index
            answer_index: Selected answer index
            
        Returns:
            Dict with success status and next action
        """
        
        try:
            if 'quiz_data' not in session:
                return {'success': False, 'error': 'Quiz session not found'}
            
            quiz_data = session['quiz_data']
            
            # Validate question and answer indices
            if question_id >= len(self.questions):
                return {'success': False, 'error': 'Invalid question ID'}
            
            question = self.questions[question_id]
            if answer_index >= len(question.answers):
                return {'success': False, 'error': 'Invalid answer index'}
            
            # Get selected answer
            selected_answer = question.answers[answer_index]
            
            # Store answer
            quiz_data['answers'].append({
                'question_id': question_id,
                'answer_index': answer_index,
                'answer_text': selected_answer.text
            })
            
            # Apply scoring from answer
            self._apply_answer_scoring(quiz_data, selected_answer)
            
            # Update current question
            quiz_data['current_question'] = question_id + 1
            
            # Check if quiz is complete
            quiz_complete = quiz_data['current_question'] >= len(self.questions)
            
            # Update session
            session['quiz_data'] = quiz_data
            
            return {
                'success': True,
                'quiz_complete': quiz_complete,
                'next_question': quiz_data['current_question'] if not quiz_complete else None
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Error processing answer: {str(e)}'}
    
    def _apply_answer_scoring(self, quiz_data: Dict, answer: Any):
        """
        Apply scoring from quiz answer to profile data
        """
        
        profile_scores = quiz_data['profile_scores']
        terrain_votes = quiz_data['terrain_votes']
        risk_votes = quiz_data['risk_votes']
        
        # Apply numeric score changes
        for trait, score_change in answer.scores.items():
            if trait in ['powder_priority', 'view_priority', 'safety_priority', 
                        'adventure_seeking', 'social_preference']:
                current_value = profile_scores[trait]
                new_value = max(0, min(10, current_value + score_change))
                profile_scores[trait] = new_value
                
            elif trait == 'terrain_preference':
                terrain_type = answer.scores[trait]
                terrain_votes[terrain_type] = terrain_votes.get(terrain_type, 0) + 1
                
            elif trait == 'risk_tolerance':
                risk_level = answer.scores[trait]
                risk_votes[risk_level] = risk_votes.get(risk_level, 0) + 1
    
    def create_profile_from_session(self, quiz_data: Dict) -> UserProfile:
        """
        Create UserProfile object from quiz session data
        """
        
        profile_scores = quiz_data['profile_scores']
        terrain_votes = quiz_data['terrain_votes']
        risk_votes = quiz_data['risk_votes']
        
        # Determine terrain preference from votes
        terrain_preference = "balanced"
        if terrain_votes:
            terrain_preference = max(terrain_votes, key=terrain_votes.get)
        
        # Determine risk tolerance from votes
        risk_tolerance = "moderate"
        if risk_votes:
            risk_tolerance = max(risk_votes, key=risk_votes.get)
        
        # Determine experience level from other factors
        experience_level = "intermediate"
        if profile_scores['safety_priority'] >= 8:
            experience_level = "beginner"
        elif profile_scores['adventure_seeking'] >= 8 and profile_scores['safety_priority'] <= 4:
            experience_level = "advanced"
        
        return UserProfile(
            powder_priority=profile_scores['powder_priority'],
            view_priority=profile_scores['view_priority'],
            safety_priority=profile_scores['safety_priority'],
            adventure_seeking=profile_scores['adventure_seeking'],
            social_preference=profile_scores['social_preference'],
            terrain_preference=terrain_preference,
            risk_tolerance=risk_tolerance,
            experience_level=experience_level
        )
    
    def get_quiz_progress(self, session: Dict) -> Dict:
        """
        Get current quiz progress information
        """
        
        if 'quiz_data' not in session:
            return {'progress': 0, 'current_question': 0, 'total_questions': len(self.questions)}
        
        quiz_data = session['quiz_data']
        current = quiz_data.get('current_question', 0)
        total = len(self.questions)
        progress = int((current / total) * 100) if total > 0 else 0
        
        return {
            'progress': progress,
            'current_question': current,
            'total_questions': total,
            'answers_count': len(quiz_data.get('answers', []))
        }


class LocationFormHandler:
    """
    Handles location input processing and validation
    """
    
    def __init__(self):
        self.location_service = LocationService()
    
    def process_location(self, location_input: str) -> Dict:
        """
        Process and validate location input
        
        Args:
            location_input: User's location input string
            
        Returns:
            Dict with success status and location data
        """
        
        try:
            if not location_input or not location_input.strip():
                return {'success': False, 'error': 'Please enter a location'}
            
            # Clean input
            location_input = location_input.strip()
            
            # Get location coordinates
            location_result = self.location_service.get_location_coordinates(location_input)
            
            if location_result:
                # Validate coordinates are in Norway
                if self.location_service.validate_coordinates(
                    location_result['lat'], location_result['lon']
                ):
                    return {
                        'success': True,
                        'location': location_result,
                        'display_name': self._create_display_name(location_result)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Location appears to be outside Norway. Please enter a Norwegian location.'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Location not found. Please try a different location name or check spelling.'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Error processing location: {str(e)}'}
    
    def get_location_suggestions(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Get location suggestions for autocomplete
        """
        try:
            if not query or len(query) < 2:
                return []
            
            locations = self.location_service.search_multiple_locations(query, max_results)
            
            suggestions = []
            for location in locations:
                suggestion = {
                    'value': location['name'],
                    'display': self._create_display_name(location),
                    'lat': location['lat'],
                    'lon': location['lon']
                }
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            return []
    
    def _create_display_name(self, location: Dict) -> str:
        """
        Create a nice display name for a location
        """
        name = location['name']
        municipality = location.get('municipality', '')
        county = location.get('county', '')
        
        if municipality and county:
            return f"{name}, {municipality} ({county})"
        elif municipality:
            return f"{name}, {municipality}"
        elif county:
            return f"{name} ({county})"
        else:
            return name
    
    def validate_driving_hours(self, hours_input: Any) -> Dict:
        """
        Validate driving hours input
        """
        try:
            hours = int(hours_input)
            
            if hours not in [1, 2, 3, 4, 5, 6]:
                # Round to nearest valid option
                valid_options = [1, 2, 3, 4, 5, 6]
                hours = min(valid_options, key=lambda x: abs(x - hours))
            
            return {
                'success': True,
                'hours': hours,
                'adjusted': hours != int(hours_input) if str(hours_input).isdigit() else False
            }
            
        except (ValueError, TypeError):
            return {
                'success': False,
                'error': 'Invalid driving hours. Please enter a number between 1 and 6.',
                'default': 3
            }


class PreferencesFormHandler:
    """
    Handles user preference updates and adjustments
    """
    
    def __init__(self):
        pass
    
    def update_profile_preferences(self, user_profile: UserProfile, updates: Dict) -> Dict:
        """
        Update user profile with new preference values
        """
        try:
            updated_profile = UserProfile(
                powder_priority=updates.get('powder_priority', user_profile.powder_priority),
                view_priority=updates.get('view_priority', user_profile.view_priority),
                safety_priority=updates.get('safety_priority', user_profile.safety_priority),
                adventure_seeking=updates.get('adventure_seeking', user_profile.adventure_seeking),
                social_preference=updates.get('social_preference', user_profile.social_preference),
                terrain_preference=updates.get('terrain_preference', user_profile.terrain_preference),
                risk_tolerance=updates.get('risk_tolerance', user_profile.risk_tolerance),
                experience_level=updates.get('experience_level', user_profile.experience_level)
            )
            
            return {'success': True, 'profile': updated_profile}
            
        except Exception as e:
            return {'success': False, 'error': f'Error updating preferences: {str(e)}'}
    
    def validate_preference_values(self, preferences: Dict) -> Dict:
        """
        Validate preference values are within acceptable ranges
        """
        errors = []
        validated = {}
        
        # Validate numeric preferences (0-10 scale)
        numeric_prefs = ['powder_priority', 'view_priority', 'safety_priority', 
                        'adventure_seeking', 'social_preference']
        
        for pref in numeric_prefs:
            if pref in preferences:
                try:
                    value = int(preferences[pref])
                    if 0 <= value <= 10:
                        validated[pref] = value
                    else:
                        errors.append(f'{pref} must be between 0 and 10')
                except (ValueError, TypeError):
                    errors.append(f'{pref} must be a number')
        
        # Validate categorical preferences
        valid_terrain = ['coastal_alpine', 'high_alpine', 'forest_valley', 'plateau_ridge', 'fjord_valley', 'balanced']
        valid_risk = ['conservative', 'moderate', 'aggressive']
        valid_experience = ['beginner', 'intermediate', 'advanced']
        
        if 'terrain_preference' in preferences:
            if preferences['terrain_preference'] in valid_terrain:
                validated['terrain_preference'] = preferences['terrain_preference']
            else:
                errors.append('Invalid terrain preference')
        
        if 'risk_tolerance' in preferences:
            if preferences['risk_tolerance'] in valid_risk:
                validated['risk_tolerance'] = preferences['risk_tolerance']
            else:
                errors.append('Invalid risk tolerance')
        
        if 'experience_level' in preferences:
            if preferences['experience_level'] in valid_experience:
                validated['experience_level'] = preferences['experience_level']
            else:
                errors.append('Invalid experience level')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'validated_values': validated
        }