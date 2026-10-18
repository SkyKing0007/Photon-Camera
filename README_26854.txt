PHOTON 26854 — GUARDED ACTIONS CHECKOUT SCOPE REPAIR
Branch: experimental-clean-photon-rebuild ONLY. No backup. Do not edit dev.

This small ZIP has exactly THREE upload stages. No APK, compiled candidate, or generated GLSL files are included.

IMPORTANT: You DO NOT need to delete glsl_static manually. The existing GitHub branch
contains 50 previously uploaded generated shaders. The Stage 2 workflow contains a
new, hash-guarded preflight which confirms that exact set and removes ONLY those
files from its temporary Actions checkout/index. It does not push or commit any
changes to the GitHub branch. It will fail if any path, count, or byte differs.
The historical files remain on the GitHub branch until a separately approved
cleanup commit; they do not become part of the compiler-tested runtime candidate.

STAGE 1 — ROOT FILES ONLY
Upload the CONTENTS of STAGE_1_ROOT_FILES/ to the GitHub repository ROOT.
Do not upload the enclosing Stage folder. Do NOT upload generated glsl_static.
Commit/push: 26854: prepare guarded Actions GLSL cleanup

STAGE 2 — WORKFLOW YML ONLY
Upload the SINGLE FILE from STAGE_2_WORKFLOW_ONLY/ to the exact path:
.github/workflows/build-26854-cfa-noise-correction.yml
Commit/push: 26854: install hash-guarded Actions checkout preflight

STAGE 3 — TRIGGER FILE ONLY
Upload the SINGLE FILE from STAGE_3_TRIGGER_ONLY/ to repository root:
TRIGGER_26854.txt
It contains a NEW retry suffix relative to the previous failed run.
Commit/push: 26854: trigger guarded checkout repair build

Only Stage 3 should launch the intended Actions run.

WHAT IS VERIFIED LOCALLY:
- Runtime authority: successful 26853 compiled candidate, exact 1,786 app files.
- Runtime scope: exactly GlesMgcRawSabreShaders.kt, GlesMgcRawSpatialStacker.kt,
  and app/version.properties; 1,783 protected app files byte-identical.
- The 17 named inherited verification stages and real compiler commands remain ordered.
- One intentionally audited workflow preflight occurs BEFORE the 17-stage runner.
- 50 accidental historical generated files are matched by path AND SHA-256,
  removed from temporary index only, with all other historical paths rejected.
- Forward/rollback patches are proven at core.abbrev 7, 12, 40, fuzz=0.
- Real pinned GLSL, Kotlin, Java, native, full assemble and post-build invariance
  are NOT RUN locally. GitHub Actions alone proves the build.

Never copy the outer ZIP into the repository, push APKs, or modify live app/src.
