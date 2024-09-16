#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/BitCapIPR.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/BitCapIPR.dmg" && rm "dist/BitCapIPR.dmg"
create-dmg \
  --volname "BitCapIPR" \
  --volicon "src/resources/icons/app/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.icns" \
  --window-pos 200 120 \
  --window-size 500 500 \
  --icon-size 100 \
  --icon "BitCapIPR.app" 175 120 \
  --hide-extension "BitCapIPR.app" \
  --app-drop-link 425 120 \
  "dist/BitCapIPR.dmg" \
  "dist/dmg/"
