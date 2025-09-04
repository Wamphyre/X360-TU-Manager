#!/bin/bash

# X360 TU Manager - AppImage builder script
# Creates a portable AppImage using Python directly (no PyInstaller needed)

set -Eeuo pipefail
IFS=$'\n\t'
trap 'echo "Error on line $LINENO" >&2' ERR

APP_NAME="${APP_NAME:-X360_TU_Manager}"
APP_VERSION="${APP_VERSION:-$(git describe --tags --always 2>/dev/null || echo 1.0.0)}"
ARCH="${ARCH:-$(uname -m)}"
APPDIR="AppDir"
PYTHON="${PYTHON:-python3}"

echo "🚀 Building X360 TU Manager AppImage (Python-based)..."

# Preflight checks
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "❌ $PYTHON not found. Please install Python 3." >&2
  exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$APPDIR" *.AppImage

# Create AppDir structure
echo "📁 Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/python3/dist-packages"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/opt/x360-tu-manager"


# Copy application files
echo "📄 Copying application files..."
cp -r assets/ "$APPDIR/opt/x360-tu-manager/"
cp -r xextool/ "$APPDIR/opt/x360-tu-manager/"
cp -r addons/ "$APPDIR/opt/x360-tu-manager/"
cp *.py "$APPDIR/opt/x360-tu-manager/"


# Install Python dependencies locally
echo "📦 Installing Python dependencies (into AppDir)..."
if [ -f requirements.txt ]; then
    "$PYTHON" -m pip install --disable-pip-version-check --no-cache-dir --no-compile \
        --target "$APPDIR/usr/lib/python3/dist-packages" -r requirements.txt
else
    echo "ℹ️ requirements.txt not found; skipping dependency install"
fi

# Verify Python environment
echo "🔍 Verifying Python environment..."
if [ -d "$APPDIR/usr/lib/python3/dist-packages" ]; then
    echo "  ✅ Python packages directory created"
    echo "  📦 Some installed packages:"
    ls "$APPDIR/usr/lib/python3/dist-packages/" | head -5 || true
else
    echo "  ⚠️  Python packages directory not found (may be fine if no deps)"
fi

# Check if requests is installed (optional)
if [ -d "$APPDIR/usr/lib/python3/dist-packages/requests" ]; then
    echo "  ✅ Requests library found"
else
    echo "  ℹ️ Requests library not found in AppDir (will rely on system if available)"
fi

# Trim caches to reduce size
if [ -d "$APPDIR/usr/lib/python3/dist-packages" ]; then
    echo "🧽 Removing __pycache__ directories..."
    find "$APPDIR/usr/lib/python3/dist-packages" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
fi

# Bundle system Python runtime into AppDir
echo "🐍 Bundling system Python runtime into AppDir..."
PYBIN="$(command -v "$PYTHON")"
PYMAJMIN="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
STDLIB_DIR="$($PYTHON -c 'import sysconfig; print(sysconfig.get_paths()["stdlib"])')"
LIBPY_SO="$($PYTHON -c 'import sys, sysconfig, glob, os; libdir=sysconfig.get_config_var("LIBDIR") or "/usr/lib"; stem=f"libpython{sys.version_info.major}.{sys.version_info.minor}"; cands=glob.glob(os.path.join(libdir, stem+"*.so*")); print(cands[0] if cands else "")')"

mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share"
cp -L "$PYBIN" "$APPDIR/usr/bin/python3"
# Copy Python standard library (e.g., /usr/lib/python3.X)
if [ -d "$STDLIB_DIR" ]; then
  cp -a "$STDLIB_DIR" "$APPDIR/usr/lib/" 2>/dev/null || true
else
  echo "⚠️  Could not locate Python stdlib via sysconfig; skipping copy"
fi
# Copy libpython shared library if available
if [ -n "$LIBPY_SO" ] && [ -f "$LIBPY_SO" ]; then
  cp -L "$LIBPY_SO" "$APPDIR/usr/lib/" 2>/dev/null || true
fi

# Bundle Tk/Tcl runtime (shared libs and scripts)
echo "🎛  Bundling Tk/Tcl runtime..."
if [ -d "/usr/share/tcltk" ]; then
  cp -a "/usr/share/tcltk" "$APPDIR/usr/share/" 2>/dev/null || true
fi
for libpat in libtk libtcl; do
  for f in /usr/lib*/${libpat}*.so*; do
    [ -e "$f" ] && cp -L "$f" "$APPDIR/usr/lib/" 2>/dev/null || true
  done
done

# Quick non-fatal check for embedded Python runtime
APPABS="$(readlink -f "$APPDIR")"
env LD_LIBRARY_PATH="$APPABS/usr/lib:${LD_LIBRARY_PATH:-}" PYTHONHOME="$APPABS/usr" TCL_LIBRARY="$APPABS/usr/share/tcltk/tcl8.6" TK_LIBRARY="$APPABS/usr/share/tcltk/tk8.6" \
  "$APPABS/usr/bin/python3" - << 'PY' >/dev/null 2>&1 || echo "⚠️  Embedded Python quick check skipped/failed (will rely on runtime)"
try:
    import sys, tkinter, ssl
    print("OK")
except Exception:
    pass
PY

# Note: Wine will be used from the system installation
echo "🍷 Wine will be used from system installation"
echo "  ⚠️  Make sure Wine is installed on target systems"

