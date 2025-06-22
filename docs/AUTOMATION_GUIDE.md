# 🤖 Automated Coding Practice System

## 🎯 Overview

This automation system streamlines your coding practice workflow by:
- **Automatically selecting problems** based on your preferences
- **Generating properly structured solution files** with templates
- **Tracking your progress** with detailed statistics
- **Auto-committing to git** with meaningful messages and milestone tags
- **Managing multiple programming languages** (Python, JavaScript, TypeScript, React)

## 🚀 Quick Start

### 1. Initial Setup
```bash
# Run the setup script
./setup.sh

# Or manually:
pip3 install -r requirements.txt
python3 practice.py setup
```

### 2. Start Your First Practice Session
```bash
# Start with default settings (Python, sequential selection)
python3 practice.py start

# Or use the alias (after setup)
practice start
```

### 3. Complete a Problem
```bash
# Mark as completed
python3 practice.py complete

# With notes
python3 practice.py complete --notes "Used two pointers technique"

# With time tracking
python3 practice.py complete --time 45 --notes "Struggled with edge cases"
```

### 4. Check Your Progress
```bash
python3 practice.py stats
```

## 📋 Available Commands

### Core Commands

#### `practice start`
Start a new practice session with intelligent problem selection.

**Options:**
- `--topic TOPIC`: Filter by specific topic (arrays, strings, trees, etc.)
- `--difficulty LEVEL`: Filter by difficulty (easy, medium, hard)
- `--language LANG`: Choose language (python, javascript, typescript, react)
- `--mode MODE`: Selection mode (sequential, random, topic)

**Examples:**
```bash
# Basic usage
practice start

# Practice arrays in Python
practice start --topic arrays --language python

# Random medium difficulty problems
practice start --difficulty medium --mode random

# Sequential JavaScript practice
practice start --language javascript --mode sequential
```

#### `practice complete`
Mark the current problem as completed and update progress.

**Options:**
- `--notes TEXT`: Add notes about your solution approach
- `--time MINUTES`: Record time spent (in minutes)

**Examples:**
```bash
# Simple completion
practice complete

# With detailed notes
practice complete --notes "Used HashMap for O(1) lookup, learned about handling duplicates"

# With time tracking
practice complete --time 30 --notes "Quick solution using built-in functions"
```

#### `practice stats`
Display comprehensive statistics about your practice sessions.

**Output includes:**
- Total problems solved by difficulty
- Topic breakdown
- Recent activity
- Progress trends

### Quick Aliases

After running setup, you can use these shorter commands:
- `pstart` = `practice start`
- `pcomplete` = `practice complete`
- `pstats` = `practice stats`

## 🎛️ Configuration

The system maintains a configuration file at `practice_data/config.json`:

```json
{
  "languages": ["python", "javascript", "typescript", "react"],
  "current_language": "python",
  "difficulty_preference": "mixed",
  "topic_preference": "sequential",
  "daily_goal": 3,
  "review_interval": 7,
  "auto_git": true
}
```

### Configuration Options:
- **languages**: Supported programming languages
- **current_language**: Default language for new sessions
- **daily_goal**: Target number of problems per day
- **auto_git**: Automatically commit completed problems to git
- **review_interval**: Days between problem reviews

## 📁 File Organization

### Generated Files
When you start a practice session, the system generates:

```
problem-solving/
├── leetcode/
│   ├── two-sum_easy_2024-01-15.py
│   ├── valid-parentheses_easy_2024-01-15.js
│   └── maximum-subarray_medium_2024-01-16.py
├── hackerrank/
│   └── [problems from HackerRank]
└── template.py  # Your original template
```

### File Naming Convention
`{problem-slug}_{difficulty}_{date}.{extension}`
- **problem-slug**: Kebab-case problem name
- **difficulty**: easy, medium, or hard
- **date**: YYYY-MM-DD format
- **extension**: Based on selected language (.py, .js, .ts, .jsx)

## 🗄️ Data Management

### Database Structure
The system uses SQLite to store:

**Problems Table:**
- Problem metadata (title, difficulty, topic, platform)
- Problem description and examples
- Constraints and hints
- URL and tags

**Progress Table:**
- Completion status and timestamps
- Language used
- Time spent and attempt count
- Personal notes
- File paths

### Progress Tracking Files
- `practice_data/problems.db`: SQLite database
- `practice_data/config.json`: User configuration
- `docs/learning-notes/progress-tracker.md`: Updated automatically

## 🔄 Git Integration

### Automatic Commits
When `auto_git` is enabled, the system:
1. **Adds all changes** to git staging
2. **Commits with descriptive message**: `✅ Solved: Problem Name (difficulty) - topic`
3. **Creates milestone tags** every 10 completed problems

