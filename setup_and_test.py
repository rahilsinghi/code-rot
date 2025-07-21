#!/usr/bin/env python3
"""
Setup and Test Script for Enhanced Coding Practice System
Installs dependencies, sets up environment, and runs comprehensive tests
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🚀 Enhanced Coding Practice System - Setup & Test")
    print("=" * 60)
    print("This script will:")
    print("  1. Install required dependencies")
    print("  2. Set up test environment")
    print("  3. Run comprehensive tests")
    print("  4. Launch demo components")
    print("=" * 60)

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing Dependencies...")
    
    # Core requirements
    core_packages = [
        "flask>=2.3.0",
        "flask-cors>=4.0.0", 
        "flask-limiter>=3.0.0",
        "requests>=2.31.0",
        "PyJWT>=2.8.0",
        "Werkzeug>=2.3.0"
    ]
    
    # Optional packages for enhanced features
    optional_packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "scikit-learn>=1.3.0",
        "scipy>=1.11.0",
        "psutil>=5.9.0",
        "pygame>=2.5.0"
    ]
    
    success_count = 0
    total_packages = len(core_packages) + len(optional_packages)
    
    print("📋 Installing core packages...")
    for package in core_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"  ✅ {package} installed")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install {package}: {e}")
    
    print("\n📋 Installing optional packages...")
    for package in optional_packages:
        try:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"  ✅ {package} installed")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Optional package {package} failed (continuing...)")
    
    print(f"\n📊 Installation Summary: {success_count}/{total_packages} packages installed")
    
    if success_count >= len(core_packages):
        print("✅ Core dependencies installed successfully!")
        return True
    else:
        print("❌ Some core dependencies failed to install")
        return False

def setup_environment():
    """Setup test environment"""
    print("\n⚙️  Setting up environment...")
    
    # Create necessary directories
    directories = [
        "practice_data",
        "test_data", 
        "logs",
        "static",
        "static/css",
        "static/js",
        "static/icons",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created directory: {directory}")
    
    print("✅ Environment setup complete!")

def run_quick_demo():
    """Run quick demonstration of components"""
    print("\n🎯 Running Quick Demo...")
    
    try:
        # Test imports
        print("  🔍 Testing imports...")
        
        modules_tested = 0
        modules_working = 0
        
        # Test PWA Manager
        try:
            from pwa_manager import PWAManager
            print("    ✅ PWA Manager import successful")
            modules_tested += 1
            modules_working += 1
        except Exception as e:
            print(f"    ❌ PWA Manager import failed: {e}")
            modules_tested += 1
        
        # Test Analytics Engine
        try:
            from analytics_engine import AdvancedAnalytics
            print("    ✅ Analytics Engine import successful")
            modules_tested += 1
            modules_working += 1
        except Exception as e:
            print(f"    ❌ Analytics Engine import failed: {e}")
            modules_tested += 1
        
        # Test API Layer
        try:
            from api_layer import CodingPracticeAPI
            print("    ✅ API Layer import successful")
            modules_tested += 1
            modules_working += 1
        except Exception as e:
            print(f"    ❌ API Layer import failed: {e}")
            modules_tested += 1
        
        # Test Notification System
        try:
            from notification_system import SmartNotificationSystem
            print("    ✅ Notification System import successful")
            modules_tested += 1
            modules_working += 1
        except Exception as e:
            print(f"    ❌ Notification System import failed: {e}")
            modules_tested += 1
        
        # Test Study Session Manager
        try:
            from study_session_manager import StudySessionManager
            print("    ✅ Study Session Manager import successful")
            modules_tested += 1
            modules_working += 1
        except Exception as e:
            print(f"    ❌ Study Session Manager import failed: {e}")
            modules_tested += 1
        
        print(f"  📊 Module Status: {modules_working}/{modules_tested} working")
        
        if modules_working >= 3:
            print("✅ Core system is functional!")
            return True
        else:
            print("⚠️  Some modules have issues")
            return False
            
    except Exception as e:
        print(f"  ❌ Demo failed: {e}")
        return False

def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("\n🧪 Running Comprehensive Tests...")
    print("This may take a few minutes...")
    
    try:
        # Import and run test runner
        from test_runner import main as run_tests
        
        print("🚀 Starting test suite...")
        exit_code = run_tests()
        
        if exit_code == 0:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n⚠️  Some tests failed - check output above")
        
        return exit_code == 0
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False

def launch_demo_components():
    """Launch demo components"""
    print("\n🎮 Demo Components Available:")
    print("  You can now test the following components:")
    print()
    
    # API Server demo
    print("  🌐 API Server:")
    print("    python api_layer.py --host 0.0.0.0 --port 5000")
    print("    Then visit: http://localhost:5000/api/docs")
    print()
    
    # Analytics demo
    print("  📊 Analytics Engine:")
    print("    python analytics_engine.py --generate-report")
    print()
    
    # Notification system demo
    print("  🔔 Notification System:")
    print("    python notification_system.py --test-notification")
    print()
    
    # Study session demo
    print("  ⏰ Study Session Manager:")
    print("    python study_session_manager.py --start --focus-mode pomodoro")
    print()
    
    # Web dashboard demo
    print("  📱 Web Dashboard:")
    print("    python web_dashboard.py")
    print("    Then visit: http://localhost:5000")
    print()

def interactive_demo():
    """Interactive demo menu"""
    while True:
        print("\n" + "=" * 50)
        print("🎮 INTERACTIVE DEMO MENU")
        print("=" * 50)
        print("1. 🌐 Start API Server")
        print("2. 📊 Generate Analytics Report")
        print("3. 🔔 Send Test Notification")
        print("4. ⏰ Start Study Session")
        print("5. 🧪 Run Full Test Suite")
        print("6. 📱 Launch Web Dashboard")
        print("7. ❌ Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == "1":
            demo_api_server()
        elif choice == "2":
            demo_analytics()
        elif choice == "3":
            demo_notifications()
        elif choice == "4":
            demo_study_session()
        elif choice == "5":
            run_comprehensive_tests()
        elif choice == "6":
            demo_web_dashboard()
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def demo_api_server():
    """Demo API server"""
    print("\n🌐 Starting API Server Demo...")
    print("The server will start on http://localhost:5001")
    print("API Documentation: http://localhost:5001/api/docs")
    print("Default admin login: username=admin, password=admin123")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        from api_layer import CodingPracticeAPI
        api = CodingPracticeAPI()
        api.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

def demo_analytics():
    """Demo analytics engine"""
    print("\n📊 Generating Analytics Report...")
    
    try:
        from analytics_engine import AdvancedAnalytics
        analytics = AdvancedAnalytics()
        
        report = analytics.get_learning_analytics("python", 30)
        
        print("📈 Learning Analytics Report:")
        if 'learning_velocity' in report:
            velocity = report['learning_velocity']
            print(f"  • Learning Velocity: {velocity.get('velocity', 0):.2f} problems/day")
            print(f"  • Trend: {velocity.get('trend', 'unknown')}")
            print(f"  • Consistency: {velocity.get('consistency', 0):.2f}")
        
        if 'knowledge_gaps' in report and report['knowledge_gaps']['gaps']:
            print("  • Top Knowledge Gaps:")
            for topic, info in list(report['knowledge_gaps']['gaps'].items())[:3]:
                print(f"    - {topic}: Severity {info['severity_score']:.2f}")
        
        print("✅ Analytics report generated successfully!")
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")

def demo_notifications():
    """Demo notification system"""
    print("\n🔔 Testing Notification System...")
    
    try:
        from notification_system import SmartNotificationSystem, Notification, NotificationType, NotificationPriority
        
        notifications = SmartNotificationSystem()
        
        # Send test notification
        test_notification = Notification(
            type=NotificationType.ACHIEVEMENT,
            priority=NotificationPriority.HIGH,
            title="🎉 Demo Achievement",
            message="You successfully tested the notification system!",
            channels=['in_app']
        )
        
        result = notifications.send_notification(test_notification)
        
        if result:
            print("✅ Test notification sent successfully!")
            
            # Check for achievements
            achievements = notifications.check_and_award_achievements("demo_user")
            print(f"🏆 Achievements checked: {len(achievements) if achievements else 0} new")
            
            # Get notifications
            user_notifications = notifications.get_notifications("demo_user", limit=5)
            print(f"📋 Recent notifications: {len(user_notifications)}")
            
        else:
            print("❌ Failed to send notification")
            
    except Exception as e:
        print(f"❌ Notification error: {e}")

def demo_study_session():
    """Demo study session manager"""
    print("\n⏰ Starting Study Session Demo...")
    
    try:
        from study_session_manager import StudySessionManager
        
        sessions = StudySessionManager()
        
        # Start a short demo session
        config = {
            'type': 'problem_solving',
            'focus_mode': 'pomodoro',
            'language': 'python',
            'duration': 60,  # 1 minute for demo
            'goals': ['Test the session system']
        }
        
        session = sessions.start_session(config)
        print(f"✅ Session started (ID: {session.id})")
        print(f"⏱️  Duration: {session.planned_duration}s")
        print(f"🎯 Focus Mode: {session.focus_mode.value}")
        
        # Show status
        status = sessions.get_session_status()
        print(f"📊 Status: {status['state']}")
        print(f"🔥 Active: {status['active']}")
        
        # Simulate some activity
        print("\n⏳ Simulating session activity...")
        time.sleep(2)
        
        # Add problem completion
        sessions.add_problem_completion({
            'problem_id': 1,
            'time_spent': 30,
            'language': 'python'
        })
        print("✅ Added problem completion")
        
        # End session
        completed = sessions.end_session(early=True)
        print(f"🏁 Session completed with focus score: {completed.focus_score:.1f}/10")
        
        # Show analytics
        analytics = sessions.get_productivity_analytics(1)
        overview = analytics['overview']
        print(f"📈 Total sessions today: {overview['total_sessions']}")
        
    except Exception as e:
        print(f"❌ Session error: {e}")

def demo_web_dashboard():
    """Demo web dashboard"""
    print("\n📱 Starting Web Dashboard Demo...")
    print("The dashboard will start on http://localhost:5000")
    print("Features: PWA support, real-time analytics, mobile-friendly")
    print("\nPress Ctrl+C to stop the dashboard")
    
    try:
        from web_dashboard import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

def main():
    """Main setup and test function"""
    print_header()
    
    # Step 1: Install dependencies
    deps_ok = install_dependencies()
    if not deps_ok:
        print("❌ Dependency installation failed. Some features may not work.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    # Step 2: Setup environment
    setup_environment()
    
    # Step 3: Quick demo
    demo_ok = run_quick_demo()
    
    # Step 4: Ask user what to do next
    print("\n" + "=" * 60)
    print("🎉 Setup Complete!")
    print("=" * 60)
    
    if demo_ok:
        print("✅ Your enhanced coding practice system is ready!")
    else:
        print("⚠️  System is partially ready - some components may have issues")
    
    print("\nWhat would you like to do next?")
    print("1. 🧪 Run comprehensive tests")
    print("2. 🎮 Interactive demo menu")
    print("3. 📋 Show manual testing commands")
    print("4. ❌ Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        run_comprehensive_tests()
    elif choice == "2":
        interactive_demo()
    elif choice == "3":
        launch_demo_components()
    elif choice == "4":
        print("👋 Setup complete! Check README for usage instructions.")
    else:
        print("Invalid choice. Run 'python setup_and_test.py' again to restart.")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 