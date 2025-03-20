#!/bin/bash

PNAME="BitCapIPR"
OS="$(uname)"
PLATFORM="$(uname -i)"

[[ -z "$1" ]] && echo "ERROR: Supply version string." && exit 1

python3 -m nuitka src/main.py --standalone --output-file=BitCapIPR --output-dir=dist/BitCapIPR

mv dist/BitCapIPR/main.dist dist/BitCapIPR/ipr
cp README.md dist/BitCapIPR
zip -r "dist/$PNAME-$1-${OS,,}-$PLATFORM-portable.zip" dist/BitCapIPR
rm dist/BitCapIPR/README.md

[ -e package ] && rm -rf package
mkdir -p package/DEBIAN
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/128x128/apps

# control file
echo "Package: bitcapipr" > package/DEBIAN/control
echo "Version: ${1##v}" >> package/DEBIAN/control
echo "Maintainer: MatthewWertman" >> package/DEBIAN/control
echo "Architecture: amd64" >> package/DEBIAN/control
echo "Homepage: https://github.com/bitcap-co/bitcap-ipr" >> package/DEBIAN/control
echo "Description: cross-platform IP reporter that listens for Antminers, IceRivers, and Whatsminers." >> package/DEBIAN/control

cp -r dist/BitCapIPR package/opt/
cp resources/app/icons/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png package/usr/share/icons/hicolor/128x128/apps/
cp resources/linux/ipr.desktop package/usr/share/applications/

find package/opt/BitCapIPR -type f -exec chmod 644 -- {} +
find package/opt/BitCapIPR -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/BitCapIPR/ipr/BitCapIPR

dpkg-deb --build --root-owner-group package "dist/$PNAME-$1-${OS,,}-$PLATFORM.deb"
