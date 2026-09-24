PHOTON 26694 — Spektra integration correction

Runtime authority: exact successful 26693 Actions compiled candidate
  commit ce1ebd051bc8708733afb8bba75909eb12138824
  run 35926194546
  artifact 10779656771 photon-26693-global-ui-spektra-lifecycle
  artifact SHA-256 a5c4d67a04a8ca442eaf81786e81041a85c8dd4bcbe42bbf52ff9703f22b5fa1
  candidate TAR SHA-256 3b67997d17a02093053ce7be78128f72f39a6f666b267a54e05b507b62bd5c68

Verification mechanics authority: exact successful 26693 build/workflow implementation; inherited successful compiler/build order unchanged.
Backup: NONE.
Runtime changed-file allowlist: exactly 7 files, 0 additions/removals.
Infrastructure delta: 26694 identity/scope/regression wrappers only; compiler/build ordering unchanged.

Two-stage vscode.dev upload (same style as 26693):
1) Upload every file/folder in this ZIP EXCEPT .github/workflows/build-26694-spektra-integration-fix.yml. Commit: 26694 payload and proofs
2) Upload only .github/workflows/build-26694-spektra-integration-fix.yml. Commit: 26694: activate Spektra integration correction build

26694 targets the observed 26693 device failures without changing the successful 26693 global UI geometry, native renderer, RCD/SPEKTRA processing, Photo histogram, or Spektra histogram presentation architecture:
- initialize the exact native exposure-meter carrier as CenterWeighted=0 at normalized center (0.5,0.5), fixing the accidental top-left (0,0) input that left sensor AE at the ISO-min reciprocal-rule startup pivot;
- keep the single active Unspektrawesome MediaStore publisher but publish Spektra JPEGs to DCIM/Camera;
- bridge active Spektra capture lifecycle into Iris's existing capture/progress/processing UI;
- pass the exact saved MediaStore Uri into Iris gallery thumbnail ownership;
- fail-contained shutter-admission race releases the UI;
- preserve 26693 histogram lifecycle; restored exposure distribution is expected to make it visibly responsive again.

Status before upload: prepared/upload-ready only. Real GLSL/Kotlin/Java/NDK/full assemble/APK/post-build gates run in GitHub Actions and must not be claimed before the run succeeds.
