Photon 26866 — THREE vscode.dev commits; NO backup branch
Branch: experimental-clean-photon-rebuild
Runtime: SUCCESS 26865 run 39719781362, commit 7e5999c6ba20e31f56b9c599ce43018ff6eb915b, artifact 12400363326 (SHA a3d2899bd6765872e12efd7303ca4e7c927603cea2f907cf4dfab15c9b831647).
Mechanics: successful 26865 build_26865_iris_rawr.sh Git blob 3d88fddca9eeb2aa9c98f63e6fe2ac91bd65bd9c, exact same 17-stage order and compiler commands.

1. Upload CONTENTS of STAGE_1/ into repository ROOT preserving folders. Commit "26866 stage 1: B sensor clip smooth-white no Iris chroma".
2. Upload STAGE_2/.github/workflows/build-26866-iris-smooth-white.yml into .github/workflows/. Commit "26866 stage 2: inherited guarded Actions".
3. Upload STAGE_3/TRIGGER_26866.txt into repository ROOT. Commit "26866 stage 3: trigger guarded build".
Push the three commits together to experimental-clean-photon-rebuild. Do not push APKs. GitHub Actions compiles and proves runtime; BEFORE successful Actions, PREPARED/UPLOAD-READY only.
