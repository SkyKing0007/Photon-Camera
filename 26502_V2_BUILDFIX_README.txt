26502 V2 BUILD-PROCEDURE FIX (runtime math unchanged)

WHY V1 FAILED
GNU patch emitted src/main/java/.../MotionV2CfaReconstruction.java.orig when the 26502 patch applied with a physical mismatch/offset. The strict delta gate correctly rejected that temporary backup file.

BEFORE UPLOADING THESE FILES
Create backup branch:
  backup-26502-v1-before-buildfix-20260818
from exact commit:
  4e9971ec70abeb6533e675dc1bb3509d46af552f

REPLACE/ADD IN REPOSITORY ROOT
REPLACE: build_26502_stack_aware_chroma_highlight.sh
REPLACE: 26502_HANDOFF_HASHES.sha256
REPLACE: .github/workflows/build-26502-stack-aware-chroma-highlight.yml
ADD:     26502_v2_buildfix_prechange.patch

DO NOT REPLACE THE 26502 RUNTIME PATCH OR VALIDATOR; V2 DOES NOT CHANGE IMAGE PROCESSING.

COMMIT MESSAGE
26502 V2: harden patch application against backup artifacts

WHAT CHANGED
- All three patch applications use --fuzz=0 --no-backup-if-mismatch (plus --batch --forward).
- Explicit gates reject any .orig or .rej after each patch and again before real GLSL/Java preflight.
- V2 requires the pushed 26502 V1 commit to be frozen on backup-26502-v1-before-buildfix-20260818.
- The strict two-runtime-file 26502 scope assertion remains unchanged.
- Version remains 0.9726502 / 26502 because V1 never reached version bump/build and runtime math is byte-identical.

EXPECTED APK
IrisCamera-0.9726502-26502-stack-aware-chroma-highlight-debug.apk
