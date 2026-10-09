PHOTON 26793 — SABRE SAME-LOCATION CFA COLOR

STATUS BEFORE ACTIONS
PREPARED / UPLOAD-READY only after the included clean-extract replay passes. Real GLSL/Kotlin/Java/NDK/full assemble are intentionally performed by GitHub Actions.

AUTHORITY
Runtime: successful 26792, commit 46c5cd4b4fd1ae28b4394a2e2388edffb276a85a, Actions run 37877930275, artifact 11592844879.
Verification mechanics: exact successful 26792 17-stage procedure, inheriting root 26752 mechanics unchanged.
No backup branch. No source commit/push has been performed by ChatGPT. No APK is included in this handoff.

RUNTIME SCOPE
Exactly 2 modified runtime files, 0 added, 0 deleted:
1. app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt
2. app/version.properties
Version: 0.9726793 / 26793.

PURPOSE
At the first Sabre CFA->RGB construction point, reconstruct R-G and B-G using green predicted at the same physical CFA site with the existing Sabre covariance, then recompose RGB while preserving legacy Sabre luma. The same correction is applied to the physically-authorized SHORT RBF. Night inherits the shared Sabre path. Super Res continues using native Sabre/VGN as its sole chroma guide; direct-CFA SR detail is untouched.

FROZEN
LCA/neutral scalar producer, guide/covariance, alignment/rejection, temporal weights, VGN, residual denoise, protected chroma floor, DNG, SDR/UHDR, native/vendor, and Super Res detail are unchanged.

VSCODE.DEV DELIVERY
Upload/replace the ZIP contents at repository root on experimental-clean-photon-rebuild, commit once, and push once. Only TRIGGER_26793.txt is watched by the 26793 workflow, so that push launches the intended build. Do not upload an APK.

After Actions succeeds, the new Actions artifact becomes runtime authority only after its compiler/build/invariance proofs are verified.
