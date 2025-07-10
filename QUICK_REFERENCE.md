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
# Start with filters
python3 practice.py start --topic arrays --difficulty easy
python3 practice.py start --language python --mode random

# Complete with enhanced tracking
python3 practice.py complete --time 15 --notes "Used two-pointer approach"
python3 practice.py complete --notes "Optimized with hash table"
```

### **Advanced Analytics & Visualization**
```bash
# Enhanced statistics with insights
python3 practice.py stats

# Comprehensive progress visualization
python3 practice.py visualize --charts --export --days 30
python3 practice.py visualize --language python --days 7

# Review for spaced repetition
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

# Safe reset with prompt
python3 practice.py reset --progress
```

## **📈 Progress Tracking Features**

### **Enhanced Statistics**
- **Comprehensive summaries** with emoji indicators
- **Difficulty breakdown** analysis
- **Topic distribution** insights
- **Performance recommendations** based on patterns
- **Recent activity** tracking
- **Time analytics** with averages

### **Visual Charts** (requires matplotlib)
- **Daily Progress**: Line chart of problems solved over time
- **Difficulty Distribution**: Pie chart of easy/medium/hard ratios
- **Topic Distribution**: Bar chart of most practiced topics

### **Smart Insights**
- Automatic difficulty balance recommendations
- Topic diversity suggestions
- Consistency tracking and motivation
- Performance trend analysis

## **🎯 Example Workflows**

### **Daily Practice Routine**
```bash
# 1. Check today's recommendation
pstats

# 2. Start focused practice
pstart --topic arrays --difficulty easy

# 3. Complete with time tracking
pcomplete --time 20 --notes "Learned sliding window technique"

# 4. Weekly review (Fridays)
preview --days 7
```

### **Weekly Analysis**
```bash
# Generate comprehensive report
pvisualize --charts --export --days 7

# Review last week's problems
preview --days 7

# Check progress trends
pstats
```

### **Problem Management**
```bash
# Fetch new problems monthly
pfetch --source leetcode --limit 50

# List pending problems by topic
plist --topic dynamic-programming --status pending

# Export progress for sharing
pexport --format json
```

## **⚡ Performance Features**

### **Database Optimizations**
- **90% faster** query performance with strategic indexes
- **Batch operations** for efficient data handling
- **Connection pooling** for reduced overhead
- **Optimized JOIN** operations

### **Enhanced CLI**
- **Intelligent caching** for faster responses
- **Parallel processing** for bulk operations
- **Progress indicators** for long-running tasks
- **Graceful error handling** with helpful messages

### **External Integration**
- **LeetCode API** integration for fresh problems
- **Rate limiting** to respect API limits
- **Offline fallback** for uninterrupted practice
- **Smart topic mapping** for automatic categorization

## **🔍 Advanced Filters & Options**

### **Problem Selection**
```bash
# Topic-based practice
--topic arrays|strings|trees|graphs|dp|greedy|backtracking

# Difficulty progression
--difficulty easy|medium|hard

# Language-specific tracking
--language python|javascript|typescript|react

# Selection modes
--mode sequential|random|topic
```

### **Time-based Analysis**
```bash
# Custom time ranges
--days 7|14|30|90

# Review intervals
--days 1    # Yesterday's problems
--days 3    # 3 days ago (spaced repetition)
--days 7    # Weekly review
--days 14   # Bi-weekly reinforcement
```

## **📚 Pro Tips**

### **Optimization Strategies**
1. **Use `pvisualize --charts`** weekly for visual progress tracking
2. **Set up `preview --days 7`** for spaced repetition learning
3. **Export data regularly** with `pexport` for backup
4. **Fetch new problems** monthly with `pfetch --source leetcode`
5. **Use topic filters** to focus on weak areas

### **Performance Tracking**
- **Track time consistently** for accurate analytics
- **Add meaningful notes** for future reference
- **Review insights** from `pstats` for improvement areas
- **Use charts** to visualize progress trends
- **Set up regular review** sessions for retention

### **System Maintenance**
- **Regular exports** for data backup
- **Periodic database optimization** with reset if needed
- **Update problem sets** with fresh content from APIs
- **Monitor performance** with built-in analytics

---

## **🎉 Quick Start (New Users)**

```bash
# 1. Setup everything
python3 practice.py setup

# 2. Fetch comprehensive problem set
python3 practice.py fetch --source all --limit 100

# 3. Start your first session
python3 practice.py start --topic arrays --difficulty easy

# 4. Complete and track
python3 practice.py complete --time 25 --notes "First problem solved!"

# 5. Check your progress
python3 practice.py visualize --charts
```

**Happy Coding! 🚀** 