# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import argparse
import os
import shutil
import sys
from subprocess import Popen


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", action="store", required=True)
    parser.add_argument("--no-setup", action="store_true")
    return parser.parse_args()


def main():
    args = parse_arguments()
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    p = Popen(
        [
            sys.executable,
            "-m",
            "nuitka",
            "src/main.py",
            "--assume-yes-for-downloads",
            "--msvc=latest",
            "--windows-console-mode=disable",
            "--windows-icon-from-ico=resources/app/icons//BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.ico",
            "--standalone",
            "--output-file=BitCapIPR",
            "--output-dir=dist/BitCapIPR",
        ]
    )
    p.wait()
    os.rename("dist\\BitCapIPR\\main.dist", "dist\\BitCapIPR\\bitcap-ipr")
    shutil.copy("README.md", "dist\\BitCapIPR")
    shutil.copy("CONFIGURATION.md", "dist\\BitCapIPR")
    shutil.make_archive(
        f"dist\\BitCapIPR-v{args.v}-win-x64-portable",
        "zip",
        os.path.join("dist\\BitCapIPR"),
    )
    os.remove("dist\\BitCapIPR\\README.md")
    os.remove("dist\\BitCapIPR\\CONFIGURATION.md")

    if args.no_setup:
        shutil.rmtree("dist\\BitCapIPR")
        sys.exit(1)
    else:
        p = Popen(
            ["C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe", ".\\setup\\setup.iss"]
        )
        p.wait()
        os.rename(
            os.path.join("setup", "Output/BitCapIPR-setup.exe"),
            f"dist\\BitCapIPR-v{args.v}-win-x64-setup.exe",
        )
        shutil.rmtree("dist\\BitCapIPR")
    sys.exit(0)


if __name__ == "__main__":
    main()