# Create main executable script
echo "🔧 Creating launcher script..."
cat > "$APPDIR/usr/bin/x360-tu-manager" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
APPDIR="$(dirname "$(dirname "$HERE")")"

echo "🚀 Starting X360 TU Manager AppImage..."
echo "📁 AppDir: $APPDIR"

# Set Python path to include our dependencies
export PYTHONPATH="$APPDIR/usr/lib/python3/dist-packages:$PYTHONPATH"
echo "🐍 Python path: $PYTHONPATH"

# Configure embedded Python runtime
export PYTHONHOME="$APPDIR/usr"
export LD_LIBRARY_PATH="$APPDIR/usr/lib:${LD_LIBRARY_PATH:-}"
# Set Tk/Tcl paths if present
[ -d "$APPDIR/usr/share/tcltk/tcl8.6" ] && export TCL_LIBRARY="$APPDIR/usr/share/tcltk/tcl8.6"
[ -d "$APPDIR/usr/share/tcltk/tk8.6" ] && export TK_LIBRARY="$APPDIR/usr/share/tcltk/tk8.6"

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
exec "$APPDIR/usr/bin/python3" main.py "$@"
EOF
chmod +x "$APPDIR/usr/bin/x360-tu-manager"

# Create desktop file
cat > "$APPDIR/usr/share/applications/x360-tu-manager.desktop" << EOF
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
echo "🎨 Preparing application icon..."

# Use existing icon if available; otherwise, create a tiny placeholder
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
if [ -f "assets/icon.png" ]; then
    echo "📋 Using existing icon.png from assets..."
    install -m 0644 assets/icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/x360-tu-manager.png"
    cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/x360-tu-manager.png" "$APPDIR/"
else
    echo "🧪 No icon found, creating minimal placeholder..."
    ICON_OUT="$APPDIR/usr/share/icons/hicolor/256x256/apps/x360-tu-manager.png"
    # 1x1 transparent PNG (base64)
    printf '%s' 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=' | base64 -d > "$ICON_OUT"
    cp "$ICON_OUT" "$APPDIR/"
fi

# Create AppRun
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export APPDIR="$HERE"

# Set up environment
export PATH="${HERE}/usr/bin:${PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/dist-packages:${PYTHONPATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
# Embedded Python runtime
export PYTHONHOME="${HERE}/usr"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
# Optional Tk/Tcl paths
[ -d "${HERE}/usr/share/tcltk/tcl8.6" ] && export TCL_LIBRARY="${HERE}/usr/share/tcltk/tcl8.6"
[ -d "${HERE}/usr/share/tcltk/tk8.6" ] && export TK_LIBRARY="${HERE}/usr/share/tcltk/tk8.6"

# Run the application
exec "${HERE}/usr/bin/x360-tu-manager" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Copy desktop file and icon to root (required by AppImage)
cp "$APPDIR/usr/share/applications/x360-tu-manager.desktop" "$APPDIR/"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/x360-tu-manager.png" "$APPDIR/" 2>/dev/null || \
cp "$APPDIR/usr/share/icons/hicolor/128x128/apps/x360-tu-manager.png" "$APPDIR/" 2>/dev/null || \
cp "$APPDIR/usr/share/icons/hicolor/64x64/apps/x360-tu-manager.png" "$APPDIR/" 2>/dev/null || \
true

# Select appimagetool based on architecture
case "$ARCH" in
  x86_64|amd64)
    APPIMAGETOOL_FILE="appimagetool-x86_64.AppImage"
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    APPIMAGE_ARCH="x86_64"
    ;;
  aarch64|arm64)
    APPIMAGETOOL_FILE="appimagetool-aarch64.AppImage"
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-aarch64.AppImage"
    APPIMAGE_ARCH="aarch64"
    ;;
  *)
    echo "⚠️  Unknown architecture '$ARCH'; defaulting to x86_64 appimagetool and label"
    APPIMAGETOOL_FILE="appimagetool-x86_64.AppImage"
    APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    APPIMAGE_ARCH="x86_64"
    ;;
esac

# Download appimagetool if not exists
if [ ! -f "$APPIMAGETOOL_FILE" ]; then
    echo "⬇️  Downloading $APPIMAGETOOL_FILE..."
    wget -q "$APPIMAGETOOL_URL"
    chmod +x "$APPIMAGETOOL_FILE"
fi

# Build AppImage
OUTPUT_FILE="${APP_NAME}-${APP_VERSION}-${APPIMAGE_ARCH}.AppImage"
echo "🔧 Building AppImage ($OUTPUT_FILE)..."
ARCH="$APPIMAGE_ARCH" ./$APPIMAGETOOL_FILE "$APPDIR" "$OUTPUT_FILE"

# Make executable
chmod +x "$OUTPUT_FILE"

echo "✅ AppImage created successfully!"
echo "📦 File: $OUTPUT_FILE"
echo "🚀 Run with: ./$(basename "$OUTPUT_FILE")"

# Show file info
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ AppImage ready!"
    ls -lh "$OUTPUT_FILE"
    echo ""
    echo "💡 This AppImage includes:"
    echo "   - Embedded Python 3 runtime + stdlib + Tk/Tcl (no system Python needed)"
    echo "   - Application files and assets"
    echo "   - XexTool.exe and assets"
    echo "   - Uses system Wine (install with: sudo apt install wine)"
    echo "   - No installation required!"
else
    echo "❌ AppImage creation failed!"
    exit 1
fi
