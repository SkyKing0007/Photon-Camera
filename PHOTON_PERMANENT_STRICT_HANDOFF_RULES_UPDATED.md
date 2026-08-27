# Photon Permanent Strict Handoff Rules

**Purpose:** Permanent project reference for Photon Camera / Iris handoffs, compiler validation, runtime ownership, deterministic packaging, and regression prevention.

**Status:** Canonical workflow rule for future Photon Camera Development work.

**Backup branches protect architectural transitions, not every edit; small/localized changes use exact forward/rollback patches and hashes without creating another backup branch.**

---

## 1. Non-negotiable readiness rule

A handoff is **not ready** until every modified **active-path** component has passed the applicable real compiler:

- modified active-path GLSL → real pinned `glslangValidator`
- modified Kotlin → real project `:app:compileDebugKotlin`
- modified Java → real project `:app:compileDebugJavaWithJavac`
- final Android candidate → real `:app:assembleDebug`

Custom validators, regex checks, syntax balancing, marker checks, source-presence checks, isolated snippets, and transform success are **supplementary only**. They are never substitutes for the real project compiler.

If a real compiler cannot run in the current environment, that gate remains **NOT RUN / UNPROVEN**. Never describe the corresponding compiler or APK result as proven.

---

## 2. Runtime ownership must be proven before code modification

Before modifying a feature, trace the exact production path:

`production entry point → live owner/class → active program/shader/function → downstream consumer`

For every modified feature:

1. Prove the edited implementation is production-reachable.
2. Identify dormant, duplicate, legacy, fallback, or alternate owners.
3. Do not allow a dormant implementation to satisfy validation.
4. Confirm no later stage silently overrides or duplicates the same decision.
5. Prove the producer → carrier → consumer chain for any changed state, metadata, texture, noise quantity, exposure quantity, confidence map, or frame policy.
6. Verify Motion, Night, Photo, and shared ownership separately whenever relevant.

A source file being modified does **not** prove that runtime uses it.

---

## 3. Exact prior successful runtime authority

When the handoff system reconstructs or transforms a candidate from a previous successful artifact:

1. The exact prior successful candidate artifact is the runtime authority.
2. Verify its full file manifest and hashes.
3. Do not silently substitute repository `app/src` as runtime authority.
4. Reconstruct the candidate from the exact prior successful source/artifact and approved transforms.
5. Prove the resulting candidate is byte-identical to the expected runtime tree wherever unchanged.

If a future workflow intentionally changes this authority model, that change must be explicit and independently audited first.

---

## 4. Backup and rollback rule

Create a backup branch only before a meaningful architectural or high-risk runtime change, including changes to pipeline ownership, reconstruction/merge architecture, RAW or color-processing domains, exposure/frame policy, alignment architecture, Night/Motion routing, DNG/UHDR ownership, major shader algorithms, GPU lifetime/allocation architecture, or replacement/removal of a previously validated subsystem.

Do not create a new backup branch for small or localized changes, including compiler fixes, Kotlin/Java plumbing corrections, parameter/tuning changes, diagnostic instrumentation, UI/settings changes, slider additions, minor shader corrections, workflow/build-script fixes, validator changes, and narrowly scoped bug fixes.

A single backup branch may cover a sequence of closely related architectural revisions. Do not create redundant backup branches for compiler, handoff, or localized corrections within that same architectural change.

Before all runtime source modifications, regardless of backup requirement, preserve rollback safety using exact source hashes and canonical binary forward/rollback patches before source writes.

For Tier 3 non-runtime/non-critical changes, a backup branch and runtime patch are not required unless the change separately meets the architectural-risk rule.

Escalation: if a supposedly small correction changes pipeline ownership, frame/exposure policy, RAW/color domain, merge/reconstruction math, alignment architecture, Night/Motion routing, DNG/UHDR ownership, or GPU allocation/lifetime architecture, immediately treat it as architectural/high-risk and require a backup.

When uncertain, prefer no new backup unless the change could materially invalidate a proven pipeline design or would be difficult to reverse using the canonical rollback patch.

---

## 5. Temporary-copy / candidate-first rule

Never make the first experimental transform directly against the live source tree.

Required order:

