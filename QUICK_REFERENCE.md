# 🚀 Quick Reference Card

## Essential Commands

### Setup (One-time)
```bash
./setup.sh                    # Complete setup with aliases
python3 practice.py setup     # Manual setup
```

### Daily Workflow
```bash
# Start practice session
python3 practice.py start

# Complete current problem
python3 practice.py complete

# Check your progress
python3 practice.py stats
```

## Command Options

### Start Session
```bash
# Basic usage
python3 practice.py start

# Specific topic
python3 practice.py start --topic arrays

# Specific difficulty
python3 practice.py start --difficulty medium

# Different language
python3 practice.py start --language javascript

# Random selection
python3 practice.py start --mode random

# Combined options
python3 practice.py start --topic trees --difficulty easy --language python
```

### Complete Problem
```bash
# Simple completion
python3 practice.py complete

# With notes
python3 practice.py complete --notes "Used two pointers technique"

# With time tracking
python3 practice.py complete --time 30

# Full completion
python3 practice.py complete --time 45 --notes "Struggled with edge cases, learned about HashMap optimization"
```

## Quick Aliases (After Setup)
```bash
practice start              # Start session
pstart --topic arrays      # Quick start with topic
pcomplete --notes "..."     # Quick complete with notes
pstats                      # Quick stats
```

## File Locations
- **Generated problems**: `problem-solving/[platform]/`
- **Configuration**: `practice_data/config.json`
- **Database**: `practice_data/problems.db`
- **Progress tracker**: `docs/learning-notes/progress-tracker.md`

## Supported Languages
- Python (`.py`)
- JavaScript (`.js`)
- TypeScript (`.ts`)
- React (`.jsx`)

## Problem Selection Modes
- **sequential**: Logical progression (default)
- **random**: Random selection
- **topic**: Topic-focused

## Available Topics
- arrays
- strings
- linked-lists
- stacks
- trees
- graphs
- dynamic-programming
- sorting
- searching

## Git Integration
- Auto-commits completed problems
- Creates milestone tags (every 10 problems)
- Meaningful commit messages
- Can be disabled in config

## Quick Troubleshooting
```bash
# Reset database
rm -rf practice_data/
python3 practice.py setup

# Check permissions
chmod +x practice.py setup.sh

# View configuration
cat practice_data/config.json
```

---
*Keep this card handy for quick reference during your practice sessions!* 