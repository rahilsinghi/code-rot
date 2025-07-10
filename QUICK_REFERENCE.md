# 🚀 Quick Reference - Enhanced Coding Practice System

## **Shell Aliases (After running setup.sh)**
```bash
# Core commands
pstart     # Start practice session
pcomplete  # Mark problem as completed
pstats     # Show comprehensive statistics
plist      # List problems with filters

# New enhanced commands
pfetch     # Fetch problems from external APIs
pvisualize # Generate progress charts and reports
preview    # Review problems from N days ago
preset     # Reset progress or database
pexport    # Export data to JSON/CSV
pimport    # Import problems from files

# NEW: Smart recommendations
precommend # Get personalized problem recommendations

# NEW: Spaced repetition system
preview-due     # Show problems due for review
preview-session # Start review session
preview-stats   # Review system statistics
```

## **📋 Core Commands**

### **Setup & Problem Management**
```bash
# Initial setup with enhanced fetching
python3 practice.py setup

# Fetch problems from external APIs
python3 practice.py fetch --source leetcode --limit 50
python3 practice.py fetch --source sample
python3 practice.py fetch --source all --limit 30

# Import custom problems
python3 practice.py import problems.json --format json
python3 practice.py import problems.csv --format csv
```

### **Practice Session**
```bash
# Start with filters and smart recommendations
python3 practice.py start --topic arrays --difficulty easy
python3 practice.py start --language python --mode smart  # 🆕 AI-powered selection
python3 practice.py start --mode random

# Complete with enhanced tracking
python3 practice.py complete --time 15 --notes "Used two-pointer approach"
python3 practice.py complete --notes "Optimized with hash table"
```

### **🆕 Smart Recommendations**
```bash
# Get personalized recommendations
python3 practice.py recommend --count 5
python3 practice.py recommend --topic arrays --count 3
python3 practice.py recommend --daily  # Daily challenge

# Start practice with smart selection
python3 practice.py start --mode smart  # Uses AI recommendations
```

### **🆕 Spaced Repetition System**
```bash
# Check what's due for review
python3 practice.py review-due --limit 10

# Start a review session
python3 practice.py review-session --time 30  # 30-minute session

# Complete a review with performance rating
python3 practice.py review-complete 15 excellent --time 10 --notes "Solved quickly"
python3 practice.py review-complete 23 fair --time 25

# View review statistics and retention analysis
python3 practice.py review-stats --days 30
```

### **Advanced Analytics & Visualization**
```bash
# Enhanced statistics with insights
python3 practice.py stats

# Comprehensive progress visualization
python3 practice.py visualize --charts --export --days 30
python3 practice.py visualize --language python --days 7

# Review for spaced repetition (different from review-due)
python3 practice.py review --days 7
python3 practice.py review --days 14
```

## **📊 List & Filter Commands**

### **Problem Listing**
```bash
# List with advanced filters
python3 practice.py list --topic arrays --difficulty easy --limit 10
python3 practice.py list --status pending --limit 20
python3 practice.py list --status completed --topic trees

# Quick status overview
python3 practice.py list --status pending    # Show pending problems
python3 practice.py list --status completed  # Show completed problems
```

## **🔧 Data Management**

### **Export & Backup**
```bash
# Export progress data
python3 practice.py export --format json --output backup.json
python3 practice.py export --format csv --output progress.csv

# Export with visualization reports
python3 practice.py visualize --export
```

### **Reset & Maintenance**
```bash
# Reset progress only (keep problems)
python3 practice.py reset --progress --confirm

# Reset everything (destructive)
python3 practice.py reset --all --confirm
```

## **🆕 New Features Overview**

### **Smart Recommendation Engine**
- **Personalized suggestions** based on your progress and performance
- **Difficulty progression** that adapts to your skill level
- **Topic mastery tracking** to identify weak areas
- **Learning path optimization** for systematic improvement

### **Spaced Repetition System**
- **Intelligent review scheduling** based on forgetting curves
- **Performance-based intervals** that adapt to your retention
- **Retention analysis** to identify problem areas
- **Optimized review sessions** for maximum efficiency

### **Enhanced Analytics**
- **Visual progress charts** with matplotlib integration
- **Comprehensive insights** and recommendations
- **Topic and difficulty analysis** with retention metrics
- **Performance trends** over time

## **🎯 Recommended Workflows**

### **Daily Practice Routine**
```bash
# 1. Check for due reviews first
python3 practice.py review-due

# 2. If reviews available, do a quick session
python3 practice.py review-session --time 15

# 3. Get smart recommendation for new problem
python3 practice.py recommend --daily

# 4. Start practice with smart selection
python3 practice.py start --mode smart

# 5. Complete and track progress
python3 practice.py complete --time 20 --notes "Your approach"
```

### **Weekly Review Process**
```bash
# 1. Check overall progress
python3 practice.py stats

# 2. Analyze retention patterns
python3 practice.py review-stats --days 7

# 3. Generate visual reports
python3 practice.py visualize --charts --days 7

# 4. Get topic-specific recommendations
python3 practice.py recommend --topic "your-weak-topic" --count 5
```

### **Performance Optimization**
```bash
# 1. Identify weak areas
python3 practice.py review-stats --days 30

# 2. Get targeted recommendations
python3 practice.py recommend --topic arrays --count 3

# 3. Practice with smart selection
python3 practice.py start --mode smart --topic arrays

# 4. Track improvement over time
python3 practice.py visualize --days 30 --export
```

## **📈 Performance Ratings Guide**

When completing reviews, use these performance ratings:

- **excellent**: Solved quickly and correctly, remembered approach clearly
- **good**: Solved correctly with minor hesitation or small mistakes
- **fair**: Solved but took longer than expected or needed hints
- **poor**: Struggled significantly or couldn't solve without help

## **🎮 Gamification Elements**

- **Ease factors**: Track how well you retain each problem (1.3-3.0)
- **Review streaks**: Maintain consistent review habits
- **Topic mastery**: Build expertise in specific areas
- **Difficulty progression**: Gradually tackle harder problems
- **Milestone tracking**: Celebrate achievements with git tags

---

**🚀 Pro Tips:**
- Use `--mode smart` for AI-powered problem selection
- Complete reviews daily to maintain optimal retention
- Focus on understanding rather than just solving
- Use visualization to track long-term progress
- Export data regularly for backup and analysis 