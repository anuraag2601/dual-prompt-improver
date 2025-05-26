#!/usr/bin/env python3
"""
Setup Validation Script

This script checks if everything is properly configured before running
the dual prompt improvement system.
"""

import os
import sys
from pathlib import Path

def check_api_key():
    """Check if OpenAI API key is set"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return False, "OPENAI_API_KEY environment variable not set"
    elif len(api_key) < 20:
        return False, "API key seems too short (possibly invalid)"
    elif not api_key.startswith(('sk-', 'sk_')):
        return False, "API key doesn't start with 'sk-' (possibly invalid)"
    else:
        return True, f"API key found (starts with: {api_key[:10]}...)"

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import openai
        return True, f"OpenAI package found (version: {openai.__version__})"
    except ImportError:
        return False, "OpenAI package not installed. Run: pip install openai"

def check_files():
    """Check if required input files exist"""
    required_files = [
        'user_input.txt',
        'initial_system_prompt.txt', 
        'critique_system_prompt.txt'
    ]
    
    missing_files = []
    existing_files = []
    
    for file in required_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            existing_files.append(f"{file} ({size} bytes)")
        else:
            missing_files.append(file)
    
    if missing_files:
        return False, f"Missing files: {', '.join(missing_files)}"
    else:
        return True, f"All files found: {', '.join(existing_files)}"

def check_config():
    """Check if config file exists and is valid"""
    try:
        import config
        return True, "Config file loaded successfully"
    except ImportError:
        return False, "config.py not found (will use defaults)"
    except Exception as e:
        return False, f"Error in config.py: {e}"

def check_main_script():
    """Check if main script exists"""
    if Path('dual_prompt_improver.py').exists():
        return True, "dual_prompt_improver.py found"
    else:
        return False, "dual_prompt_improver.py not found"

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return False, "No API key to test with"
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test. Please respond with just 'OK'."}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            return True, "OpenAI API connection successful"
        else:
            return False, "API responded but with empty content"
            
    except Exception as e:
        return False, f"API connection failed: {e}"

def print_status(check_name, success, message):
    """Print formatted status message"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:<10} {check_name:<25} {message}")

def main():
    """Run all validation checks"""
    print("🔍 DUAL PROMPT IMPROVER - SETUP VALIDATION")
    print("=" * 60)
    print()
    
    checks = [
        ("API Key", check_api_key),
        ("Dependencies", check_dependencies), 
        ("Required Files", check_files),
        ("Configuration", check_config),
        ("Main Script", check_main_script),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        success, message = check_func()
        print_status(check_name, success, message)
        if not success:
            all_passed = False
    
    print()
    
    # Test API connection if basic checks pass
    if all_passed:
        print("🌐 Testing OpenAI API connection...")
        success, message = test_openai_connection()
        print_status("API Connection", success, message)
        if not success:
            all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ You're ready to run the dual prompt improver!")
        print()
        print("To start:")
        print("  python dual_prompt_improver.py")
        print()
        print("To see a demo:")
        print("  python demo_comparison.py")
    else:
        print("❌ SOME CHECKS FAILED")
        print("Please fix the issues above before running the improver.")
        print()
        print("Quick fixes:")
        print("• Set API key: export OPENAI_API_KEY='your-key'")
        print("• Install OpenAI: pip install openai")
        print("• Create missing input files")
    
    print()
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 