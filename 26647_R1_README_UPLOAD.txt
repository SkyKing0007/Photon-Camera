PHOTON CAMERA 26647 R1 — DIRECT FINAL SHORT FUSION + HEIC DISPLAY-P3 CONTRACT

Upload/replace every path listed in R1_26647_UPLOAD_PATHS.txt into the repository root on branch experimental-clean-photon-rebuild, commit once, and push once.
Do not upload or commit any live app/src replacement directly; the sealed handoff reconstructs the exact candidate from the successful 26646 Actions compiled-candidate artifact.
Do not modify dev.

Runtime authority:
  successful 26646 R1 commit 19003161060180e61354e23051308b1798f917b9
  Actions run 35021453792
  artifact 10418400144
  artifact SHA-256 7e1e2c56c7b3d6aa309aa7ea67b867efaa3aae1fbd679d816cf4a4e64f492e2f
  compiled-candidate TAR SHA-256 74446096c1113480ba0b8e0c2b0efc56ebaf77f4fef508bac94dab97ea93fc25

Verification-mechanics authority:
  exact successful 26646 R1 compiler/native/patch/PRE-BUILD/assemble/postbuild order
  build-script blob 10e22181cb4964af845d637ab62878f988628571
  workflow blob a1326ea24920fbd60daef953bf3d129a1546fe9f

Runtime scope:
  exactly 5 changed files, 0 additions, 1715 protected files unchanged.
  See R1_26647_RUNTIME_CHANGED_PATHS.txt.

Local status:
  candidate reconstruction/ownership/regressions/manifests/static runtime-expanded GLSL/patch determinism are packaged for replay.
  Real pinned glslang 16.5.0, Kotlin, Java, both NDK ABIs and full assemble are intentionally GitHub Actions gates and must not be claimed before Actions passes.

Target: 0.9726647 / 26647
Backup: none created/requested.