1. Verify exact starting branch, HEAD, version, and runtime authority.
2. Apply transformations to a temporary candidate copy first.
3. Validate the candidate completely.
4. Generate canonical forward and rollback patches.
5. Prove forward application recreates the candidate exactly.
6. Prove rollback recreates the exact starting source exactly.
7. Only then allow controlled live-source writes in the build procedure.

---

## 6. Real GLSL compiler rule

Every changed shader that is active in production must pass the real pinned GLSL compiler.

This includes:

- standalone `.glsl` files;
- shaders assembled from templates;
- GLSL embedded in Kotlin/Java strings;
- generated GLSL;
- conditional variants that production can select.

Required checks:

1. Extract the exact shader text that production will compile.
2. Apply the exact production defines/version/profile needed for validation.
3. Compile with the pinned Khronos `glslangValidator` version used by the project.
4. Report the exact compiler result.
5. Keep static binding/type/resource checks as supplementary guards.

A structurally valid shader is not considered compiler-valid until real `glslangValidator` passes.

---

## 7. Real Kotlin and Java compiler rule

Any modified Kotlin/Java must pass the actual project compiler path.

### Kotlin

Run:

`./gradlew :app:compileDebugKotlin`

Explicitly guard against prior failure classes including:

- `Float` / `Double` mismatches;
- type inference;
- overload resolution;
- named arguments;
- nullable / non-nullable mismatches;
- visibility;
- scope;
- constructor signatures;
- unresolved references;
- wrong property/function ownership.

### Java

Run:

`./gradlew :app:compileDebugJavaWithJavac`

Explicitly guard against:

- missing imports;
- unresolved JDK/Android symbols;
- wrong exception types;
- method signature mismatches;
- wrong scope;
- stale variable names;
- wrong generic types.

A lexical parser or isolated `javac` snippet is useful supplementary evidence but is not a replacement for the real project compile.

---

## 8. Full Android build rule

After applicable language compilers pass, run the real Android build:

`./gradlew :app:assembleDebug`

A handoff is not an APK-proven handoff until this passes on the authoritative build environment.

If the current environment lacks the Android SDK/Gradle toolchain, explicitly report:

- `REAL GLSL COMPILE: PASS / NOT RUN`
- `REAL KOTLIN COMPILE: PASS / NOT RUN`
- `REAL JAVA COMPILE: PASS / NOT RUN`
- `FULL ANDROID ASSEMBLE: PASS / NOT RUN`

Never blur a custom contract test into a real compiler result.

---

## 9. Previous compiler/build failures are permanent regression tests

Every real compiler/build failure becomes a permanent regression test for later handoffs.

### 26543 failure lineage

#### 26543 V1 — GLSL compiler failure

A GLSL identifier escaped static/custom validation but was invalid for the real compiler because of a reserved-keyword conflict.

Permanent rule:

- compile every modified active GLSL shader with real `glslangValidator`;
- do not treat marker/static GLSL validation as proof of compilability.

#### 26543 V1.1 — nondeterministic Git patch representation

Patch generation depended on environment-sensitive Git abbreviation behavior.

Permanent rule:

- use canonical full-index binary patch generation;
- verify regeneration under multiple `core.abbrev` settings produces byte-identical patch output.

#### 26543 V1.2 — Kotlin type/scope compiler failures

Custom source/API checks failed to catch genuine Kotlin type-system and scope errors, including `Float` / `Double` and unresolved/scope issues.

Permanent rule:

- modified Kotlin must pass real `:app:compileDebugKotlin`;
- add targeted regression assertions for each discovered Kotlin failure class.

#### 26543 V1.3 — Java `ByteBuffer` symbol failure

The real Java compiler found:

```java
ByteBuffer source = plane.getBuffer().duplicate();
```

in `CaptureController.java` without an applicable `ByteBuffer` import.

V1.4 corrected only that line to:

```java
java.nio.ByteBuffer source = plane.getBuffer().duplicate();
```

Permanent rule:

- modified Java must pass real `:app:compileDebugJavaWithJavac`;
- Java symbol/import audits must explicitly cover previously failed symbols, including:
  - `ByteBuffer`
  - `FileOutputStream`
  - `Executors`
  - `AtomicInteger`

V1.4 changing only the fully qualified `ByteBuffer` symbol relative to V1.3 is the model for narrow compiler-only correction: do not alter unrelated runtime math or architecture while fixing a compiler defect.

---

## 10. Canonical deterministic patch rule

