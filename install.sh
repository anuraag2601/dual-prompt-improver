#!/bin/bash

echo "🚀 Setting up Dual Prompt Improver..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is required but not installed. Please install pip first."
    exit 1
fi

echo "✅ Python found"

# Install dependencies
echo "📦 Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set your API key:"
echo "   For OpenAI: export OPENAI_API_KEY='your-key'"
echo "   For Anthropic: export ANTHROPIC_API_KEY='your-key'"
echo ""
echo "2. Prepare your input files:"
echo "   - user_input.txt (describe your task)"
echo "   - initial_system_prompt.txt (your starting prompt)"
echo "   - critique_system_prompt.txt (included by default)"
echo ""
echo "3. Run the improver:"
echo "   python dual_prompt_improver.py"
echo ""
echo "Happy prompt engineering! 🚀" 