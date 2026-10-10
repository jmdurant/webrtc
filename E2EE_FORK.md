# M144 creation-time E2EE development

This branch is an experimental, opt-in frame-transformer integration for native
WebRTC. It is not a production E2EE release or a complete Jitsi SDK integration.

## Baseline

- Upstream: https://github.com/webrtc-sdk/webrtc
- Base commit: `30d5e63ae91da483e06577b5c35ee91cc5e5c3db` (`m144_release`).
- LiveKit Apple framework release: `144.7559.15`.
- Corresponding build recipe commit in `webrtc-sdk/webrtc-build`:
  `5c75bb9e7e558b80cda5dc8e9d07ec309ebe895f`.
- Development branch: `codex/m144-creation-time-e2ee`.

The upstream release branches remain available as comparison points. Keep native
source changes separate from React Native bridge and application patches. The
TV application's M144 bridge migration is maintained separately in
`app-flutter-openemr`, branch `codex/tvos-m144-review`.

## Proposed change

An optional `PeerConnectionDependencies` callback creates a frame transformer
for each audio/video sender and receiver during native construction. The callback
receives media type, endpoint ID, and direction. A supplied callback returning
null installs a transformer that drops frames. Omitting the callback preserves
ordinary media behavior. Plan B rejects the optional callback.

The callback runs synchronously on the signaling thread. It must not block on
JavaScript or reenter the peer connection, and should return a distinct
transformer for each endpoint. The Objective-C native factory exposes this hook.
Later replacement or removal of transformers requires separate enforcement.

This is an attachment mechanism, not a cryptographic implementation, key
exchange protocol, or assertion of interoperability with stock Jitsi.

## Validation status (2026-10-10)

The published, unmodified M144 Apple framework passed physical Apple TV H.264
plaintext and synthetic encryption probes. Missing/wrong keys and disabled
cryptors blocked the expected frames; restoring matching keys/enabled cryptors
restored reception. Those probes do **not** validate this source patch.

The creation-time hook now builds as an arm64 tvOS framework and macOS test
executable. Disabling Clang modules/custom libc++ and using bundled LLD resolved
the Xcode 27 SDK/header/linker compatibility errors. The local configurations,
toolchain details, and unsigned framework hash are in
[e2ee-experiment](e2ee-experiment/README.md). No patched framework has been
installed, and no release artifact is published here.

All 10 targeted native tests pass. They cover Plan B rejection, per-endpoint
callback invocation, ordinary media, null-factory frame dropping, and supplied
identity transformers. Media tests exercise both initial negotiation and adding
audio/video after a data channel is open. They assert that new receivers reuse
the already-connected DTLS transport. In the null-factory cases, absolute
received frame counts remain zero through negotiation and a two-second
observation window. Identity controls prove frames traverse all four
audio/video sender/receiver transform paths. These are attachment/media tests,
not cryptographic or full test-suite results.

Run the targeted suite with:

```sh
out/mac-creation-tests/peerconnection_unittests \
  --gtest_filter='*CreationTransformer*'
```

## Before release or upstream submission

1. Turn the local build checkpoint into a release-quality reproducible pipeline
   with correct metadata, ABI/prefixes, required slices, and artifact validation.
2. Extend attachment coverage to further renegotiation, replacement, teardown,
   and failure cases, and review the synchronous factory API for upstream use.
3. Validate key installation, revocation, replacement, close, and recovery with
   actual cryptors; prove no unencrypted media escapes during transitions.
4. Integrate the React Native bridge and Jitsi lifecycle separately, including
   interoperability with Jitsi's key derivation and frame format.
5. Test the resulting framework on Apple TV and mobile devices, including
   ordinary calls, E2EE calls, reconnection, and live server interoperability.

Do not enable required E2EE based only on the stock-framework loopback probes.
Keep the upstream API/test proposal small and separate from local build
workarounds and application-specific integration.
