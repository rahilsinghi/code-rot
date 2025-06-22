#!/bin/bash

# Automated Coding Practice Setup Script

echo "🚀 Setting up your automated coding practice environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies in virtual environment..."
source venv/bin/activate
pip install -r requirements.txt

# Make practice script executable
chmod +x practice.py

# Initialize the practice database
echo "🗄️ Initializing practice database..."
python3 practice.py setup

# Create shell aliases for convenience
echo "🔧 Setting up shell aliases..."

# Detect shell and add aliases
if [[ $SHELL == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ $SHELL == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
else
    SHELL_RC="$HOME/.profile"
fi

# Add aliases if they don't exist
if ! grep -q "alias practice=" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Coding Practice Aliases" >> "$SHELL_RC"
    echo "alias practice='source $(pwd)/venv/bin/activate && python $(pwd)/practice.py'" >> "$SHELL_RC"
    echo "alias pstart='source $(pwd)/venv/bin/activate && python $(pwd)/practice.py start'" >> "$SHELL_RC"
    echo "alias pcomplete='source $(pwd)/venv/bin/activate && python $(pwd)/practice.py complete'" >> "$SHELL_RC"
    echo "alias pstats='source $(pwd)/venv/bin/activate && python $(pwd)/practice.py stats'" >> "$SHELL_RC"
    echo "alias activate-practice='source $(pwd)/venv/bin/activate'" >> "$SHELL_RC"
    echo "✅ Added shell aliases to $SHELL_RC"
    echo "   Run 'source $SHELL_RC' or restart your terminal to use aliases"
else
    echo "ℹ️ Shell aliases already exist"
fi

echo ""
echo "🎉 Setup complete! You can now use the following commands:"
echo ""
echo "📚 Basic Commands:"
echo "  python3 practice.py start                    # Start a practice session"
echo "  python3 practice.py complete                 # Mark current problem as done"
echo "  python3 practice.py stats                    # View your progress"
echo ""
echo "🎯 Advanced Options:"
echo "  python3 practice.py start --topic arrays     # Practice specific topic"
echo "  python3 practice.py start --difficulty easy  # Practice specific difficulty"
echo "  python3 practice.py start --language python  # Use specific language"
echo "  python3 practice.py start --mode random      # Random problem selection"
echo ""
echo "⚡ Quick Aliases (after sourcing shell config):"
echo "  practice start                               # Start practice"
echo "  pstart --topic arrays                       # Quick start with topic"
echo "  pcomplete --notes 'Used two pointers'       # Complete with notes"
echo "  pstats                                       # Quick stats"
echo ""
echo "🚀 Ready to start coding! Try: python3 practice.py start" 