### Milestone Tags
- `milestone-10`: First 10 problems completed
- `milestone-20`: 20 problems completed
- `milestone-50`: 50 problems completed
- And so on...

### Manual Git Control
To disable auto-commits, edit `practice_data/config.json`:
```json
{
  "auto_git": false
}
```

## 🎨 Language Templates

### Python Template
```python
"""
Problem: [Title]
Platform: [Platform]
Difficulty: [Level]
Date: [Date]
URL: [URL]

Problem Description:
[Description]

Examples:
[Examples]

Constraints:
[Constraints]

Tags: [Tags]
"""

def solution():
    """
    Approach:
    1. [Step 1]
    2. [Step 2]
    
    Time Complexity: O(?)
    Space Complexity: O(?)
    """
    pass

def test_solution():
    """Test cases"""
    # Test implementations
    pass

if __name__ == "__main__":
    test_solution()
```

### JavaScript Template
```javascript
/**
 * Problem: [Title]
 * Platform: [Platform]
 * [Other metadata]
 */

/**
 * Approach description
 * Time Complexity: O(?)
 * Space Complexity: O(?)
 */
function solution() {
    // Implementation
}

function testSolution() {
    // Test cases
}

testSolution();
```

## 📊 Progress Analytics

### Statistics Tracked
- **Total problems solved** by difficulty level
- **Topic distribution** showing your strengths/weaknesses
- **Recent activity** with completion dates
- **Time spent** on problems (when recorded)
- **Success rate** and retry patterns

### Example Stats Output
```
📊 Practice Statistics
==================================================
Total Problems Solved: 25
  Easy: 15
  Medium: 8
  Hard: 2

📚 By Topic:
  Arrays: 8
  Strings: 5
  Trees: 4
  Dynamic Programming: 3
  Graphs: 2
  Linked Lists: 3

🕐 Recent Activity:
  Two Sum (easy) - 2024-01-15
  Valid Parentheses (easy) - 2024-01-14
  Maximum Subarray (medium) - 2024-01-13
```

## 🛠️ Advanced Features

### Problem Selection Modes

#### Sequential Mode (Default)
- Follows a logical learning progression
- Ensures foundational concepts before advanced topics
- Ideal for systematic learning

#### Random Mode
- Provides variety in practice sessions
- Helps with pattern recognition across different problem types
- Good for maintaining engagement

#### Topic Mode
- Focuses on specific areas for deep learning
- Useful for targeted skill improvement
- Perfect for interview preparation

### Multi-Language Support

The system supports seamless switching between languages:
```bash
# Start Python session
practice start --language python

# Switch to JavaScript for next session
practice start --language javascript

# TypeScript for React preparation
practice start --language typescript
```

Each language maintains separate progress tracking, allowing you to:
- Compare your performance across languages
- Focus on language-specific patterns
- Build polyglot programming skills

## 🔧 Troubleshooting

### Common Issues

#### "No problems found"
- Run `python3 practice.py setup` to populate initial problems
- Check if your filters are too restrictive
- Verify database file exists in `practice_data/`

#### Git commit failures
- Ensure you're in a git repository (`git init` if needed)
- Check git configuration (`git config user.name` and `git config user.email`)
- Disable auto-git in config if not needed

#### Permission errors
- Run `chmod +x practice.py setup.sh` to make scripts executable
- Check file permissions in the practice_data directory

### Database Reset
If you need to reset your progress:
```bash
rm -rf practice_data/
python3 practice.py setup
```

## 🎯 Best Practices

### Daily Workflow
1. **Morning**: Check stats and set daily goals
2. **Practice**: Use `practice start` for focused sessions
3. **Evening**: Review completed problems and plan next day

### Problem-Solving Approach
1. **Read carefully**: Understand the problem completely
2. **Plan first**: Think through the approach before coding
3. **Implement**: Write clean, commented code
4. **Test thoroughly**: Verify with examples and edge cases
5. **Optimize**: Consider time/space complexity improvements
6. **Document**: Add meaningful notes when completing

### Progress Tracking
- Use `--notes` to record insights and learnings
- Track time spent to identify improvement areas
- Review stats weekly to adjust focus areas
- Set milestone goals and celebrate achievements

## 🚀 Future Enhancements

Planned features for future versions:
- **Web dashboard** for visual progress tracking
- **Spaced repetition** system for problem review
- **Difficulty progression** algorithm
- **Team challenges** and leaderboards
- **Integration with more platforms** (Codeforces, AtCoder)
- **AI-powered problem recommendations**
- **Performance analytics** and weak area identification

---

*Happy coding! The system is designed to grow with you as you improve. Focus on consistency and understanding rather than just solving problems.* 