# 🧪 Comprehensive Testing Guide

## 🚀 Quick Start

### 1. **One-Command Setup & Test**
```bash
python setup_and_test.py
```
This automated script will:
- Install all dependencies
- Set up the test environment  
- Run comprehensive tests
- Launch interactive demos

### 2. **Manual Testing Steps**

#### **Step 1: Install Dependencies**
```bash
pip install flask flask-cors flask-limiter requests PyJWT Werkzeug
pip install pandas numpy scikit-learn scipy psutil pygame  # Optional
```

#### **Step 2: Run Comprehensive Tests**
```bash
python test_runner.py
```

---

## 🧩 Component Testing

### **📱 PWA Manager**
```bash
# Test PWA functionality
python -c "
from pwa_manager import PWAManager
from flask import Flask
app = Flask(__name__)
pwa = PWAManager(app)
print('✅ PWA Status:', pwa.get_pwa_status())
"
```

### **🔬 Analytics Engine** 
```bash
# Generate analytics report
python analytics_engine.py --generate-report --language python --days 30

# Test programmatically
python -c "
from analytics_engine import AdvancedAnalytics
analytics = AdvancedAnalytics()
report = analytics.get_learning_analytics('python', 30)
print('📊 Velocity:', report['learning_velocity']['velocity'], 'problems/day')
print('📈 Trend:', report['learning_velocity']['trend'])
"
```

### **🌐 API Layer**
```bash
# Start API server
python api_layer.py --host 0.0.0.0 --port 5000

# Test in another terminal
curl http://localhost:5000/api/docs
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**API Endpoints to Test:**
- `GET /api/docs` - API documentation
- `POST /api/auth/login` - Authentication (admin/admin123)
- `GET /api/problems` - Get problems (requires auth)
- `GET /api/analytics/overview` - Analytics data
- `GET /api/system/health` - System health

### **🔔 Notification System**
```bash
# Send test notification
python notification_system.py --test-notification

# Check achievements
python notification_system.py --check-achievements

# Test programmatically
python -c "
from notification_system import SmartNotificationSystem, Notification, NotificationType
notifications = SmartNotificationSystem()
test_notif = Notification(
    type=NotificationType.ACHIEVEMENT,
    title='🎉 Test Achievement',
    message='Testing notifications!',
    channels=['in_app']
)
result = notifications.send_notification(test_notif)
print('✅ Notification sent:', result)
"
```

### **⏰ Study Session Manager**
```bash
# Start study session
python study_session_manager.py --start --focus-mode pomodoro --duration 5

# Check session status
python study_session_manager.py --status

# View analytics
python study_session_manager.py --analytics

# Test programmatically
python -c "
from study_session_manager import StudySessionManager
sessions = StudySessionManager()
session = sessions.start_session({
    'type': 'problem_solving',
    'focus_mode': 'pomodoro',
    'duration': 60
})
print('✅ Session started:', session.id)
status = sessions.get_session_status()
print('📊 Active:', status['active'])
sessions.end_session(early=True)
"
```

---

## 🎮 Interactive Testing

### **Interactive Demo Menu**
```bash
python setup_and_test.py
# Then select option 2: Interactive demo menu
```

This gives you:
1. 🌐 Start API Server
2. 📊 Generate Analytics Report  
3. 🔔 Send Test Notification
4. ⏰ Start Study Session
5. 🧪 Run Full Test Suite
6. 📱 Launch Web Dashboard

---

## 🌐 Web Testing

### **API Server Testing**
1. **Start server:**
   ```bash
   python api_layer.py --port 5001
   ```

2. **Visit endpoints:**
   - API docs: http://localhost:5001/api/docs
   - Health check: http://localhost:5001/api/system/health
   
3. **Test authentication:**
   ```bash
   # Login
   curl -X POST http://localhost:5001/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   
   # Use returned token
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5001/api/problems
   ```

### **PWA Testing (Mobile)**
1. Start the web dashboard
2. Open Chrome DevTools
3. Go to "Application" tab
4. Check "Service Workers" and "Manifest"
5. Test offline functionality by going offline in DevTools

---

## 📊 Expected Test Results

### **✅ Successful Test Output**
```
🧪 Enhanced Coding Practice System - Comprehensive Test Suite
======================================================================
✅ PWA Manager imported successfully
✅ Analytics Engine imported successfully  
✅ API Layer imported successfully
✅ Notification System imported successfully
✅ Study Session Manager imported successfully

