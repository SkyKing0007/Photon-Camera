PHOTON CAMERA 26648 R1.1 — COMPILER REPAIR — UNIVERSAL NORMAL+SHORT FUSION + HEIC HDR + CONTRAST-SAFE MANUAL UI

Upload/replace every path listed in R1_1_26648_UPLOAD_PATHS.txt into the repository root on branch experimental-clean-photon-rebuild, commit once, and push once.
Do not upload or commit any live app/src replacement directly; the sealed handoff reconstructs the exact 26648 candidate from the successful 26646 Actions compiled-candidate artifact.
Do not modify dev. No backup is required or created.

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

Repair note:
  26648 R1 failed the pinned real glslang 16.5.0 gate because universalNormalShortFusion26648 declared uShortExtractedBayer but four copied helper accesses still referenced undeclared uExtractedBayer.
  R1.1 changes only that shader-symbol defect plus verification/packaging proof. A permanent undeclared-uXxx regression now fails before the compiler.

Repository lineage note:
  branch currently contains rejected 26647 handoff commit 3d9851e030cededc038e3a1a3287460c916c9e9d.
  That commit is proven handoff-only and contains no live app source. 26648 does NOT inherit 26647 runtime bytes; runtime is reconstructed from exact successful 26646 compiled-candidate authority.

Runtime scope:
  exactly 8 changed existing files, 0 additions, 1712 protected files unchanged.
  See R1_1_26648_RUNTIME_CHANGED_PATHS.txt.

Architectural target:
  NORMAL temporal reconstruction + aligned/exposure-normalized SHORT -> one scene-independent scalar-RGB radiometric fusion owner -> one fusedExtendedLinear HDR master before Resolve/VGN.
  SHORT is excluded from NORMAL temporal/noise support, DNG accumulation and true2x high-frequency detail. Clipped SHORT CFA samples are removed individually; exact undilated physical rejection support and local affine flow residual gate SHORT. No gradient requirement, blurred HDR mask, dilation, spatial fill, border extrapolation, grey rescue, cross-edge propagation, or per-channel exposure switching.
  HEIC preserves 26646 gain-map/tmap/ISO21496 architecture while matching hardware HEVC and HEIF base color signaling and numerically proving saved-file gain-map reconstruction.
  Manual controls remain pure white with dark edge/shadow only; no background/pill/scrim. This includes the chevron, four bottom manual labels/icons, and dynamically drawn Auto/numeric knob values.

Local status:
  deterministic candidate reconstruction/ownership/regressions/manifests/runtime-expanded GLSL static gates/patch proof and clean handoff replay are packaged for local prebuild.
  Real pinned glslang 16.5.0, Kotlin, Java, both NDK ABIs and full assemble remain GitHub Actions authority and must not be claimed before Actions passes.

Target: 0.9726648 / 26648
Backup: none created/requested.

R1.1 status: repaired shader static gates pass locally; pinned real glslang/Kotlin/Java/NDK/full assemble remain authoritative Actions gates unless explicitly recorded otherwise in the final handoff report.
