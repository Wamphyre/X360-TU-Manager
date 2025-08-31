#!/bin/bash

# X360 TU Manager - AppImage builder script
# Creates a portable AppImage using Python directly (no PyInstaller needed)

set -e

APP_NAME="X360_TU_Manager"
APP_VERSION="1.0.0"

echo "🚀 Building X360 TU Manager AppImage (Python-based)..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf AppDir/ *.AppImage

# Create AppDir structure
echo "📁 Creating AppDir structure..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/lib/python3/dist-packages
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p AppDir/opt/x360-tu-manager


# Copy application files
echo "� Cnopying application files..."
cp -r assets/ AppDir/opt/x360-tu-manager/
cp -r xextool/ AppDir/opt/x360-tu-manager/
cp -r addons/ AppDir/opt/x360-tu-manager/
cp *.py AppDir/opt/x360-tu-manager/


# Install Python dependencies locally
echo "📦 Installing Python dependencies..."
pip install --target AppDir/usr/lib/python3/dist-packages -r requirements.txt

# Install Pillow for icon creation
echo "🎨 Installing Pillow for icon creation..."
pip install --target AppDir/usr/lib/python3/dist-packages Pillow

# Verify Python environment
echo "🔍 Verifying Python environment..."
if [ -d "AppDir/usr/lib/python3/dist-packages" ]; then
    echo "  ✅ Python packages directory created"
    echo "  📦 Installed packages:"
    ls AppDir/usr/lib/python3/dist-packages/ | head -5
else
    echo "  ❌ Python packages directory not found"
fi

# Check if requests is installed
if [ -d "AppDir/usr/lib/python3/dist-packages/requests" ]; then
    echo "  ✅ Requests library found"
else
    echo "  ❌ Requests library not found"
fi

# Note: Wine will be used from the system installation
echo "🍷 Wine will be used from system installation"
echo "  ⚠️  Make sure Wine is installed on target systems"

# Create main executable script
echo "🔧 Creating launcher script..."
cat > AppDir/usr/bin/x360-tu-manager << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
APPDIR="$(dirname "$(dirname "$HERE")")"

echo "🚀 Starting X360 TU Manager AppImage..."
echo "📁 AppDir: $APPDIR"

# Set Python path to include our dependencies
export PYTHONPATH="$APPDIR/usr/lib/python3/dist-packages:$PYTHONPATH"
echo "🐍 Python path: $PYTHONPATH"

# Verify Python dependencies
if [ -d "$APPDIR/usr/lib/python3/dist-packages/requests" ]; then
    echo "✅ Python requests library found"
else
    echo "❌ Python requests library not found"
fi

# Wine will be configured when needed by the application

# Check if Wine is available on the system (but don't initialize it)
if command -v wine &> /dev/null; then
    echo "✅ Wine found on system: $(wine --version 2>/dev/null)"
else
    echo "⚠️  Wine not found - XexTool.exe functionality will be limited"
    echo "   Install with: sudo apt install wine"
fi

# Change to app directory
cd "$APPDIR/opt/x360-tu-manager"
echo "📂 Working directory: $(pwd)"

# Verify application files
if [ -f "main.py" ]; then
    echo "✅ main.py found"
else
    echo "❌ main.py not found"
    exit 1
fi

if [ -d "xextool" ]; then
    echo "✅ xextool directory found"
else
    echo "❌ xextool directory not found"
fi

# Run the application
echo "🎮 Starting application..."
exec python3 main.py "$@"
EOF
chmod +x AppDir/usr/bin/x360-tu-manager

# Create desktop file
cat > AppDir/usr/share/applications/x360-tu-manager.desktop << EOF
[Desktop Entry]
Type=Application
Name=X360 TU Manager
Comment=Xbox 360 Title Updates Manager
Exec=x360-tu-manager
Icon=x360-tu-manager
Categories=Game;
Terminal=false
EOF

# Create application icons
echo "🎨 Creating application icons..."

# First, try to use the existing icon.png if available
if [ -f "assets/icon.png" ]; then
    echo "📋 Using existing icon.png from assets..."
    # Create icon directories for different sizes
    mkdir -p AppDir/usr/share/icons/hicolor/{16x16,32x32,48x48,64x64,128x128,256x256,512x512}/apps
    
    # Use Python to resize the existing icon to different sizes
    PYTHONPATH="AppDir/usr/lib/python3/dist-packages:$PYTHONPATH" python3 << 'EOF'
