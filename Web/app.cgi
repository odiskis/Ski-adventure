#!/usr/bin/env python3

import sys
import os
import json
from io import StringIO
from datetime import datetime

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, '..'))  # For accessing parent directory services

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, session
    import config
    from services.location_service import LocationService
    from services.user_personality_quiz import SkiTouringPersonalityQuiz, UserProfile
    from services.regional_ski_touring_service import RegionalSkiTouringService
    from web_services.web_ski_service import WebSkiService
    from web_services.form_handlers import QuizFormHandler, LocationFormHandler
    
    # Create Flask application
    app = Flask(__name__)
    app.secret_key = 'your-secret-key-change-this-in-production'
    
    # Initialize services
    location_service = LocationService()
    quiz_service = SkiTouringPersonalityQuiz()
    regional_service = RegionalSkiTouringService()
    web_ski_service = WebSkiService()
    quiz_handler = QuizFormHandler()
    location_handler = LocationFormHandler()
    
    @app.route('/')
    def index():
        """Landing page"""
        return render_template('index.html')
    
    @app.route('/quiz')
    def quiz():
        """Start personality quiz"""
        # Initialize quiz session
        session['quiz_data'] = {
            'current_question': 0,
            'answers': [],
            'profile_scores': {
                'powder_priority': 5,
                'view_priority': 5,
                'safety_priority': 5,
                'adventure_seeking': 5,
                'social_preference': 5
            },
            'terrain_votes': {},
            'risk_votes': {}
        }
        return redirect(url_for('quiz_question', question_id=0))
    
    @app.route('/quiz/<int:question_id>')
    def quiz_question(question_id):
        """Display specific quiz question"""
        questions = quiz_service.questions
        
        if question_id >= len(questions):
            return redirect(url_for('quiz_results'))
        
        question = questions[question_id]
        progress = int((question_id / len(questions)) * 100)
        
        return render_template('quiz.html', 
                             question=question,
                             question_id=question_id,
                             progress=progress,
                             total_questions=len(questions))
    
    @app.route('/quiz/answer', methods=['POST'])
    def quiz_answer():
        """Process quiz answer"""
        data = request.get_json()
        question_id = data.get('question_id')
        answer_index = data.get('answer_index')
        
        # Process answer using quiz handler
        result = quiz_handler.process_answer(session, question_id, answer_index)
        
        if result['success']:
            if result['quiz_complete']:
                return jsonify({'success': True, 'redirect': url_for('quiz_results')})
            else:
                next_question = result['next_question']
                return jsonify({'success': True, 'redirect': url_for('quiz_question', question_id=next_question)})
        else:
            return jsonify({'success': False, 'error': result['error']})
    
    @app.route('/quiz/results')
    def quiz_results():
        """Show quiz results and collect location"""
        if 'quiz_data' not in session:
            return redirect(url_for('quiz'))
        
        # Create user profile from quiz data
        profile_data = session['quiz_data']
        user_profile = quiz_handler.create_profile_from_session(profile_data)
        
        # Store profile in session for next step
        session['user_profile'] = user_profile.to_dict()
        
        return render_template('quiz_results.html', 
                             profile=user_profile,
                             profile_summary=quiz_service.get_profile_summary(user_profile))
    
    @app.route('/location', methods=['GET', 'POST'])
    def location():
        """Get user location and driving preferences"""
        if request.method == 'POST':
            data = request.get_json()
            location_input = data.get('location')
            max_hours = data.get('max_hours', 3)
            
            # Process location
            location_result = location_handler.process_location(location_input)
            
            if location_result['success']:
                session['start_location'] = location_result['location']
                session['max_hours'] = max_hours
                return jsonify({'success': True, 'redirect': url_for('recommendations')})
            else:
                return jsonify({'success': False, 'error': location_result['error']})
        
        return render_template('location.html')
    
    @app.route('/recommendations')
    def recommendations():
        """Show personalized ski touring recommendations"""
        # Check if we have all required session data
        if 'user_profile' not in session or 'start_location' not in session:
            return redirect(url_for('quiz'))
        
        try:
            # Get data from session
            user_profile_dict = session['user_profile']
            user_profile = UserProfile(**user_profile_dict)
            start_location = session['start_location']
            max_hours = session.get('max_hours', 3)
            
            # Get recommendations using web service
            recommendations_data = web_ski_service.get_web_recommendations(
                start_location, max_hours, user_profile
            )
            
            if 'error' in recommendations_data:
                error_message = recommendations_data['error']
                return render_template('error.html', error=error_message)
            
            return render_template('recommendations.html', 
                                 recommendations=recommendations_data,
                                 user_profile=user_profile,
                                 search_info=recommendations_data.get('search_info', {}))
        
        except Exception as e:
            error_message = f"An error occurred while generating recommendations: {str(e)}"
            return render_template('error.html', error=error_message)
    
    @app.route('/api/recommendations/refresh', methods=['POST'])
    def refresh_recommendations():
        """Refresh recommendations with new parameters"""
        try:
            data = request.get_json()
            max_hours = data.get('max_hours', 3)
            
            # Update session
            session['max_hours'] = max_hours
            
            return jsonify({'success': True, 'redirect': url_for('recommendations')})
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')
    
    @app.route('/api/health')
    def health_check():
        """API health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'location_service': 'available',
                'quiz_service': 'available',
                'regional_service': 'available'
            }
        })
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error="Internal server error"), 500
    
    # CGI execution
    if __name__ == '__main__':
        # CGI mode - capture output
        from wsgiref.handlers import CGIHandler
        CGIHandler().run(app)

except Exception as e:
    # Emergency fallback for any import or initialization errors
    print("Content-Type: text/html\n")
    print(f"""
    <html>
    <head><title>Ski Touring App - Error</title></head>
    <body>
        <h1>🎿 Ski Touring Application Error</h1>
        <p>Sorry, there was an error starting the application:</p>
        <pre>{str(e)}</pre>
        <p>Please try again later or contact support.</p>
    </body>
    </html>
    """)