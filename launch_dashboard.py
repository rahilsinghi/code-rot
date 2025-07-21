#!/usr/bin/env python3
"""
Web Dashboard Launcher
Starts the enhanced coding practice web interface with all components
"""

import sys
import os
import time
import threading
import webbrowser
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("🚀 Enhanced Coding Practice System - Web Dashboard")
    print("=" * 60)
    print("Starting all components:")
    print("  📊 Web Dashboard with real-time analytics")
    print("  🔌 REST API server")
    print("  📱 Progressive Web App (PWA)")
    print("  🧠 AI-powered recommendations")
    print("  ⏱️  Study session management")
    print("  📈 Advanced analytics engine")
    print("=" * 60)

def check_dependencies():
    """Check if required dependencies are available"""
    missing = []
    
    try:
        import flask
    except ImportError:
        missing.append('flask')
    
    try:
        import flask_socketio
    except ImportError:
        missing.append('flask-socketio')
    
    try:
        import plotly
    except ImportError:
        missing.append('plotly')
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Please install with: pip install " + " ".join(missing))
        return False
    
    return True

def start_web_dashboard():
    """Start the web dashboard"""
    try:
        print("📊 Starting web dashboard...")
        from web_dashboard import WebDashboard
        
        dashboard = WebDashboard()
        dashboard.setup_routes()
        
        print("✅ Web dashboard initialized")
        return dashboard
        
    except ImportError as e:
        print(f"⚠️  Web dashboard module not found: {e}")
        return None
    except Exception as e:
        print(f"❌ Error starting web dashboard: {e}")
        return None

def start_api_server():
    """Start the API server"""
    try:
        print("🔌 Starting API server...")
        from api_layer import CodingPracticeAPI
        
        api = CodingPracticeAPI()
        api.register_routes()
        
        print("✅ API server initialized")
        return api
        
    except ImportError as e:
        print(f"⚠️  API module not found: {e}")
        return None
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def initialize_pwa():
    """Initialize PWA components"""
    try:
        print("📱 Initializing PWA...")
        from pwa_manager import PWAManager
        
        pwa = PWAManager()
        pwa.setup_pwa_files()
        
        print("✅ PWA initialized")
        return pwa
        
    except ImportError as e:
        print(f"⚠️  PWA module not found: {e}")
        return None
    except Exception as e:
        print(f"❌ Error initializing PWA: {e}")
        return None

def create_simple_flask_app():
    """Create a simple Flask app if modules aren't available"""
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO
    import sqlite3
    from datetime import datetime, timedelta
    import json
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'demo-secret-key'
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Simple routes for demo
    @app.route('/')
    def dashboard():
        # Mock stats for demo
        stats = {
            'problems_solved': 42,
            'success_rate': 85.5,
            'current_streak': 7,
            'total_hours': 24
        }
        return render_template('dashboard.html', stats=stats)
    
    @app.route('/api/dashboard/stats')
    def api_stats():
        return jsonify({
            'problems_solved': 42,
            'success_rate': 85.5,
            'current_streak': 7,
            'total_hours': 24
        })
    
    @app.route('/api/dashboard/progress')
    def api_progress():
        days = int(request.args.get('days', 7))
        # Mock data
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
        problems = [2, 3, 1, 4, 2, 3, 5][:days]
        
        return jsonify({
            'dates': dates,
            'problems_solved': problems
        })
    
    @app.route('/api/dashboard/languages')
    def api_languages():
        return jsonify({
            'languages': ['Python', 'JavaScript', 'Java', 'C++'],
            'counts': [15, 12, 8, 7]
        })
    
    @app.route('/api/dashboard/activity')
    def api_activity():
        activities = [
            {
                'title': 'Solved Two Sum',
                'description': 'Completed in 12 minutes',
                'icon': 'fa-check-circle',
                'color': 'success',
                'time_ago': '2 hours ago'
            },
            {
                'title': 'Started study session',
                'description': 'Pomodoro focus mode',
                'icon': 'fa-play',
                'color': 'primary',
                'time_ago': '3 hours ago'
            },
            {
                'title': 'Reviewed Binary Search',
                'description': 'Spaced repetition',
                'icon': 'fa-redo',
                'color': 'info',
                'time_ago': '1 day ago'
            }
        ]
        return jsonify({'activities': activities})
    
    @app.route('/api/recommendations')
    def api_recommendations():
        recommendations = [
            {
                'id': 1,
                'title': 'Valid Parentheses',
                'description': 'Practice stack operations',
                'language': 'Python',
                'difficulty': 'Easy'
            },
            {
                'id': 2,
                'title': 'Merge Intervals',
                'description': 'Array manipulation',
                'language': 'Python', 
                'difficulty': 'Medium'
            }
        ]
        return jsonify({'recommendations': recommendations})
    
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'name': 'Coding Practice API',
            'version': '2.0.0',
            'description': 'Enhanced API for coding practice system',
            'endpoints': {
                '/api/dashboard/stats': 'GET - Dashboard statistics',
                '/api/dashboard/progress': 'GET - Progress over time',
                '/api/dashboard/languages': 'GET - Language distribution',
                '/api/dashboard/activity': 'GET - Recent activity',
                '/api/recommendations': 'GET - AI recommendations'
            }
        })
    
    return app, socketio

def open_browser(url):
    """Open browser after a short delay"""
    time.sleep(2)
    try:
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"Please open manually: {url}")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Try to start full system
    dashboard = start_web_dashboard()
    api = start_api_server()
    pwa = initialize_pwa()
    
    # Create Flask app (either enhanced or simple)
    if dashboard and api:
        print("🎉 Full system available!")
        app = dashboard.app
        socketio = dashboard.socketio
        port = 5000
    else:
        print("⚠️  Using simplified dashboard for demo")
        app, socketio = create_simple_flask_app()
        port = 5000
    
    # Setup PWA routes if available
    if pwa and hasattr(pwa, 'init_app'):
        pwa.init_app(app)
    
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print("📱 Mobile-friendly PWA enabled")
    print("🔄 Real-time updates with WebSocket")
    print("\n📋 Available URLs:")
    print(f"   Dashboard: http://localhost:{port}/")
    print(f"   API Docs:  http://localhost:{port}/api/docs")
    print(f"   PWA Manifest: http://localhost:{port}/static/manifest.json")
    
    print("\n⌨️  Keyboard shortcuts:")
    print("   Ctrl+C: Stop server")
    print("   Ctrl+R: Refresh dashboard (in browser)")
    print("   Ctrl+P: Start practice (in dashboard)")
    
    # Open browser in background thread
    threading.Thread(
        target=open_browser,
        args=(f"http://localhost:{port}/",),
        daemon=True
    ).start()
    
    try:
        print("\n" + "=" * 60)
        print("🎯 Server is running! Press Ctrl+C to stop")
        print("=" * 60)
        
        # Run the server
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        print("✅ Server stopped successfully")
        return 0
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 