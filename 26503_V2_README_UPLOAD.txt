26503 V2 Canonical Scene-Faithful A-G handoff

WHAT THIS HANDOFF DOES
1. Verifies the current experimental-clean-photon-rebuild lineage.
2. Creates NO backup branch and requires NO new backup branch.
3. Reconstructs exact tested 26502 one final time only to synchronize app/src/main with the tested APK runtime.
4. Commits/pushes that exact tested 26502 source as the canonical app/src/main if it is not already canonical.
5. Builds 26503 as a direct exact eight-file delta from canonical 26502.
6. Does NOT promote untested 26503 source on the normal first run.
7. Emits exactly one named 26503 APK plus the proof bundle.

VSCODE.DEV UPLOAD
Upload/replace every file from this ZIP at the matching repository path on branch:
  experimental-clean-photon-rebuild
Keep the nested .github/workflows path exactly as supplied.

Suggested handoff commit message:
  26503 V2 handoff: canonical 26502 + scene-faithful A-G build

The push triggers the guarded workflow. Do not manually set promote_26503_source=true for the first build.

EXPECTED BUILD
Version: 0.9726503
Build: 26503
APK: IrisCamera-0.9726503-26503-canonical-scene-faithful-debug.apk

FIRST-RUN EXPECTATION
- If repository app/src/main is still stale, the workflow first commits:
    Canonicalize tested 26502 V4 runtime source [skip ci]
  This source-only synchronization does not retrigger the 26503 workflow because the workflow push paths are limited to handoff files.
- Then the same running workflow creates the 26503 candidate directly from canonical 26502 and builds it.
- PROMOTE_26503_SOURCE remains false, so 26502 stays canonical until 26503 is tested on-device.

AFTER BUILD
Send the final GitHub Actions output/proof or say the run completed. The APK should not be treated as install-ready until the final PASS gates and artifact identity are checked.

AFTER ON-DEVICE ACCEPTANCE
Only after 26503 is judged successful should the same workflow be run manually with:
  promote_26503_source = true
That promotes accepted 26503 into app/src/main so 26504 starts directly from 26503 under the new canonical-source rule.

LAYMAN VERSION
26502 becomes the actual engine sitting in the source tree. 26503 is made by changing only eight proven owners on that engine. The first run gives you 26503 to test but keeps tested 26502 as the official engine. If 26503 is good, then and only then we make 26503 the new official engine.
