#!/bin/bash

# Post-build script to set up the app launcher
# This script modifies the built app to include environment setup

set -e

APP_PATH="dist/ChatCircuit.app"
MACOS_PATH="$APP_PATH/Contents/MacOS"
ORIGINAL_EXE="$MACOS_PATH/app"
BACKUP_EXE="$MACOS_PATH/app_original"
LAUNCHER_SCRIPT="$MACOS_PATH/app"

echo "Setting up launcher for ChatCircuit.app..."

# Check if the app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH not found. Run 'make package' first."
    exit 1
fi

# Backup the original executable
if [ -f "$ORIGINAL_EXE" ] && [ ! -f "$BACKUP_EXE" ]; then
    echo "Backing up original executable..."
    mv "$ORIGINAL_EXE" "$BACKUP_EXE"
fi

# Create the launcher script
echo "Creating launcher script..."
cat > "$LAUNCHER_SCRIPT" << 'EOF'
#!/bin/bash

# ChatCircuit App Launcher
# This script sets up the proper environment for the app

# Get the directory where this script is located (inside the app bundle)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
PROJECT_DIR="$(dirname "$(dirname "$APP_DIR")")"

# Set up environment variables
export VIRTUAL_ENV="$PROJECT_DIR/.venv"
export PATH="$VIRTUAL_ENV/bin:$PATH"

# Change to project directory
cd "$PROJECT_DIR"

# Launch the actual application executable
exec "$SCRIPT_DIR/app_original"
EOF

# Make the launcher executable
chmod +x "$LAUNCHER_SCRIPT"

echo "Launcher setup complete!"
echo "The app should now launch properly via Finder or 'open' command."
