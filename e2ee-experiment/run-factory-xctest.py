#!/usr/bin/env python3
"""Run the allocated-media-kind regression from the actual upstream XCTest file."""
import argparse
from pathlib import Path
import plistlib
import subprocess

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--framework', type=Path, default=root / 'out/mac-creation-tests/WebRTC.framework')
parser.add_argument('--output-dir', type=Path, default=root / 'out/mac-factory-xctest')
args = parser.parse_args()
framework = args.framework.resolve(strict=True)
bundle = args.output_dir.resolve() / 'FactoryTests.xctest'
executable = bundle / 'Contents/MacOS/FactoryTests'
executable.parent.mkdir(parents=True, exist_ok=True)
developer = Path(subprocess.check_output(['xcode-select', '-p'], text=True).strip())
xctest = developer / 'Platforms/MacOSX.platform/Developer/Library/Frameworks'
sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
with (bundle / 'Contents/Info.plist').open('wb') as output:
    plistlib.dump({'CFBundleExecutable': 'FactoryTests',
                  'CFBundleIdentifier': 'org.webrtc.experimental.FactoryTests',
                  'CFBundlePackageType': 'BNDL'}, output)
subprocess.run([
    'xcrun', '--sdk', 'macosx', 'clang', '-fobjc-arc', '-bundle',
    '-target', 'arm64-apple-macos14.0', '-isysroot', sdk,
    '-I', str(root), '-I', str(root / 'sdk/objc'), '-I', str(root / 'sdk/objc/base'),
    '-F', str(xctest), '-F', str(framework.parent),
    '-framework', 'XCTest', '-framework', 'Foundation', '-framework', 'WebRTC',
    '-Wl,-rpath,' + str(xctest), '-Wl,-rpath,' + str(framework.parent),
    str(root / 'sdk/objc/unittests/RTCPeerConnectionFactory_xctest.m'),
    '-o', str(executable)], check=True)
subprocess.run(['xcrun', 'xctest', '-XCTest',
                'RTCPeerConnectionFactoryTests/testCapabilitiesWithNonconstantKindStrings',
                str(bundle)], check=True, timeout=60)
