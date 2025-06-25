#!/usr/bin/env python3
"""
Test script to run the Flask app in development mode
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

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
    
    @app.route('/test')
    def test():
        """Simple test page"""
        return """
        <h1>🎿 Ski Touring App Test</h1>
        <p>Flask is working!</p>
        <p>Services initialized successfully!</p>
        <a href="/">Go to main page</a>
        """
    #placeholder for the quiz page in test environment
    @app.route('/quiz')
    def quiz():
        return "<h1>Quiz page coming soon!</h1><a href='/'>Back to home</a>"
    
    
    if __name__ == '__main__':
        print("🎿 Starting Ski Touring Flask App in development mode...")
        print("📡 Visit: http://localhost:5000")
        print("🧪 Test page: http://localhost:5000/test")
        app.run(debug=True, host='127.0.0.1', port=5000)

except Exception as e:
    print(f"❌ Error starting Flask app: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()