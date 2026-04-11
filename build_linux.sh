#!/bin/bash
# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

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

[ -e dist ] && rm -rf dist
python3 -m nuitka src/main.py --assume-yes-for-downloads --standalone --output-file=BitCapIPR --output-dir=dist/BitCapIPR

mv dist/BitCapIPR/main.dist dist/BitCapIPR/bitcap-ipr
cp README.md CONFIGURATION.md dist/BitCapIPR/
ln -s bitcap-ipr/BitCapIPR dist/BitCapIPR/BitCapIPR
(cd dist && zip -r --symlinks "$PNAME-$VERSION-${OS,,}-$PLATFORM-portable.zip" .)
rm dist/BitCapIPR/README.md dist/BitCapIPR/CONFIGURATION.md dist/BitCapIPR/BitCapIPR

if [[ ARCHIVE -eq 1 ]]; then
  rm -rf dist/BitCapIPR
  exit 0
fi

# create bitcap-ipr package
mkdir -p dist/package/DEBIAN
mkdir -p dist/package/opt/bitcap-ipr
mkdir -p dist/package/usr/share/applications
mkdir -p dist/package/usr/share/icons/hicolor/128x128/apps

# control file
cat > dist/package/DEBIAN/control << EOF
Package: bitcap-ipr
Version: ${VERSION##v}
Maintainer: MatthewWertman
Architecture: amd64
Homepage: https://github.com/bitcap-co/bitcap-ipr
Description: cross-platform IP reporter that listens for Antminers, IceRivers, and Whatsminers.
EOF

(cd dist/BitCapIPR/bitcap-ipr && cp -r . ../../package/opt/bitcap-ipr)
cp resources/app/icons/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png dist/package/usr/share/icons/hicolor/128x128/apps/
cp resources/linux/bitcap-ipr.desktop dist/package/usr/share/applications/

find dist/package/opt/bitcap-ipr -type f -exec chmod 644 -- {} +
find dist/package/opt/bitcap-ipr -type d -exec chmod 755 -- {} +
find dist/package/usr/share -type f -exec chmod 644 -- {} +
chmod +x dist/package/opt/bitcap-ipr/BitCapIPR

(cd dist && dpkg-deb --build --root-owner-group package "$PNAME-$VERSION-${OS,,}-$PLATFORM.deb")
rm -rf dist/package
rm -rf dist/BitCapIPR
exit 0