🔬 Testing: File Generation
  📁 pwa_manager.py: ✅
  📁 analytics_engine.py: ✅
  📁 api_layer.py: ✅
  📁 notification_system.py: ✅
  📁 study_session_manager.py: ✅
✅ PASSED: File Generation

🔬 Testing: Analytics Engine
  📊 Velocity: 0.13 problems/day
  📊 Trend: stable
  📊 Analytics sections: 10
✅ PASSED: Analytics Engine

🔬 Testing: API Layer
  🌐 API Documentation: ✅
  🌐 Authentication: ✅
  🌐 Protected Endpoints: ✅
✅ PASSED: API Layer

======================================================================
🧪 TEST RESULTS SUMMARY
======================================================================
✅ PASSED: 8
❌ FAILED: 0
⏭️  SKIPPED: 0
📊 TOTAL: 8

🎉 ALL TESTS PASSED! Your system is ready to use!
📈 Success Rate: 100.0%
```

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Import Errors**
```bash
# If you see "ModuleNotFoundError"
pip install flask requests pandas numpy

# For optional dependencies
pip install scikit-learn scipy psutil pygame
```

#### **Port Already in Use**
```bash
# If port 5000 is busy
python api_layer.py --port 5001
```

#### **Database Issues**
```bash
# Clean test databases
rm -rf test_data/
rm -rf practice_data/
python setup_and_test.py  # Recreates everything
```

#### **Permission Issues**
```bash
# On Unix systems
chmod +x setup_and_test.py
chmod +x test_runner.py
```

### **Debugging Mode**
```bash
# Run with debug output
python api_layer.py --debug
python analytics_engine.py --generate-report --verbose
```

---

## 📱 Mobile/PWA Testing

### **Test PWA Installation**
1. Open Chrome on mobile or desktop
2. Visit your dashboard URL
3. Look for "Install App" prompt
4. Test offline functionality
5. Check home screen icon

### **Test Mobile Features**
- Touch-friendly interface
- Pull-to-refresh
- Bottom navigation
- Responsive design
- Offline caching

---

## 🎯 Feature Verification Checklist

### **✅ Core Features**
- [ ] All 5 components import successfully
- [ ] Test database created with sample data
- [ ] API server starts and responds
- [ ] Authentication works (admin/admin123)
- [ ] Analytics generate reports
- [ ] Notifications send successfully
- [ ] Study sessions start/end properly

### **✅ Advanced Features**
- [ ] PWA manifest generates correctly
- [ ] Service worker caches resources
- [ ] Real-time session tracking
- [ ] Achievement system awards points
- [ ] ML analytics provide insights
- [ ] API rate limiting works
- [ ] Mobile interface responsive

### **✅ Integration Features**  
- [ ] Components communicate correctly
- [ ] Data flows between modules
- [ ] Git auto-commit works
- [ ] Notification scheduling active
- [ ] Performance monitoring tracks metrics

---

## 💡 Usage Examples

### **Complete Workflow Test**
```python
# 1. Start study session
from study_session_manager import StudySessionManager
sessions = StudySessionManager()
session = sessions.start_session({
    'focus_mode': 'pomodoro',
    'duration': 300,  # 5 minutes
    'goals': ['Solve array problems']
})

# 2. Add problem completion
sessions.add_problem_completion({
    'problem_id': 1,
    'time_spent': 240,
    'language': 'python'
})

# 3. Check for achievements
from notification_system import SmartNotificationSystem
notifications = SmartNotificationSystem()
new_achievements = notifications.check_and_award_achievements('user1', {
    'time_spent': 240
})

# 4. Generate analytics
from analytics_engine import AdvancedAnalytics
analytics = AdvancedAnalytics()
report = analytics.get_learning_analytics('python', 7)

# 5. End session
completed_session = sessions.end_session()
print(f"Focus score: {completed_session.focus_score}/10")
```

---

## 🏁 Next Steps

After successful testing:

1. **Production Setup:** Configure email/push notifications
2. **Customization:** Modify achievement definitions
3. **Integration:** Connect with external APIs
4. **Monitoring:** Set up production logging
5. **Scaling:** Deploy with proper database

**Happy Coding! 🎉** 