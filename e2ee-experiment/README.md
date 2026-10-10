# Local M144 build and test checkpoint

These are the GN configurations used for the 2026-10-10 source experiment.
They produced an arm64 tvOS framework and macOS native test executable. They
are not a published XCFramework recipe or a production replacement for
LiveKitWebRTC: the framework is unsigned, uses the `WebRTC`/`RTC` names rather
than LiveKit's prefixes, and contains only the creation-time hook, not the
Jitsi-compatible cryptor/controller.

## Environment

- macOS 27.0.1 (26A434), Apple Silicon.
- Xcode 27.0 (27A5228h), macOS/tvOS 27 SDKs.
- WebRTC base: `30d5e63ae91da483e06577b5c35ee91cc5e5c3db` plus this branch.
- DEPS `build` checkout: `be1a8f6dcd7df7e46320192c5e2f364e50d79bbf`.
- Bundled Clang 22, package `llvmorg-22-init-14273-gea10026b-2`, executable
  revision `efe9a8c95451c9dadb5dd522802b05afd8b52d1b`.
- Bundled LLD, system libc++, and disabled Clang modules.

The original configuration hit SDK module/header errors with bundled libc++.
System libc++ and disabled modules passed those points. Apple's linker then
rejected a missing bundled `libLTO.dylib` warning; using the matching bundled
LLD resolved the link failure. No dependency-source edits were required. These
choices must be reconsidered against the shipping framework's ABI/toolchain.

## Commands

Use a dedicated workspace containing `depot_tools/` and a `src/` checkout of
this fork's development branch. Select the intended Xcode installation before
running hooks. In the workspace parent, the `.gclient` used here contains:

```python
solutions = [{
    'name': 'src', 'url': 'https://github.com/webrtc-sdk/webrtc.git',
    'managed': False, 'deps_file': 'DEPS', 'custom_deps': {}, 'custom_vars': {}
}]
target_os = ['ios']
```

`managed: False` preserves the already-checked-out patched source. Run dependency
sync and hooks from the workspace with depot_tools on PATH:

```sh
DEPOT_TOOLS_UPDATE=0 gclient sync --nohooks --no-history -j 6
DEPOT_TOOLS_UPDATE=0 gclient runhooks
```

From `src/`:

```sh
mkdir -p out/mac-creation-tests out/tvos-creation-hook
cp e2ee-experiment/mac-tests.args.gn out/mac-creation-tests/args.gn
cp e2ee-experiment/tvos-device.args.gn out/tvos-creation-hook/args.gn
buildtools/mac/gn gen out/mac-creation-tests
buildtools/mac/gn gen out/tvos-creation-hook
third_party/ninja/ninja -C out/mac-creation-tests -j 4 pc:peerconnection_unittests
third_party/ninja/ninja -C out/mac-creation-tests -j 4 sdk:mac_framework_objc
third_party/ninja/ninja -C out/tvos-creation-hook -j 4 sdk:framework_objc
out/mac-creation-tests/peerconnection_unittests \
  --gtest_filter='*CreationTransformer*' \
  --gtest_output=json:creation-transformer-tests.json
```

The local checkout had shallow dependency history; `build/util/lastchange.py`
warned and used fallback version metadata. A release pipeline must supply
correct version metadata, dependency/toolchain pins, all needed slices,
prefixes, and signing. A local successful build is not proof of byte-for-byte
reproducibility or release readiness.

tvOS framework binary SHA-256 at this checkpoint:
`dc74f89bffb5f5f580a52618b71621a42b22fe4b103bd1ff2d4281770c6a32ba`.
It has not been installed on Apple TV. The already-verified physical TV probes
used the published, unmodified LiveKit M144 framework, a different binary.

## Native test result

[Recorded targeted test output](2026-10-10-tests.json): 10 tests, zero failures,
zero errors, zero disabled cases, 9.860 seconds. The two factory tests check
Plan B rejection and callback identity/thread/media/direction. The eight media
cases combine modes 0–3 (ordinary, null sender factory, null receiver factory,
supplied identity transformers) with initial versus active-transport setup.
Active-transport cases check an open data channel, no prior RTP receivers, and
new audio/video receivers sharing that same DTLS object after negotiation.
The complete upstream suite was not run.

## Objective-C regression and external cryptor checkpoint

The macOS configuration now also exports Objective-C symbols, needed to link
external test applications against `WebRTC.framework`. This does not change the
creation-time callback's behavior. The macOS framework target is
`sdk:mac_framework_objc`; the Apple device target is `sdk:framework_objc`.

An allocated `NSString` containing `audio` or `video` exposed an existing
pointer-comparison bug in `mediaTypeForKind:`. Commit `4da73f2` compares string
contents. Its added XCTest exercises both sender and receiver capabilities for
both media kinds using strings with different object identities. The actual
upstream XCTest method passed locally (one test, zero failures):

```sh
python3 e2ee-experiment/run-factory-xctest.py
```

That script compiles the repository's XCTest source into a temporary macOS
bundle; it does not substitute a mirrored implementation. It runs only the
new method, not the full Apple test suite.

Framework SHA-256 after the capability fix:

- macOS: `ca91a6162da6e73ee7e212676aa4d267ca278b796ddacc811f927cdcd1104f9d`
- tvOS: `46edd9f59f5428ed05d9e9eb7e02857c2f4104d96cf5946e06f98583487ac2f8`

The separate TV review branch now contains an experimental Jitsi-compatible
Apple cryptor/controller and browser fixture under
`tvos-companion-rn/e2ee-harness/native/jitsi-m144`. The macOS native controller
passes 11 direct-browser stages with simultaneous VP8 and Opus, using unchanged,
hash-verified Jitsi Context code and external AES-128/index-zero keys. The same
native fixture compiles and links for tvOS 17 arm64; it has not been installed.
This is not JitsiConference/JVB, automatic key exchange, an M144 React Native
bridge test, or physical-TV media validation. The cryptor remains outside this
WebRTC fork and is not built into these framework binaries.
