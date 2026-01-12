#!/bin/bash

# Define variables
PLIST_NAME="com.gapintel.backend.plist"
SOURCE_PLIST="$(pwd)/$PLIST_NAME"
DEST_DIR="$HOME/Library/LaunchAgents"
DEST_PLIST="$DEST_DIR/$PLIST_NAME"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Copy the plist file
echo "📋 Copying service definition to $DEST_DIR..."
cp "$SOURCE_PLIST" "$DEST_PLIST"

# Unload previous instance if it exists (ignore errors)
launchctl unload "$DEST_PLIST" 2>/dev/null

# Load the new service
echo "🚀 Starting background service..."
launchctl load "$DEST_PLIST"

echo "✅ Service installed!"
echo "The backend will now run automatically in the background."
echo "It will restart automatically if it crashes or if you restart your computer."
echo "Logs are available at: ~/AiRAG/backend.log"
