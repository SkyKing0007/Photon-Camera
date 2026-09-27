PHOTON 26719 — HIGH-ZOOM LAZY ISOLATION

Upload to the repository root on branch experimental-clean-photon-rebuild, preserving paths.
Do not upload this ZIP itself.

STEP 1
Upload every path listed in 26719_UPLOAD_PATHS.txt EXCEPT:
.github/workflows/build-26719-high-zoom-lazy-isolation.yml
Commit message:
26719: prepare high-zoom lazy isolation

STEP 2
Upload only:
.github/workflows/build-26719-high-zoom-lazy-isolation.yml
Commit message:
26719: activate high-zoom lazy isolation

The new workflow does not exist before step 2, so step 1 cannot launch an incomplete 26719 build.
No backup branch is required or created.