Generate patches canonically with:

```bash
git diff --binary --full-index --no-ext-diff
```

Do not depend on abbreviated object IDs.

Do not use environment-sensitive reverse patch generation as the canonical source of rollback.

Required proof:

1. Generate canonical forward patch.
2. Generate canonical rollback patch from the exact source/candidate pair.
3. Repeat patch generation with representative `git core.abbrev` values, including:
   - `7`
   - `12`
   - `40`
4. Require byte-identical output.
5. Apply forward patch with `fuzz=0`.
6. Require exact candidate equivalence.
7. Apply rollback with `fuzz=0`.
8. Require exact starting-source equivalence.

Patch determinism is part of handoff correctness.

---

## 11. Full authoritative-script replay

The authoritative build/handoff script is itself part of the test specification.

Before packaging a handoff, execute every locally reproducible pre-Gradle step **in the same order as the real script**.

Do not validate only the "important" transforms while skipping apparently minor guards.

This includes, when applicable:

- shell/Python/PowerShell syntax;
- historical/source reconstruction proof;
- complete transform chain;
- exact changed-file allowlist;
- whitespace/scoped-diff checks;
- every marker/grep proof;
- protected-file hashes;
- Java/Kotlin supplemental static checks;
- GLSL supplemental checks;
- ownership checks;
- dormant-owner rejection;
- memory/resource invariants;
- build/version proof;
- candidate/live equivalence;
- forward/rollback patch proof;
- all other pre-build safety gates.

A guard failure discovered in Actions that could have been reproduced locally is a process regression and must be added to the permanent replay.

---

## 12. Clean final-ZIP replay

After the handoff ZIP is finalized:

1. Extract it into a completely clean directory.
2. Use only files contained in that extracted ZIP.
3. Re-run all handoff file hashes.
4. Re-run transform syntax checks.
5. Reconstruct the candidate again.
6. Re-run runtime ownership validation.
7. Re-run compiler-contract validation.
8. Re-run all available real compiler checks.
9. Re-run version/build simulation.
10. Re-run canonical forward `fuzz=0`.
11. Re-run canonical rollback `fuzz=0`.
12. Require exact candidate/base manifests and hashes.
13. Verify workflow YAML and shell syntax.
14. Verify no unintended `.pyc`, `__pycache__`, or transient files are packaged.

A handoff that passed before ZIP creation but fails clean extraction is not ready.

---

## 13. Scope and regression protection

Before every code modification, compare the proposed change against:

- exact current runtime source;
- relevant earlier builds that introduced or fixed the same subsystem;
- known-good protected behavior;
- producer → carrier → consumer ownership;
- known failure modes.

Protect, unless intentionally replaced with evidence:

- stable Motion frame retention and reference ownership;
- ghost/duplicate-subject rejection;
- correct static-frame contribution;
- subpixel alignment/reconstruction behavior;
- highlight reconstruction behavior already proven;
- clean chroma improvements;
- fabric/denim/foliage/hair/text microdetail;
- correct brightness and exposure ownership;
- Night architecture and memory bounds;
- Photo/Night isolation where required;
- DNG handling;
- safe GPU resource formats/bindings/lifecycle;
- stable capture behavior.

Do not evaluate a fix in isolation.

---

## 14. Whole-system ownership audit

Before significant pipeline changes, explicitly answer:

- Who owns the quantity being changed?
- Who else can modify or respond to it later?
- What exact data domain is it in?
- Is the state mutable, cached, shared, or stale?
- What is recomputed downstream?
- Which producer writes it and which consumer reads it?
- Can GPU resources alias?
- Are formats/bindings compatible?
- Who creates and frees the resource?
- What happens on second/subsequent captures?
- What changes by physical camera/lens?
- What happens when Motion is inactive?
- What happens when a frame/result is missing or late?
- What happens at saturation, black floor, NaN/Inf, or precision limits?
- What evidence would falsify the proposed theory?
- What old controller must be retired or constrained if a new authority is introduced?

A local equation being correct is not sufficient. The full control loop must remain correct.

---

## 15. Night memory / ownership regression requirements

When Night code or shared capture ownership changes, preserve explicit checks for:

- Night production ownership;
- no accidental ZSL ownership where Night is intended to be independent;
- bounded RAW memory;
- no retained per-frame full-RAW duplicate/covariance structures beyond the intended design;
- no dormant owner satisfying validation;
- correct frame-count policy;
- correct reference and per-frame metadata ownership.

