PHOTON 26696 R1 SPEKTRA RUNTIME PARITY — COMPILER-CLOSURE REPAIR — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26695 Actions compiled candidate, commit 2502da697abfc243819f208714cba9ee6c646e06, run 35947529069, artifact 10787318407.
Targeted rollback reference: exact successful 26694 compiled candidate, run 35943631402, artifact 10785824126, used only for the same 3 device-rejected 26695 Spektra runtime files before applying 26696 R1.
Verification mechanics authority: exact successful 26695 build/workflow; compiler/build stage order unchanged.
Failed-run regression authority: 26696 run 35957174533, Java compile failure in byte-protected dormant SpektraCameraOwner caused by missing legacy two-argument SpektraExposureController.update overload.
Backup: NONE, per user request.
Runtime scope: exactly 9 paths (8 modified + 1 added), identical allowlist to intended 26696. R1 changes only SpektraExposureController.java relative to failed 26696, adding source compatibility for the dormant compiled caller; active four-argument AE path remains mandatory.
Infrastructure delta: R1 identity/scope/regression wrappers; exact successful 26695 compiler/build order unchanged. New R1 names intentionally do not match the already-active failed 26696 workflow path filters.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26696r1-spektra-runtime-parity.yml
Commit message: 26696 R1 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26696r1-spektra-runtime-parity.yml
Commit message: 26696 R1: activate Spektra runtime parity repair

Do not upload APK files. GitHub Actions is the real compiler/build authority.
