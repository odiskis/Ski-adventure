# services/user_personality_quiz.py
"""
Interactive personality quiz to determine user preferences for ski touring
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class QuizAnswer:
    """Represents a single quiz answer choice"""
    text: str
    scores: Dict[str, int]  # Scoring weights for different personality traits

@dataclass 
class QuizQuestion:
    """Represents a single quiz question with multiple choice answers"""
    id: str
    question: str
    description: str
    answers: List[QuizAnswer]

@dataclass
class UserProfile:
    """User personality profile for ski touring preferences"""
    powder_priority: int = 5      # 0-10 scale (how much they prioritize fresh snow)
    view_priority: int = 5        # 0-10 scale (how much they prioritize scenic views)
    safety_priority: int = 5      # 0-10 scale (how safety-conscious they are)
    adventure_seeking: int = 5    # 0-10 scale (how much they seek adventure/challenge)
    social_preference: int = 5    # 0-10 scale (solo vs social skiing preference)
    
    terrain_preference: str = "balanced"      # coastal_alpine, high_alpine, forest_valley, etc.
    risk_tolerance: str = "moderate"          # conservative, moderate, aggressive
    experience_level: str = "intermediate"    # beginner, intermediate, advanced
    
    def to_dict(self):
        """Convert profile to dictionary for easier handling"""
        return {
            'powder_priority': self.powder_priority,
            'view_priority': self.view_priority,
            'safety_priority': self.safety_priority,
            'adventure_seeking': self.adventure_seeking,
            'social_preference': self.social_preference,
            'terrain_preference': self.terrain_preference,
            'risk_tolerance': self.risk_tolerance,
            'experience_level': self.experience_level
        }

class SkiTouringPersonalityQuiz:
    def __init__(self):
        self.questions = self._create_quiz_questions()
    
    def _create_quiz_questions(self) -> List[QuizQuestion]:
        """Create the ski touring personality quiz questions"""
        
        questions = [
            QuizQuestion(
                id="weather_vs_snow",
                question="🌤️ vs ❄️ The Perfect Ski Day",
                description="You have one perfect ski day. Which would you choose?",
                answers=[
                    QuizAnswer(
                        "☀️ Bluebird sunny day with incredible views, but older, firmer snow",
                        {"view_priority": +3, "powder_priority": -1, "adventure_seeking": +1}
                    ),
                    QuizAnswer(
                        "❄️ Fresh 30cm powder, but cloudy with limited visibility", 
                        {"powder_priority": +3, "view_priority": -1, "adventure_seeking": +2}
                    ),
                    QuizAnswer(
                        "🌤️ Partly cloudy with decent snow and good visibility",
                        {"view_priority": +1, "powder_priority": +1, "safety_priority": +1}
                    )
                ]
            ),
            
            QuizQuestion(
                id="terrain_preference",
                question="⛰️ Your Dream Ski Descent",
                description="Which type of ski descent excites you most?",
                answers=[
                    QuizAnswer(
                        "🌊 Steep couloir dropping straight into a dramatic fjord",
                        {"adventure_seeking": +3, "view_priority": +2, "terrain_preference": "coastal_alpine"}
                    ),
                    QuizAnswer(
                        "🏔️ Technical glacier skiing among massive peaks",
                        {"adventure_seeking": +3, "powder_priority": +1, "terrain_preference": "high_alpine"}
                    ),
                    QuizAnswer(
                        "🌲 Flowing powder turns through peaceful birch forests",
                        {"powder_priority": +2, "safety_priority": +2, "terrain_preference": "forest_valley"}
                    ),
                    QuizAnswer(
                        "🌬️ Wide open bowl with endless views across plateaus",
                        {"view_priority": +2, "adventure_seeking": +1, "terrain_preference": "plateau_ridge"}
                    )
                ]
            ),
            
            QuizQuestion(
                id="risk_vs_reward", 
                question="⚠️ Risk vs. Reward",
                description="When avalanche conditions are 'Considerable' (Level 3):",
                answers=[
                    QuizAnswer(
                        "🔒 I'd stick to low-angle, safe terrain below 30 degrees",
                        {"safety_priority": +3, "risk_tolerance": "conservative"}
                    ),
                    QuizAnswer(
                        "⚖️ I'd carefully assess specific slopes and make conservative choices",
                        {"safety_priority": +2, "adventure_seeking": +1, "risk_tolerance": "moderate"}
                    ),
                    QuizAnswer(
                        "🎯 I'd accept the risk for good skiing if I could read the terrain well",
                        {"adventure_seeking": +2, "safety_priority": -1, "risk_tolerance": "aggressive"}
                    )
                ]
            ),
            
            QuizQuestion(
                id="objective_priority",
                question="🎯 Summit vs. Skiing",
                description="Your main objective on a ski tour:",
                answers=[
                    QuizAnswer(
                        "🏔️ Reach the summit and enjoy the panoramic views",
                        {"view_priority": +3, "adventure_seeking": +1}
                    ),
                    QuizAnswer(
                        "🎿 Find the best snow conditions and optimal ski terrain",
                        {"powder_priority": +3, "adventure_seeking": +2}
                    ),
                    QuizAnswer(
                        "📸 Experience the beauty of the mountains and capture great photos",
                        {"view_priority": +2, "social_preference": +1}
                    ),
                    QuizAnswer(
                        "🏃 Challenge myself physically and push my limits",
                        {"adventure_seeking": +3, "safety_priority": -1}
                    )
                ]
            ),
            
            QuizQuestion(
                id="social_vs_solitude",
                question="👥 Social vs. Solo",
                description="Your ideal ski touring experience:",
                answers=[
                    QuizAnswer(
                        "🏔️ Remote wilderness where I might not see another soul",
                        {"adventure_seeking": +2, "social_preference": -2}
                    ),
                    QuizAnswer(
                        "👥 Popular areas with other tourers and established tracks", 
                        {"safety_priority": +2, "social_preference": +2}
                    ),
                    QuizAnswer(
                        "👨‍👩‍👧‍👦 Accessible areas where I can bring less experienced friends",
                        {"safety_priority": +3, "social_preference": +3, "terrain_preference": "forest_valley"}
                    )
                ]
            ),
            
            QuizQuestion(
                id="conditions_adaptation",
                question="🌪️ When Weather Changes",
                description="Your approach when conditions deteriorate during a tour:",
                answers=[
                    QuizAnswer(
                        "🔄 Adapt the plan and find alternative, safer objectives",
                        {"safety_priority": +3, "adventure_seeking": +1}
                    ),
                    QuizAnswer(
                        "🏠 Head back early - better safe than sorry",
                        {"safety_priority": +3, "risk_tolerance": "conservative"}
                    ),
                    QuizAnswer(
                        "⚡ Push forward if I have the skills - it's part of the adventure",
                        {"adventure_seeking": +3, "safety_priority": -1, "risk_tolerance": "aggressive"}
                    )
                ]
            ),
            
            QuizQuestion(
                id="access_vs_remoteness",
                question="🚗 vs 🥾 Access vs. Adventure",
                description="You prefer ski tours that are:",
                answers=[
                    QuizAnswer(
                        "🚗 Easy to access by car - more time skiing, less time traveling",
                        {"safety_priority": +1, "social_preference": +1}
                    ),
                    QuizAnswer(
                        "🥾 Require effort to reach - the journey is part of the experience",
                        {"adventure_seeking": +2, "social_preference": -1}
                    ),
                    QuizAnswer(
                        "🚁 Accessible by boat/helicopter - unique and exclusive experiences",
                        {"adventure_seeking": +1, "view_priority": +2}
                    )
                ]
            )
        ]
        
        return questions
    
    def conduct_quiz(self) -> UserProfile:
        """
        Run the interactive quiz and return user profile
        For web app, this would be handled by frontend
        """
        print("🎿 === SKI TOURING PERSONALITY QUIZ === 🎿")
        print("Help us understand your skiing preferences to find your perfect conditions!")
        print()
        
        # Initialize profile with neutral values
        profile = UserProfile()
        terrain_votes = {}
        risk_votes = {}
        
        for question in self.questions:
            print(f"❓ {question.question}")
            print(f"   {question.description}")
            print()
            
            # Display answer options
            for i, answer in enumerate(question.answers, 1):
                print(f"   {i}. {answer.text}")
            print()
            
            # Get user choice
            while True:
                try:
                    choice = int(input("Your choice (enter number): "))
                    if 1 <= choice <= len(question.answers):
                        selected_answer = question.answers[choice - 1]
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(question.answers)}")
                except ValueError:
                    print("Please enter a valid number")
            
            # Apply scoring from selected answer
            self._apply_answer_scores(profile, selected_answer, terrain_votes, risk_votes)
            print()
        
        # Finalize profile based on votes
        self._finalize_profile(profile, terrain_votes, risk_votes)
        
        return profile
    
    def _apply_answer_scores(self, profile: UserProfile, answer: QuizAnswer, 
                           terrain_votes: dict, risk_votes: dict):
        """Apply scoring from a quiz answer to the user profile"""
        
        for trait, score_change in answer.scores.items():
            if trait in ['powder_priority', 'view_priority', 'safety_priority', 
                        'adventure_seeking', 'social_preference']:
                current_value = getattr(profile, trait)
                new_value = max(0, min(10, current_value + score_change))
                setattr(profile, trait, new_value)
                
            elif trait == 'terrain_preference':
                terrain_type = answer.scores[trait]
                terrain_votes[terrain_type] = terrain_votes.get(terrain_type, 0) + 1
                
            elif trait == 'risk_tolerance':
                risk_level = answer.scores[trait]
                risk_votes[risk_level] = risk_votes.get(risk_level, 0) + 1
    
    def _finalize_profile(self, profile: UserProfile, terrain_votes: dict, risk_votes: dict):
        """Finalize profile based on accumulated votes and scores"""
        
        # Determine terrain preference from votes
        if terrain_votes:
            profile.terrain_preference = max(terrain_votes, key=terrain_votes.get)
        
        # Determine risk tolerance from votes  
        if risk_votes:
            profile.risk_tolerance = max(risk_votes, key=risk_votes.get)
        
        # Determine experience level from other factors
        if profile.safety_priority >= 8:
            profile.experience_level = "beginner"
        elif profile.adventure_seeking >= 8 and profile.safety_priority <= 4:
            profile.experience_level = "advanced"
        else:
            profile.experience_level = "intermediate"
    
    def get_profile_summary(self, profile: UserProfile) -> str:
        """Generate a human-readable summary of the user profile"""
        
        # Determine primary personality type
        if profile.powder_priority >= 7:
            if profile.adventure_seeking >= 7:
                personality_type = "Hardcore Powder Hunter"
            else:
                personality_type = "Snow Quality Enthusiast"
        elif profile.view_priority >= 7:
            if profile.adventure_seeking >= 7:
                personality_type = "Adventure Photographer"
            else:
                personality_type = "Scenic Tourer"
        elif profile.safety_priority >= 8:
            personality_type = "Safety-First Tourer"
        elif profile.adventure_seeking >= 8:
            personality_type = "Extreme Adventurer"
        else:
            personality_type = "Balanced Ski Tourer"
        
        # Terrain description
        terrain_descriptions = {
            "coastal_alpine": "dramatic summit-to-sea adventures",
            "high_alpine": "challenging high-altitude glacier terrain", 
            "forest_valley": "peaceful forest and valley skiing",
            "plateau_ridge": "wide-open plateau exploration",
            "fjord_valley": "scenic fjord valley touring"
        }
        
        terrain_desc = terrain_descriptions.get(profile.terrain_preference, "varied terrain")
        
        summary = f"""
