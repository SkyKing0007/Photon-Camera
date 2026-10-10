PHOTON 26804 — PRE-VGN THIN-NEUTRAL RIDGE REPAIR

Runtime authority:
- successful 26803
- commit cc863465953221f52ecfe7b5d4221f5f2a35a308
- Actions run 38076222673
- artifact 11679366034
- artifact SHA-256 a6adacefdabd1f9a8ef8aa3f1c6c35ca78d4d258a6edd5065175c9a4154878f9
- candidate TAR SHA-256 5b9b0ee16b086ce6d9ce6f435bda871af587a980d7d7ad81ada0fb9e6aa359df

Verification mechanics:
- exact successful repaired 26803 17-stage procedure, unchanged
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

Runtime allowlist: exactly 2 modified paths
- app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt
- app/version.properties

26804 purpose:
- remove JPEG-only pink/magenta fill from thin nominally white structures such as subtitles while preserving exact luma/black outline contrast
- remove disconnected alternating pink/green/cyan false-color segments on thin neutral LED/grow-light bars under the same bounded pre-VGN owner
- operate immediately after Sabre RGB reconstruction and before VGN, before false chroma can be protected as material color downstream
- preserve the exact successful 26803 far-parent late owner for thicker bright-source/chrome geometry

26804 safety architecture:
- legacy 5x5 gate remains default, but a gate-zero subtitle-center pixel may continue only through a cheap bright+chroma prefilter plus existing RAW-CFA invalidity proof
- thin geometry requires darker support on BOTH sides within <=10px along one image axis
- common proof also requires neutral surrounding evidence, chroma and minimum luma
- near-white filled ridge branch: all channels must remain materially present; unsupported chroma is neutralized to the achromatic axis
- disconnected/alternating outlier branch: center chroma must disagree with local 3x3 median; correction targets that median so coherent real colored thin structures are preserved
- exact linear luma restored; alpha unchanged
- 26784 broad clipped-neutral branch remains retired
- no new GPU texture/allocation/lifetime owner; existing 26778 stats SSBO only grows 5 -> 9 uints for decision telemetry

THREE-STAGE VSCODE.DEV UPLOAD — preserve this order exactly.

STAGE 1 — upload the CONTENTS of STAGE_1_UPLOAD_FIRST to repository root, preserving paths.
Commit/push message suggestion:
  26804: prepare pre-VGN thin-neutral ridge repair
This stage contains no workflow, no trigger and no sealed hash manifest, so it must not start 26804.

STAGE 2 — upload the CONTENTS of STAGE_2_UPLOAD_SECOND to repository root, preserving .github/workflows/.
Commit/push message suggestion:
  26804: add pre-VGN thin-neutral ridge workflow
This stage contains only the workflow. It still must not start because TRIGGER_26804.txt is absent.

STAGE 3 — upload the CONTENTS of STAGE_3_UPLOAD_LAST to repository root.
Commit/push message suggestion:
  26804: activate pre-VGN thin-neutral ridge build
This stage contains exactly:
  26804_HANDOFF_HASHES.sha256
  TRIGGER_26804.txt
This final push should launch exactly one intended 26804 workflow.

Before upload status:
- prepared/upload-ready only
- real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally
- GitHub Actions is authoritative and will run them in the exact successful 26803 order
