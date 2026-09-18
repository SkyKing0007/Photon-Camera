#!/usr/bin/env python3
from pathlib import Path
import sys

import shutil
if len(sys.argv) != 3:
    raise SystemExit('usage: transform_26667.py BASE OUT')
base=Path(sys.argv[1]).resolve(); root=Path(sys.argv[2]).resolve()
if root.exists(): shutil.rmtree(root)
shutil.copytree(base,root)

def edit(rel, old, new, count=1):
    p = root / rel
    s = p.read_text()
    c = s.count(old)
    if c != count:
        raise SystemExit(f'FAIL transform anchor {rel}: expected {count}, got {c}')
    p.write_text(s.replace(old, new, count))

main = 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java'
edit(main,
'''    /* IRIS_26663_STABLE_PREVIEW_PRESENTATION_STATE */\n    private float mIris26663LastConfirmedProtectionEv = 0.0f;\n    private float mIris26663PresentedProtectionEv = 0.0f;\n''',
'''    /* IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION_STATE\n     * Keep only the last exact Camera2-result protection value. 26663 added a second 0.10 EV/frame\n     * presentation slew on top of already-cadenced capture protection; that extra display state is\n     * removed so the frame-matched 26662 compensation follows the actual SurfaceTexture frame. */\n    private float mIris26663LastConfirmedProtectionEv = 0.0f;\n''')
edit(main,
'''        /* IRIS_26663_STABLE_PREVIEW_METADATA_HOLD\n         * Keep the 26662 white-anchored display compensation, but never interpret callback-order\n         * latency as 0 EV. Exact Camera2 metadata updates the confirmed target; an unmatched frame\n         * holds that target. A bounded 0.10 EV/frame presentation slew removes visible single-frame\n         * steps without feeding anything back into Camera2 AE or RAW capture. */\n        CaptureController iris26663Controller = PhotonCamera.getCaptureController();\n        if (iris26663Controller != null && iris26553FrameTimestamp > 0L) {\n            float exactEv = iris26663Controller.getMotion26663ReferencePreviewProtectionEv(\n                    iris26553FrameTimestamp);\n            if (Float.isFinite(exactEv)) {\n                mIris26663LastConfirmedProtectionEv = Math.max(0.0f, exactEv);\n            }\n        }\n        float iris26663DeltaEv = mIris26663LastConfirmedProtectionEv\n                - mIris26663PresentedProtectionEv;\n        if (Math.abs(iris26663DeltaEv) <= 0.01f) {\n            mIris26663PresentedProtectionEv = mIris26663LastConfirmedProtectionEv;\n        } else {\n            mIris26663PresentedProtectionEv += Math.max(-0.10f,\n                    Math.min(0.10f, iris26663DeltaEv));\n        }\n        float iris26663PreviewGain = (float) Math.pow(2.0,\n                Math.max(0.0f, mIris26663PresentedProtectionEv));\n        GLES20.glUniform1f(iris26662ReferencePreviewGain, iris26663PreviewGain);\n''',
'''        /* IRIS_26667_FRAME_EXACT_PREVIEW_PRESENTATION\n         * Preserve 26662 timestamp matching and 26663 hold-on-miss, but remove the additional\n         * 0.10 EV/frame display slew. The preview compensation now changes only when an exact\n         * Camera2 result for the displayed SurfaceTexture frame proves the protection EV; metadata\n         * misses hold the last exact value instead of inventing a transition. Capture AE ownership,\n         * Google-style highlight-safe reference acquisition and RAW exposure are untouched. */\n        CaptureController iris26663Controller = PhotonCamera.getCaptureController();\n        if (iris26663Controller != null && iris26553FrameTimestamp > 0L) {\n            float exactEv = iris26663Controller.getMotion26663ReferencePreviewProtectionEv(\n                    iris26553FrameTimestamp);\n            if (Float.isFinite(exactEv)) {\n                mIris26663LastConfirmedProtectionEv = Math.max(0.0f, exactEv);\n            }\n        }\n        float iris26667PreviewGain = (float) Math.pow(2.0,\n                Math.max(0.0f, mIris26663LastConfirmedProtectionEv));\n        GLES20.glUniform1f(iris26662ReferencePreviewGain, iris26667PreviewGain);\n''')

stack = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
edit(stack,
'''                /* IRIS_26666_MOTION_LONG_PHOTON_EVIDENCE_WEIGHT\n                 * The old +2.5 EV LONG keeps weight 1. Extra authority starts only above the exact\n                 * old acceptance ceiling (~7.46x energy), so ordinary 26665 Motion is unchanged.\n                 * Motion-only is proven by preserveExtendedHdrThroughVgn; Night remains exactly 1.\n                 * At >=9 NORMAL frames the 2.80 cap also stays within the existing 6*frame packed\n                 * validity budget (5*(N-1+2.8) <= 6*N). */\n''',
'''                /* IRIS_26667_LOCAL_CONFIDENCE_LONG_EVIDENCE_REQUEST\n                 * Keep 26666's deeper capture-only LONG request and its requested SNR advantage, but\n                 * do not grant that advantage globally. The merge shader now applies extra LONG\n                 * authority only where the exact ordinary Sabre rejection + source-headroom gate\n                 * already reports high local confidence, and caps final LONG authority near one\n                 * NORMAL observation. Night and the old +2.5 EV LONG remain exact weight 1. */\n''')
edit(stack,
'''                            "peakWeight=${peak / 255.0} longEvidenceWeight26666=$longEvidenceWeight26666 " +\n                            "postSourceClip=true " +\n                            "productionAccumulatorUnmodifiedByProof=true"\n''',
'''                            "peakWeight=${peak / 255.0} longEvidenceWeight26666=$longEvidenceWeight26666 " +\n                            "longEvidencePolicy26667=LOCAL_CONFIDENCE_GATE " +\n                            "longConfidenceStart26667=0.60 longConfidenceFull26667=0.90 " +\n                            "longFinalWeightCap26667=1.25 postSourceClip=true " +\n                            "productionAccumulatorUnmodifiedByProof=true"\n''')

shader = 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
edit(shader,
'''            frameWeight *= max(uLongEvidenceWeight26666,1.0);\n''',
'''            /* IRIS_26667_LOCAL_CONFIDENCE_LONG_EVIDENCE\n             * 26666 multiplied every surviving LONG sample by as much as 2.8 after rejection.\n             * That could turn a merely nonzero/marginal local match into visible blur/chroma. Keep\n             * the same requested SNR weight, but earn it continuously from the exact post-clip\n             * ordinary Sabre frameWeight and never let one LONG observation exceed 1.25x one fully\n             * trusted NORMAL observation. NORMAL/Night remain bit-identical because their uniform\n             * is exactly 1.0. */\n            float iris26667BaseWeight = clamp(frameWeight, 0.0, 1.0);\n            float iris26667RequestedBoost = max(uLongEvidenceWeight26666, 1.0);\n            float iris26667LocalConfidence = smoothstep(0.60, 0.90, iris26667BaseWeight);\n            float iris26667AppliedBoost = mix(1.0, iris26667RequestedBoost, iris26667LocalConfidence);\n            frameWeight = min(iris26667BaseWeight * iris26667AppliedBoost, 1.25);\n''')

ver='app/version.properties'
edit(ver, 'VERSION_NAME=0.9726666\nVERSION_BUILD=26666\n', 'VERSION_NAME=0.9726667\nVERSION_BUILD=26667\n')
print('TRANSFORM_26667_OK')
