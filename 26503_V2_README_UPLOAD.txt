26503 V6 Direct-Canonical retained-frame-owner build-fix handoff

WHAT THIS HANDOFF DOES
1. Verifies branch experimental-clean-photon-rebuild and canonical tested-26502 commit 6118984523296945a0910e55ddaa4d3126184059.
2. Verifies app/src/main + app/version.properties have zero runtime drift from canonical tested 26502.
3. Creates NO backup branch and requires NO new backup branch.
4. Does NOT reconstruct 26499/26501/26502. The long historical replay path is retired for normal forward builds.
5. Freezes a pre-change canonical 26502 snapshot/recovery patch before candidate modification.
6. Builds 26503 as a direct exact seven-file delta from canonical 26502.
7. Keeps tested-26502 ParseExif/ISO100 normalization byte-identical.
8. Does NOT promote untested 26503 source on the normal build.
9. Emits exactly one named 26503 APK plus proof bundle.

V5 FAILURE CORRECTION
The prior run successfully canonicalized tested 26502, then stopped because apply_26503_v2_integrated.py expected the obsolete method name computeReferenceGain. Canonical 26502 actually contains:
  computeDisplayGain(ByteBuffer raw, int width, int height, Parameters parameters, double referenceExposureEnergy)
V5 targets that exact method/caller contract and keeps 26502's sparse histogram sampling so the exposure estimator does not become a CPU performance regression.

V5 also audits the next performance anchor instead of waiting for another Actions failure:
- 26502 had already disabled the old direct-support CPU readback.
- 26503 now freezes that state and disables only the remaining direct-RGB provenance CPU readback/stats loop.
- Functional effective-support metrics remain active.

BUILD INFRASTRUCTURE
The Khronos glslang bootstrap is the exact proven 26501/26502-style block restored in V4 and remains unchanged in V6.

VSCODE.DEV UPLOAD
Upload/replace every file from this ZIP at the matching repository path on branch:
  experimental-clean-photon-rebuild
Keep the nested .github/workflows path exactly as supplied.

Keep promote_26503_source=false for this build.

EXPECTED BUILD
Version: 0.9726503
Build: 26503
APK: IrisCamera-0.9726503-26503-canonical-scene-faithful-debug.apk

AFTER BUILD
Send the final GitHub Actions output/proof or say the run completed. Do not install until the final PASS gates/artifact identity are checked.

AFTER ON-DEVICE ACCEPTANCE
Only after 26503 is judged successful should the workflow be run manually with promote_26503_source=true. That promotes accepted 26503 into app/src/main so 26504 starts directly from 26503.

V6 JAVAC CORRECTION
V5 reached Gradle javac and failed because the seed referenced a field that does not exist: Parameters.retainedFrameCount. The real established owner is MotionMetrics.retainedFrames(). V6 changes only that ownership reference in the intended 26503 candidate and adds a pre-Gradle Java field/method ownership audit so this class of nonexistent Parameters symbol is caught before the expensive Gradle build.

COMMIT SENTENCE
  26503 V6: use MotionMetrics retained-frame owner and add Java symbol preflight
