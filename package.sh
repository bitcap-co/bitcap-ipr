#!/bin/bash
## build ipr linux package with fpm

PNAME="bitcap-ipreporter"

# create dirs
[ -e package] && rm -r package
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/256x256/apps

cp -r dist/ipr package/opt/
cp src/resources/icons/app/BitCapLngLogo_IPR_Full_BLK-02x256.png package/usr/share/icons/hicolor/256x256/apps/
cp ipr.desktop package/usr/share/applications

find package/opt/ipr -type f -exec chmod 644 -- {} +
find package/opt/ipr -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/ipr/ipr

fpm -C package -s dir -t deb -n "$PNAME" -v "$1" -p "$PNAME-$1.deb"