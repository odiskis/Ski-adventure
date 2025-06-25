## Important for web
- All scripts (not .css, .html, .js) needs .cgi file extension to tell server to run as scripts
- All scripts (.cgi on server) must have lF line endings when used with the NTNU Unix server. 
- Pure html seems to work on NTNU server, but 
- - Check all files before going online. 


## Python flask
- Using python flask to implement python program on webpage
- template folder contains html documents with {% command %} for flask rendering (?)

## Server environment
- Server software: Apache/2.4.58 (Ubuntu)
- Current working directory: /web/folk/odinbo/Test
- Python version: 3.12.3 (main, May 26 2025, 18:50:19) [GCC 13.3.0]


## Current project structure
   app.cgi
│   config.py
│   config_web.py
│   Notes.md
│   requirements_web.txt
│   run_app.py
│   test_flask.py
│
├───api_clients
│   │   kartverket_client.py
│   │   senorge_client.py
│   │   varsom_client.py
│   │   yr_weather_client.py
│   │   _init_.py
│   │
│   └───__pycache__
│           kartverket_client.cpython-313.pyc
│           senorge_client.cpython-313.pyc
│           varsom_client.cpython-313.pyc
│           yr_weather_client.cpython-313.pyc
│
├───arkiv
│       base_v1.html
│       main.css
│
├───data
│   │   destinations.json
│   │   enhanced_ski_tours.json
│   │   ski_destinations.json
│   │   terrain_types.json
│   │
│   └───results
│       │   .gitkeep
│       │   recommendations_Trondheim_20250614_2200.json
│       │   ski_touring_Trondheim_20250616_0859.json
│       │
│       └───profiles
├───Ny mappe
├───services
│   │   dynamic_scoring_service.py
│   │   enhanced_snow_depth_service.py
│   │   location_service.py
│   │   recommendation_service.py
│   │   regional_ski_touring_service.py
│   │   ski_touring_service.py
│   │   user_personality_quiz.py
│   │   weather_monitoring_service.py
│   │   weather_service.py
│   │   _init_.py
│   │
│   └───__pycache__
│           dynamic_scoring_service.cpython-313.pyc
│           enhanced_snow_depth_service.cpython-313.pyc
│           location_service.cpython-313.pyc
│           recommendation_service.cpython-313.pyc
│           regional_ski_touring_service.cpython-313.pyc
│           ski_touring_service.cpython-313.pyc
│           user_personality_quiz.cpython-313.pyc
│           weather_monitoring_service.cpython-313.pyc
│           weather_service.cpython-313.pyc
│
├───static
│   ├───css
│   │       darkmode_fix.css
│   │       landing.css
│   │       location.css
│   │       main.css
│   │       quiz.css
│   │       recommendations.css
│   │
│   ├───images
│   │       favicon.svg
│   │
│   └───js
│           landing.js
│           location.js
│           main.js
│           quiz.js
│           recommendations.js
│
├───templates
│       about.html
│       base.html
│       base_v1.html
│       error.html
│       index.html
│       location.html
│       quiz.html
│       quiz_results.html
│       recommendations.html
│
├───utils
│   │   distance_calculator.py
│   │   file_manager.py
│   │   _init_.py
│   │
│   └───__pycache__
│           distance_calculator.cpython-313.pyc
│           file_manager.cpython-313.pyc
│
├───web_services
│   │   form_handlers.py
│   │   web_ski_service.py
│   │   _init_.py
│   │
│   └───__pycache__
│           form_handlers.cpython-313.pyc
│           web_ski_service.cpython-313.pyc
│
└───__pycache__
        config.cpython-313.pyc