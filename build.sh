#!/usr/bin/env bash
set -e

echo "🚀 Running build.sh..."

# 1. Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv venv

# 2. Activate venv
echo "🔧 Activating venv..."
source venv/bin/activate

# 3. Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 4. Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 5. Install Lighthouse CLI (skip if no permissions, it's optional)
echo "💡 Installing Lighthouse CLI..."
npm install -g lighthouse 2>/dev/null || echo "⚠️  Lighthouse install skipped (no permissions - scans will work without it)"

# 6. Install Playwright + browser binaries
# Moved to start.sh to use persistent disk
echo "⏩ Skipping Playwright install in build (will run in start.sh)..."





echo "🎉 Build completed successfully!"
