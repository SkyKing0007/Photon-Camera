PHOTON 26696 SPEKTRA RUNTIME PARITY — TWO-STAGE VSCODE.DEV HANDOFF

Runtime authority: successful 26695 Actions compiled candidate, commit 2502da697abfc243819f208714cba9ee6c646e06, run 35947529069, artifact 10787318407.
Targeted rollback reference: exact successful 26694 compiled candidate, run 35943631402, artifact 10785824126, used only to restore the 3 device-rejected 26695 Spektra runtime files before applying 26696.
Verification mechanics authority: exact successful 26695 build/workflow; compiler/build stage order unchanged.
Backup: NONE, per user request.
Runtime scope: exactly 9 paths (8 modified + 1 added); all runtime bytes are carried only inside handoff_payload_26696.
Infrastructure delta: 26696 identity/scope/regression wrappers plus explicit second artifact input for the compiled-26694 targeted restore; no compiler/build-order change.

STAGE 1
Upload every file/folder from this handoff EXCEPT:
.github/workflows/build-26696-spektra-runtime-parity.yml
Commit message: 26696 payload and proofs

STAGE 2
Upload only:
.github/workflows/build-26696-spektra-runtime-parity.yml
Commit message: 26696: activate Spektra runtime parity build

Do not upload APK files. GitHub Actions is the real compiler/build authority.
