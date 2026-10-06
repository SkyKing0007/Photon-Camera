26772 R4 STRICT MECHANICS REPAIR — TWO-STAGE VSCODE.DEV UPLOAD

IMPORTANT: R4 is infrastructure-only relative to R3. Do not edit app/src.

STAGE 1
1. Be on experimental-clean-photon-rebuild.
2. Upload the CONTENTS of STAGE1_UPLOAD_TO_REPO_ROOT into repository root, preserving paths.
3. The workflow file is inside the hidden folder:
     .github/workflows/build-r4-26772-storage-ui-highlight.yml
   vscode.dev may hide .github. Make sure that exact path exists before committing.
4. Commit message:
     26772 R4: upload strict mechanics repair
5. Push.
6. NO R4 build should start from Stage 1 because the R4 workflow only watches TRIGGER_R4_26772.txt.

STAGE 2
1. Upload only TRIGGER_R4_26772.txt from STAGE2_UPLOAD_TO_REPO_ROOT to repository root.
2. Commit message:
     26772 R4: trigger strict mechanics repair
3. Push.
4. Expected workflow:
     Build 26772 R4 Strict Mechanics Repair

DO NOT edit the trigger before Stage 2. DO NOT edit runtime source. DO NOT rerun failed R3.
