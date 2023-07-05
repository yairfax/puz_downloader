#!/bin/bash

APP=$(osascript -e 'id of app "Across Lite"')

echo "App ID: $APP"

defaults write $APP NSRequiresAquaSystemAppearance -bool Yes

echo "Dark Mode disabled"