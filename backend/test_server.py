#!/usr/bin/env python3
"""
Test script to verify the backend works without API keys
Run this to test the application in mock/test mode
"""

import os
import sys

# Set test mode environment variable
os.environ['TEST_MODE'] = 'true'

# Remove API keys if they don't exist to force test mode
if not os.getenv('OPENAI_API_KEY'):
    print("⚠️  No OPENAI_API_KEY found - running in TEST MODE")
    print("   The app will use mock data and fallback meal plans")
    print()

if not os.getenv('PERPLEXITY_API_KEY'):
    print("⚠️  No PERPLEXITY_API_KEY found - using mock ingredients")
    print()

# Import and run the app
from app import app

if __name__ == '__main__':
    print("=" * 50)
    print("🧪 TEST MODE - Backend Server")
    print("=" * 50)
    print("📡 Server starting on http://localhost:5000")
    print("💡 The app will work without API keys using mock data")
    print("=" * 50)
    print()
    
    app.run(debug=True, port=5000)