🎿 Your Ski Touring Personality: {personality_type}

You're drawn to {terrain_desc} and prefer {profile.risk_tolerance} approaches to mountain risk. 
Your skiing priorities lean toward {"fresh powder" if profile.powder_priority >= 6 else "scenic views" if profile.view_priority >= 6 else "balanced conditions"}.

Experience Level: {profile.experience_level.title()}
Risk Tolerance: {profile.risk_tolerance.title()}
Terrain Preference: {profile.terrain_preference.replace('_', ' ').title()}
        """
        
        return summary.strip()
    
    def calculate_scoring_weights(self, profile: UserProfile) -> Dict[str, float]:
        """
        Calculate personalized scoring weights based on user profile
        
        Returns:
            dict: Scoring weights for different criteria
        """
        # Base weights
        weights = {
            'snow': 0.35,
            'weather': 0.25,
            'avalanche': 0.25,
            'view_terrain': 0.10,
            'distance': 0.05
        }
        
        # Adjust based on powder priority
        if profile.powder_priority >= 7:
            weights['snow'] += 0.15
            weights['weather'] -= 0.10
            weights['view_terrain'] -= 0.05
        elif profile.powder_priority <= 3:
            weights['snow'] -= 0.10
            weights['weather'] += 0.05
            weights['view_terrain'] += 0.05
        
        # Adjust based on view priority
        if profile.view_priority >= 7:
            weights['weather'] += 0.15
            weights['view_terrain'] += 0.10
            weights['snow'] -= 0.15
        elif profile.view_priority <= 3:
            weights['view_terrain'] -= 0.05
            weights['snow'] += 0.05
        
        # Adjust based on safety priority
        if profile.safety_priority >= 8:
            weights['avalanche'] += 0.15
            weights['snow'] -= 0.05
            weights['weather'] -= 0.05
            weights['distance'] -= 0.05
        elif profile.safety_priority <= 3:
            weights['avalanche'] -= 0.10
            weights['snow'] += 0.05
            weights['weather'] += 0.05
        
        # Ensure weights sum to 1.0
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        return weights