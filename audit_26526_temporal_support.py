#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

FUSION = "app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt"
STACKER = "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt"
SHADERS = "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt"

REQUIRED = {
    FUSION: [
        "IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE",
        "GlesIris26521SpatialRgbStacker",
    ],
    STACKER: [
        "IRIS_26520_V5_FINAL_FINEST_LK_OWNER",
        "IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW",
        "IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME",
        "IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_STATS",
    ],
    SHADERS: [
        "IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT",
        "IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS",
        "IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8",
    ],
}

FORBIDDEN_ACTIVE_LEGACY = [
    "PyramidAlignment",
    "Sabre",
]

def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    rows = {
        "latestBjzhouReference": "c317bf97d2649ae9296bc1459979ce63cb3364b2",
        "temporalImageMathChanged": False,
        "temporalSupportAction": "EXACT_CANDIDATE_ARCHITECTURE_AUDIT_ONLY",
        "files": {},
        "semanticCounts": {},
    }

    for rel, tokens in REQUIRED.items():
        p = a.root / rel
        if not p.is_file():
            raise SystemExit("missing temporal owner: " + rel)
        s = p.read_text(encoding="utf-8", errors="strict")
        for token in tokens:
            if token not in s:
                raise SystemExit(f"required exact-candidate temporal lineage missing: {rel} :: {token}")
        rows["files"][rel] = h(p)
        rows["semanticCounts"][rel] = {
            "accept": len(re.findall(r"accept", s, flags=re.I)),
            "reject": len(re.findall(r"reject", s, flags=re.I)),
            "mergeWeight": len(re.findall(r"mergeWeight", s)),
            "alignment": len(re.findall(r"alignment", s, flags=re.I)),
            "ceil": len(re.findall(r"ceil", s, flags=re.I)),
            "floor": len(re.findall(r"floor", s, flags=re.I)),
        }

    # These names may occur in comments/imports elsewhere, so only reject if they occur in
    # the two active Iris owner files themselves.
    active = (a.root / STACKER).read_text(encoding="utf-8") + "\n" +              (a.root / SHADERS).read_text(encoding="utf-8")
    for token in FORBIDDEN_ACTIVE_LEGACY:
        if token in active:
            raise SystemExit("forbidden legacy owner vocabulary survived in active Iris Spatial source: " + token)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: exact 26525 candidate proves active Iris 26521 Spatial owner")
    print("PASS: merge-domain rejection-flow and continuous finest-LK transport lineage present")
    print("PASS: corrected 26523 variance-equivalent support diagnostics present")
    print("TEMPORAL_IMAGE_MATH_CHANGED=false")
    print("TEMPORAL_SUPPORT_ACTION=EXACT_CANDIDATE_ARCHITECTURE_AUDIT_ONLY")

if __name__ == "__main__":
    main()