from PIL import Image
import os

# Load the original icon
original_icon = Image.open('assets/icon.png')
print(f"📏 Original icon size: {original_icon.size}")

# Create different sizes for Ubuntu integration
sizes = [16, 32, 48, 64, 128, 256, 512]

for size in sizes:
    # Resize with high quality
    resized = original_icon.resize((size, size), Image.Resampling.LANCZOS)
    
    # Save to appropriate directory
    icon_dir = f'AppDir/usr/share/icons/hicolor/{size}x{size}/apps'
    os.makedirs(icon_dir, exist_ok=True)
    icon_path = f'{icon_dir}/x360-tu-manager.png'
    resized.save(icon_path)
    print(f"✅ Created {size}x{size} icon")

print("🎨 All icon sizes created successfully")
EOF
else
    echo "🎨 Creating fallback icon..."
    # Create a fallback icon using Python
    PYTHONPATH="AppDir/usr/lib/python3/dist-packages:$PYTHONPATH" python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import os

# Create icon directories
sizes = [16, 32, 48, 64, 128, 256, 512]
for size in sizes:
    icon_dir = f'AppDir/usr/share/icons/hicolor/{size}x{size}/apps'
    os.makedirs(icon_dir, exist_ok=True)

# Create base 256x256 image
base_img = Image.new('RGB', (256, 256), color='#2E8B57')
draw = ImageDraw.Draw(base_img)

# Draw Xbox controller-like shape
draw.rectangle([50, 100, 206, 180], fill='#1F5F3F', outline='#FFFFFF', width=3)
draw.rectangle([70, 120, 90, 140], fill='#FFFFFF')
draw.rectangle([80, 110, 100, 150], fill='#FFFFFF')
draw.ellipse([170, 110, 190, 130], fill='#FF4444', outline='#FFFFFF', width=2)
draw.ellipse([180, 120, 200, 140], fill='#44FF44', outline='#FFFFFF', width=2)
draw.ellipse([160, 120, 180, 140], fill='#4444FF', outline='#FFFFFF', width=2)
draw.ellipse([170, 130, 190, 150], fill='#FFFF44', outline='#FFFFFF', width=2)

# Add text
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except:
    font = ImageFont.load_default()

text = "X360 TU"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
x = (256 - text_width) // 2
draw.text((x, 200), text, fill='#FFFFFF', font=font)

# Create all sizes
for size in sizes:
    resized = base_img.resize((size, size), Image.Resampling.LANCZOS)
    icon_path = f'AppDir/usr/share/icons/hicolor/{size}x{size}/apps/x360-tu-manager.png'
    resized.save(icon_path)
    print(f"✅ Created {size}x{size} fallback icon")

print("🎨 Fallback icons created successfully")
EOF
fi

# Create AppRun
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export APPDIR="$HERE"

# Set up environment
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"

# Run the application
exec "${HERE}/usr/bin/x360-tu-manager" "$@"
EOF
chmod +x AppDir/AppRun

# Copy desktop file and icon to root (required by AppImage)
cp AppDir/usr/share/applications/x360-tu-manager.desktop AppDir/
cp AppDir/usr/share/icons/hicolor/256x256/apps/x360-tu-manager.png AppDir/ 2>/dev/null || \
cp AppDir/usr/share/icons/hicolor/128x128/apps/x360-tu-manager.png AppDir/ 2>/dev/null || \
echo "x360-tu-manager" > AppDir/x360-tu-manager.png

# Download appimagetool if not exists
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "⬇️  Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "🔧 Building AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir "${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

# Make executable
chmod +x "${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

echo "✅ AppImage created successfully!"
echo "📦 File: ${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
echo "🚀 Run with: ./${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

# Show file info
if [ -f "${APP_NAME}-${APP_VERSION}-x86_64.AppImage" ]; then
    echo "✅ AppImage ready!"
    ls -lh "${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
    echo ""
    echo "💡 This AppImage includes:"
    echo "   - Python runtime environment"
    echo "   - All required dependencies"
    echo "   - XexTool.exe and assets"
    echo "   - Uses system Wine (install with: sudo apt install wine)"
    echo "   - No installation required!"
else
    echo "❌ AppImage creation failed!"
    exit 1
fi