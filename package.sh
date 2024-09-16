#!/bin/bash
## build ipr linux package with fpm

PNAME="bitcapipr"
PLATFORM="linux-x86_64"

# create dirs
[ -e package ] && rm -r package
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/128x128/apps

cp -r dist/BitCapIPR package/opt/
cp src/resources/icons/app/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png package/usr/share/icons/hicolor/128x128/apps/
cp ipr.desktop package/usr/share/applications

find package/opt/BitCapIPR -type f -exec chmod 644 -- {} +
find package/opt/BitCapIPR -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/BitCapIPR/BitCapIPR

fpm -C package -s dir -t deb -n "$PNAME" -v "$1" -p "dist/$PNAME-$1-$PLATFORM.deb"
