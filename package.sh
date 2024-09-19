#!/bin/bash
## build ipr linux package with dpkg-deb

PNAME="bitcapipr"
PLATFORM="linux-x86_64"

# create dirs
[ -e package ] && rm -r package
mkdir -p package/DEBIAN
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/128x128/apps

cat > package/DEBIAN/control << "EOF"
Package: bitcapipr
Version: 1.0.0
Maintainer: MatthewWertman
Architecture: amd64
Homepage: https://matthewwertman.github.io/
Description: cross-platform IP Reporter that listens for AntMiners, IceRivers, and Whatsminers.
EOF

cp -r dist/BitCapIPR package/opt/
cp src/resources/icons/app/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png package/usr/share/icons/hicolor/128x128/apps/
cp ipr.desktop package/usr/share/applications

find package/opt/BitCapIPR -type f -exec chmod 644 -- {} +
find package/opt/BitCapIPR -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/BitCapIPR/BitCapIPR

dpkg-deb --build --root-owner-group package "dist/$PNAME-$1-$PLATFORM.deb"
