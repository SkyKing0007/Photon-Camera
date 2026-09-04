PHOTON 26594 V1 REGION-ANCHORED SHORT HIGHLIGHT HANDOFF

STATUS AT DELIVERY: PREPARED / UPLOAD-READY ONLY. NOT BUILD-PROVEN UNTIL GITHUB ACTIONS PASSES.

Runtime authority:
  successful 26593 V1.1 commit 7c485416a8f41f9bf8a834bf4282e7c2318fa9fb
  Actions run 33835148507 / job 100906020593 / artifact 9923084840
  artifact SHA-256 86e721369861a69b3237ff85bf1f2198f8c8cf3d1bfd8ad3d7cd06900c968bc1
  compiled-candidate tar SHA-256 104a9e4fe55f34087458eeb69913c6a55b2298898ba97080cefce6415e0a2f11

Verification mechanics authority:
  successful 26593 V1.1 build procedure. 26594 preserves its candidate-first ordering and
  compiler/build sequencing; verify_26594_v1_infrastructure.py pins the exact successful script
  and workflow SHA-256 and Actions re-fetches them from the authority commit before runtime writes.

Runtime changed-file allowlist (exactly 3):
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
  app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
  app/version.properties

Change:
  replace the circular per-clipped-pixel NORMAL-radiometry/coverage proof with a GPU-only,
  region-anchored SHORT handoff. Bright but still measurable NORMAL/SHORT overlap establishes
  radiometric seeds. Trust propagates only through connected highlight cells that independently
  pass the existing SHORT Sabre flow/rejection/unblocker/headroom gates. Final native-resolution
  replacement remains one whole-RGB scalar and keeps the existing 0.90 -> 0.98 saturation handoff.

No backup was created by explicit user request. No APK is contained in this handoff.
Upload/replace the contents at repository root on experimental-clean-photon-rebuild, make one clean
commit directly on 7c485416a8f41f9bf8a834bf4282e7c2318fa9fb, and push. GitHub Actions is authoritative.

Packaging correction: fixes the Actions-only verify_scope embedded-Python escaping failure; runtime candidate is byte-identical to 26594 V1.
