PHOTON 26763 — NEUTRAL/CFA OWNERSHIP ADMISSION VETO

Branch: experimental-clean-photon-rebuild
No backup branch. Do not upload or commit an APK.

IMPORTANT: This is a NEW workflow, so use the normal two-stage root upload exactly once.

STAGE 1 — GitHub repository root
Upload/replace every file/folder from this handoff EXCEPT:
  .github/workflows/build-26763-neutral-cfa-ownership-veto.yml
Preserve folders exactly, including handoff_payload_26763/.
Commit and push:
  26763: prepare neutral CFA ownership veto
No 26763 Actions run should start yet.

STAGE 2 — workflow only
Upload:
  .github/workflows/build-26763-neutral-cfa-ownership-veto.yml
at the exact repository path .github/workflows/.
Commit and push:
  26763: trigger neutral CFA ownership veto build
This commit should launch only Build 26763 Neutral CFA Ownership Veto.

Runtime authority:
  successful 26762 run 37217481610
  commit d7f8fdc75f8360244d359ea0568ec499288aecce
  artifact 11309181086 photon-26762-per-lens-chroma-controls
  artifact SHA-256 771138d83a8f500db1c344a94a9643dbd133bbec6340783464eea81aa3fb79fd
  candidate tar SHA-256 6129399df70901555310c2820d6a69e2de342f515d15b7076dd8b7babe1a04e5

Verification mechanics authority:
  successful 26752 commit 69d5cb14f950d6fe5309441f7abf29d96631ab02
  run 37075896367 / artifact 11256842407

Runtime scope: exactly 2 existing files; 0 additions; 0 deletions.
26762 settings, transport, denoise controls and compiler repair remain byte-identical.

Before Actions succeeds, 26763 is prepared/upload-ready only. GitHub Actions is authoritative for pinned real GLSL, Kotlin, Java, NDK, full assemble, one-APK proof, and post-build invariance.
