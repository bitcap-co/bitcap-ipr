import os
import sys
import argparse
import shutil
from subprocess import Popen

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action="store")
    parser.add_argument('--no-setup', action="store_true")
    return parser.parse_args()

args = parse_arguments()
p = Popen('pyinstaller .\src\ipr.spec --noconfirm')
p.wait()
#zip dist/BitCapIPR and rename zip archive with version
shutil.make_archive(f'BitCapIPR-{args.v}-win-x64-portable', 'zip', os.path.join("dist"))

if not args.no_setup:
    p = Popen("C:\Program Files (x86)\Inno Setup 6\ISCC.exe .\setup\setup.iss")
    p.wait()
    os.rename(os.path.join("setup", 'BitCapIPR-setup.exe'), f'BitCapIPR-{args.v}-win-x64-setup.exe')
