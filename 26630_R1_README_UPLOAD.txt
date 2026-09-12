PHOTON 26630 R1 — FRESH ADAPTIVE COLOR / FIXED POLICY / UHDR UNITY HANDOFF

Runtime authority:
  successful 26629 R1 commit fe1b6953fa1546f19a23c67bce55e49de15c7ac6
  Actions run 34659969391
  artifact 10287765040 (photon-26629-r1-luminance-locked-color-uhdr)
  exact compiled-candidate TAR SHA-256 51d61d1c8e13ef624939da053ff0fb41203dc5903bb21de143a69e1035d739fe

Verification-mechanics authority:
  exact successful 26629 R1 sequence. No build-order, compiler, NDK, patch, PRE-BUILD,
  assemble, one-APK, authority-seeding, or post-build invariance mechanic is intentionally changed.

Backup: NONE (localized runtime correction).
Runtime candidate delta: exactly 13 paths in R1_26630_RUNTIME_CHANGED_PATHS.txt.
Infrastructure mechanics delta from successful 26629 R1: ZERO; package identity and 26630 semantic validators only.

Behavior:
  - Adaptive V5 final luminance-locked color presentation.
  - existing per-lens Iris Saturation becomes the Motion user colorfulness owner.
  - VGN fixed at 1.0; old VGN setting removed as an active authority.
  - viewfinder-match response fixed at 65%; old setting removed as an active authority.
  - Night receives neutral saturation 1.0 and cannot inherit Motion per-lens saturation.
  - 1x/true2x CPU/true2x GPU publication equations are kept parallel.
  - Motion UHDR gain remains exact unity through sourceGuide <= 1.0 + 1e-4; true headroom above that resumes gain.

UPLOAD:
  Extract this ZIP and upload/replace its contents at repository root in vscode.dev on
  experimental-clean-photon-rebuild. Do not upload an APK. Commit once and push once.
  The 26630 workflow must be the only intended build trigger for this handoff.

Local preparation status is recorded in the included verification report generated before ZIP sealing.
GitHub Actions remains authoritative for pinned glslang 16.5.0, Kotlin, Java, both NDK ABIs,
full :app:assembleDebug, exactly-one-APK proof, post-build invariance, and final compiled candidate export.
