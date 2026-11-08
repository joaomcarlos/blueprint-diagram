#!/usr/bin/env python3
"""Run a diagram's export gate, then render native and reading-size PNGs."""
import argparse
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('script', type=Path)
parser.add_argument('--svg', type=Path, help='SVG produced by the script; default: script stem.svg')
args = parser.parse_args()
script = args.script.resolve()
svg = args.svg.resolve() if args.svg else script.with_suffix('.svg')
subprocess.run([sys.executable, str(script)], cwd=script.parent, check=True)
root = ET.parse(svg).getroot()
native_width = round(float(root.attrib.get('width', '1200')))
for width, path in [(native_width, svg.with_suffix('.png')),
                    (720, svg.with_name(svg.stem+'-reading.png'))]:
    subprocess.run(['rsvg-convert', '-w', str(width), str(svg), '-o', str(path)], check=True)
    print(path)
print('Geometry passed. View BOTH PNGs; complete REVIEW.md before delivery.')