---

## 16. Version increment and build coupling

The build version increment and APK build belong in the same authoritative command/script block.

Before build:

1. verify current version/build;
2. apply intended increment;
3. prove the candidate reports the target version/build;
4. run applicable real compilers;
5. run `assembleDebug`.

Do not hand-edit version files separately from the controlled build procedure.

---

## 17. User workflow rule

For the user:

- provide one terminal command block at a time;
- scripts/files must be visible in the Explorer panel;
- do not ask the user to manually edit application source;
- do not use the user's machine as an incremental script-debugging environment;
- validate scripts end-to-end against the exact source before giving them to the user;
- do not modify or push `dev` unless explicitly approved;
- do not commit/push new source unless explicitly approved.

---

## 18. Required handoff summary format

Every future handoff summary must explicitly include:

```text
RUNTIME OWNERSHIP: PASS / FAIL / NOT RUN
DORMANT-OWNER REJECTION: PASS / FAIL / NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: PASS / FAIL / NOT RUN
CHANGED RUNTIME SCOPE: <exact file count and list>
REAL GLSL COMPILE: PASS / FAIL / NOT RUN
REAL KOTLIN COMPILE: PASS / FAIL / NOT RUN
REAL JAVA COMPILE: PASS / FAIL / NOT RUN
FULL ANDROID ASSEMBLE: PASS / FAIL / NOT RUN
FORWARD PATCH FUZZ=0: PASS / FAIL / NOT RUN
ROLLBACK PATCH FUZZ=0: PASS / FAIL / NOT RUN
CLEAN-ZIP REPLAY: PASS / FAIL / NOT RUN
TARGET VERSION/BUILD: <version / build>
```

If any applicable real compiler is `NOT RUN`, do not describe the compiler result as proven.

If `FULL ANDROID ASSEMBLE` is `NOT RUN`, do not describe the APK/build as proven.

---

## 19. 26543 V1.4 strict replay reference

The 26543 V1.4 replay is the canonical reference for this class of synthesized Actions handoff.

Its required proof pattern included:

- exact successful 26542 runtime authority;
- complete candidate manifest equality;
- exact changed runtime scope;
- V1.3 → V1.4 difference limited to `CaptureController.java`;
- Motion production ownership;
- Night production ownership;
- dormant-owner rejection;
- bounded Night RAW memory;
- no unintended retained full-RAW/covariance structures;
- GLSL structural/contracts;
- inherited real GLSL compile evidence when shaders were byte-identical;
- inherited real Kotlin compile evidence when Kotlin was byte-identical;
- new Java symbol/import checks;
- real JDK symbol validation;
- canonical forward/rollback patch regeneration;
- identical patch output across Git abbreviation settings;
- forward `fuzz=0` exact candidate recreation;
- rollback `fuzz=0` exact prior-source recreation;
- version/build simulation;
- final ZIP clean extraction;
- clean-ZIP hashes;
- clean-ZIP transform replay;
- clean-ZIP forward/rollback replay;
- workflow YAML/shell syntax;
- transient-file exclusion.

Important distinction:

V1.4 was **not** considered a proven Android APK/compiler handoff until the real Android project compiler and `assembleDebug` ran in Actions. Local evidence exhausted what was reproducible, but missing Android compiler gates remained explicitly unpassed.

That distinction is permanent.

---

## 20. Stop-on-ambiguity rule

Stop the handoff rather than assume correctness if any of these remain uncertain:

- runtime ownership;
- active versus dormant implementation;
- compiler behavior;
- Kotlin/Java type or scope;
- shader extraction;
- GLSL compilation;
- GPU binding/format/lifecycle;
- patch determinism;
- runtime reachability;
- exact base authority;
- rollback exactness;
- memory ownership;
- frame/metadata ownership.

A delayed handoff is preferable to a handoff falsely labeled as proven.

---

## Short permanent instruction

The following sentence should also remain near the top of the ChatGPT Photon Camera Development project instructions:

> **A handoff is not “ready” until modified active-path GLSL has passed real glslang and modified Kotlin/Java has passed the real project compiler; custom/static validators are never substitutes. Preserve prior compiler/build failures as permanent regression tests.**
