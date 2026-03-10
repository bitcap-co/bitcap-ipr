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

[ -e dist ] && rm -rf dist
python3 -m nuitka src/main.py --assume-yes-for-downloads --standalone --output-file=BitCapIPR --output-dir=dist

mv dist/main.dist dist/ipr
cp README.md CONFIGURATION.md dist
ln -s ipr/BitCapIPR dist/BitCapIPR
(cd dist && zip -r --symlinks "$PNAME-$VERSION-${OS,,}-$PLATFORM-portable.zip" .)
rm dist/README.md dist/CONFIGURATION.md dist/BitCapIPR

if [[ ARCHIVE -eq 1 ]]; then
  rm -rf dist/ipr
  exit 0
fi

# create bitcap-ipr package
mkdir -p dist/package/DEBIAN
mkdir -p dist/package/opt/BitCapIPR
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

cp -r dist/ipr dist/package/opt/BitCapIPR
cp resources/app/icons/BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png dist/package/usr/share/icons/hicolor/128x128/apps/
cp resources/linux/ipr.desktop dist/package/usr/share/applications/

find dist/package/opt/BitCapIPR -type f -exec chmod 644 -- {} +
find dist/package/opt/BitCapIPR -type d -exec chmod 755 -- {} +
find dist/package/usr/share -type f -exec chmod 644 -- {} +
chmod +x dist/package/opt/BitCapIPR/ipr/BitCapIPR

(cd dist && dpkg-deb --build --root-owner-group package "$PNAME-$VERSION-${OS,,}-$PLATFORM.deb")
rm -rf dist/package
rm -rf dist/ipr
exit 0
