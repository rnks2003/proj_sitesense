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

# 5. Install Lighthouse CLI (local install to avoid permissions issues)
echo "💡 Installing Lighthouse CLI..."
npm install lighthouse

# 6. Download and install ZAP standalone
echo "🛡️  Installing OWASP ZAP..."
ZAP_VERSION="2.15.0"
ZAP_DIR="./zap"

if [ ! -d "$ZAP_DIR" ]; then
    echo "   Downloading ZAP v${ZAP_VERSION}..."
    curl -L -o zap.tar.gz "https://github.com/zaproxy/zaproxy/releases/download/v${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz"
    
    if [ $? -eq 0 ]; then
        echo "   Extracting ZAP..."
        tar -xzf zap.tar.gz
        mv "ZAP_${ZAP_VERSION}" "$ZAP_DIR"
        rm zap.tar.gz
        chmod +x "$ZAP_DIR/zap.sh"
        echo "   ✅ ZAP installed successfully"
    else
        echo "   ⚠️  Failed to download ZAP. Security scans will be unavailable."
    fi
else
    echo "   ✅ ZAP already installed"
fi

# 7. Install Playwright + browser binaries
# Moved to start.sh to use persistent disk
echo "⏩ Skipping Playwright install in build (will run in start.sh)..."





echo "🎉 Build completed successfully!"
