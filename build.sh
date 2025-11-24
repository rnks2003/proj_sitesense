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

# 5. Install Playwright + browser binaries
echo "🎭 Installing Playwright browsers..."
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/playwright-browsers
python -m playwright install chromium --with-deps


echo "🎉 Build completed successfully!"
