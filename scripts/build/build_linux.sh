#!/bin/bash

PNAME="BitCapIPR"
OS="$(uname)"
PLATFORM="$(uname -i)"
ARCHIVE=0
VERSION=""

for arg in "$@"; do
    shift
    case "$arg" in
        "--archive-only"  ) set -- "$@" "-a"     ;;
        "--version-string") set -- "$@" "-V"     ;;
                        * ) set -- "$@" "$arg"
    esac
done

OPTIND=1
while getopts "aV:" opt; do
    case "$opt" in
        "a") ARCHIVE=1          ;;
        "V") VERSION="$OPTARG"  ;;
        \? ) echo "$0: ERROR (Invalid parameter flag)" >&2; exit 1 ;;
         : ) echo "$0: ERROR ($OPTARG requires an argument)" >&2; exit 1 ;;
    esac
done
shift $(( OPTIND - 1 ))

[[ -z "$VERSION" ]] && echo "ERROR: Supply version string." && exit 1

python3 -m nuitka src/main.py --assume-yes-for-downloads --standalone --output-file=BitCapIPR --output-dir=dist/BitCapIPR

mv dist/BitCapIPR/main.dist dist/BitCapIPR/ipr
cp README.md dist/BitCapIPR
cp CONFIGURATION.md dist/BitCapIPR
zip -r "dist/$PNAME-$VERSION-${OS,,}-$PLATFORM-portable.zip" dist/BitCapIPR
rm dist/BitCapIPR/README.md dist/BitCapIPR/CONFIGURATION.md

[[ ARCHIVE -eq 1 ]] && exit 1;

[ -e package ] && rm -rf package
mkdir -p package/DEBIAN
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/128x128/apps

# control file
echo "Package: bitcapipr" > package/DEBIAN/control
echo "Version: ${VERSION##v}" >> package/DEBIAN/control
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

dpkg-deb --build --root-owner-group package "dist/$PNAME-$VERSION-${OS,,}-$PLATFORM.deb"
