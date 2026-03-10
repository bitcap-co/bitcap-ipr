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


args = parse_arguments()
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
        "--output-dir=dist",
    ]
)
p.wait()
os.rename("dist\\main.dist", "dist\\ipr")
shutil.copy("README.md", "dist")
shutil.copy("CONFIGURATION.md", "dist")
try:
    os.symlink("dist\\ipr\\BitCapIPR.exe", "dist\\BitCapIPR.exe")
except OSError:
    pass
shutil.make_archive(
    f"BitCapIPR-v{args.v}-win-x64-portable", "zip", os.path.join("dist")
)
os.remove("dist\\README.md")
os.remove("dist\\CONFIGURATION.md")

if not args.no_setup:
    p = Popen(
        ["C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe", ".\\setup\\setup.iss"]
    )
    p.wait()
    os.rename(
        os.path.join("setup", "Output/BitCapIPR-setup.exe"),
        f"BitCapIPR-v{args.v}-win-x64-setup.exe",
    )
sys.exit(0)
