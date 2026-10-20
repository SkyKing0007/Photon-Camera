PHOTON 26862 — VSCode.dev upload handoff (one intended Actions workflow).

Branch: experimental-clean-photon-rebuild only. No backup branch.
Authority: successful 26861 Actions 39490397467, SHA 999369b2ba8d683cfc333983d6f1b410ccbdac2c,
artifact 12295192965, SHA256 b5e3db77f93c32c8307cd11b891d9c7ff610e6a03cec1c24405abefa2af8ad18.
Mechanics: exact successful 26861 17-stage build; exact script provided as checked reference.

Upload the ZIP's relative paths to the repository root using vscode.dev, preserving directories.
DO NOT replace or directly edit live app/src or app/version.properties: Actions owns frozen candidate transform.
Confirm only the intended new files in 26862_INFRASTRUCTURE_CHANGED_PATHS.txt appear as changes,
then commit/push to experimental-clean-photon-rebuild; the TRIGGER_26862.txt path launches only this build.
NO user local script execution, backup branch, or APK uploads.

B-only change: RAW-burst measurement independent of flicker/EV metadata veto;
chronological frame pairs and actual shutter/ISO-based radiometric normalization;
row-mean detrending, bounded spatial same-phase RAW variance if full fit not identifiable;
strict 4-phase RAW-only B, zero Camera2 fallback. A/DNG/LONG/UHDR/flicker/EV protected.

This is PREPARED / UPLOAD-READY only after local gate replay reports PASS.
Real project Kotlin/Java/GLSL/NDK/full assemble: NOT RUN in this environment.
Do not call build proven until new Actions run succeeds and its artifact is verified.
