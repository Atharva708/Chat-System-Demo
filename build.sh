#!/bin/bash
set -e

echo "🔧 Building Chat System for Render..."

# Install system dependencies (Tesseract OCR)
# Render runs build commands as root, so no sudo needed
echo "📦 Installing Tesseract OCR..."
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Verify Tesseract installation
echo "✓ Verifying Tesseract installation..."
if command -v tesseract &> /dev/null; then
    tesseract --version
else
    echo "⚠ Tesseract not found in PATH, will try to locate it..."
    # Try common locations
    if [ -f "/usr/bin/tesseract" ]; then
        export TESSERACT_CMD="/usr/bin/tesseract"
        echo "✓ Found Tesseract at /usr/bin/tesseract"
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"

