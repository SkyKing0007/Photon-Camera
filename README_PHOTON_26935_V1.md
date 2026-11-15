# PHOTON 26935 V1 — ONE THREE-STAGE vscode.dev handoff

**READ BEFORE UPLOADING:** This ZIP is source + guarded Actions only; it is NOT an APK and NOT a device test. This is **PREPARED FOR ACTIONS**, never BUILD-PROVEN until a new Actions job succeeds and publishes the APK and source TAR.

## STRICT SEQUENTIAL UPLOAD — NO LOCAL SCRIPT COMMANDS

1. In **vscode.dev** on `experimental-clean-photon-rebuild`, upload the *contents* of **STAGE_1_UPLOAD/** into the repository root, retaining the nested paths exactly. Verify the stage-1 paths against `26935_V1_STAGE_1_UPLOAD_PATHS.txt`. Do not run any Python or shell yourself.
2. Upload the *contents* of **STAGE_2_UPLOAD/** next. It contains the complete `/.github/workflows/build-26935-change-aware.yml`. Verify against `26935_V1_STAGE_2_UPLOAD_PATHS.txt`. No source build or trigger yet.
3. Upload **STAGE_3_UPLOAD/TRIGGER_26935.txt** last. This activates the new workflow after the staged files have landed. If your browser stages all changes in a single commit, verify that all three are present before committing; no trigger-only partial commit. Use `26935_COMMIT_MESSAGE.txt` as commit message.

The **user** decides when to commit. The assistant did not commit or push anything, did not change `dev`, and did not upload an APK.

## Runtime authority — pinned, not repository source

- Repository: `SkyKing0007/Photon-Camera`, target branch `experimental-clean-photon-rebuild`.
- **26934** successful Actions run `43655649685`; commit `f206f5f0eb23f8a64e88c82abdbe8df362b99230`.
- Artifact ID `14138156573`, exact ZIP SHA-256 `011e7c9f225e142a7a04f589c6548832eb544dfb8e9b722c69b4166768ecee17`.
- Official compiled candidate TAR SHA-256 `fdc9d7d9335ea27ee9858760a7db8225240a49574481e7228b54d27dd671cd13`.
- Official executed builder SHA-256 `345d34aaa45b23c4e6b0ebc7756387478644c9b098ba4ef3493ab9b344bf2116`.
- Official executed workflow SHA-256 `3cb9871bfd2619361e6858758f36035abca2550516a1fbc0c4b39629599494ea`.
- 26934 APK SHA-256 `8d7348e7e58ee00cee42ef2a32fe3b0cfb0161e2564286f4aba994fc1555f865`.
- Exact 26934 source index: **2048**. 26935 expected: **2050** = **6 modified existing + 2 newly added**; **2042 protected** copied byte-identically from the actual successful 26934 compiled source.

## Changes — B with Super Res ON only

- Immutable per-shot owned `Iris26935BOnSession` and relay; verifies actual nonempty `.jpg/.jpeg`, or frozen HEIC `.heic/.heif` when HEIC was selected, after the successful saved callback before allowing shutter release. DNG and duplicate/out-of-order finish events cannot release the new shot.
- B/ON-only Motion processing lifecycle arm/release; native failure, no output and executor rejection cleanly terminate; no duplicated/deferred capture. Shutter is visibly grey alpha 0.38 and disabled while busy. Pending UI callbacks are generation guarded; fragment pause/resume rebinds without retaining the dead Activity.
- MainRenderer records slow synchronous `iris26872Probe` stalls and *only* during measured B/ON processing, bright light **with inactive anti-stripe compensation** permits a maximum 1–2 frame coalescing. Exact Camera2 timestamp exposure matching, anti-flicker-active/low-light probes and all original reconstruction remain unchanged. GPU scheduling remains shared; this is not a guaranteed 60fps hardware fix.
- No `RawLens` native math/worker/thread count changes. Original 15 RAW frames, true 6144 × 8192 / 50MP, LKR T=3 and steps=2, clipped highlight 26934 smooth white, Experiment A/B OFF, UHDR, DNG, Night, LONG, HEIC, Spektra, JNI/vendor and 5 shaders remain unchanged.

## Actions safety contract

The original successful **26934** historical verification block is preserved as the exact **141** ordered executable commands (SHA-256 `bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b`) — including 26886/26887, 26903, 26904 V1 optimizer/V2 CMake/V3 gates and 26916–26934. Do not weaken any check. 26935 also seals all 2050 source paths, 2042 protected full-index SHA, fails closed under eight mutations, compiles real Java session/relay through `javac`, verifies source ownership, replays actual `git apply` forward and rollback at 7/12/40 using 26934 compiled source; protects exact 26934 shaders. Original two-ABI RawLens libraries are reused from the **successful published 26934 APK**, SHA/ELF/JNI verified; no external GitHub RawLens release API HTTP 403 fallback.

Mandatory Actions order: seal and historical tests → authenticate ONLY successful 26934 published artifact → recover full successful compiled source and overlay exactly eight paths → safety/host/source/patch checks → exact cache provenance → pinned real glslang 16.5 ESSL300/310 / `spirv-opt` / `spirv-val` → original JNI/NDK dual ABI CMake proof → real Kotlin/Java compilation + `:app:assembleDebug` → exactly one APK + full compiled source TAR with builder/workflow SHA receipt and publisher proof. Abort on any missing gate.

## Verification authority and limits

`26935_LOCAL_VERIFICATION.txt` states local checks actually run and unsupported operations. **Full Android Kotlin/Java application + NDK/CMake + real pinned GLSL/SPIR-V + APK assembly are required by Actions; they cannot be marked PASS locally without the corresponding compilers and Android SDK**. New 26935 APK SHA only exists after Actions success; do not confuse the 26934 SHA above with 26935.

**Device preview responsiveness, exposure/stripe correctness under real flicker, image quality and shutter interactions remain NOT RUN until on-phone testing.** After the new APK is published, review its motion trace, synchronized preview frame intervals, per-frame GPU readback wait, shutter UI lock/unlock and 50MP sample outputs. The hardware GPU remains shared between GLES preview and Vulkan LKR; this handoff makes no unproven absolute smoothness claim.

## Scope and integrity inventory

- `26935_BASE_26934_FULL_APP.sha256`: exact 2048 prior source.
- `26935_EXPECTED_FULL_APP.sha256`: exact expected 2050 new source.
- `26935_PROTECTED_SOURCE.sha256`: exact protected 2042.
- `26935_CHANGED_RUNTIME_ALLOWLIST.txt`: 6 modified.
- `26935_ADDED_RUNTIME_PATHS.txt`: 2 added.
- `26935_HANDOFF_HASHES.sha256`: full sealed staged files.
- `26935_FORWARD_FULLINDEX.patch` + `26935_ROLLBACK_FULLINDEX.patch`: deterministic changes and direct reverse.
- `26935_V1_STAGE_{1,2,3}_UPLOAD_PATHS.txt`: exact three-stage upload list.
- `26935_EXPECTED_ACTION_EXECUTABLES.txt`: exact executable workflow references.

**Infrastructure diff:** new 26935 workflow/trigger/builder/validators/manifests; original successful 26934 historical stage commands unchanged; no `dev` or application Gradle/CMake/vendor changes. One existing 26934 historical workflow is not deleted or overwritten. No APK and no private files included.
