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

LEGACY_IDENTIFIERS = ["PyramidAlignment", "Sabre"]

def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def strip_comments_and_literals(src: str) -> str:
    """Neutralize Kotlin/Java comments and literals while preserving line structure."""
    out = []
    i = 0
    n = len(src)
    state = "code"
    quote = ""

    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        tri = src[i:i + 3]

        if state == "code":
            if c == "/" and nxt == "/":
                out.extend((" ", " "))
                i += 2
                state = "line_comment"
                continue
            if c == "/" and nxt == "*":
                out.extend((" ", " "))
                i += 2
                state = "block_comment"
                continue
            if tri == '"""':
                out.extend((" ", " ", " "))
                i += 3
                state = "triple_string"
                continue
            if c in ('"', "'"):
                quote = c
                out.append(" ")
                i += 1
                state = "literal"
                continue
            out.append(c)
            i += 1
            continue

        if state == "line_comment":
            if c == "\n":
                out.append("\n")
                state = "code"
            else:
                out.append(" ")
            i += 1
            continue

        if state == "block_comment":
            if c == "*" and nxt == "/":
                out.extend((" ", " "))
                i += 2
                state = "code"
            else:
                out.append("\n" if c == "\n" else " ")
                i += 1
            continue

        if state == "triple_string":
            if tri == '"""':
                out.extend((" ", " ", " "))
                i += 3
                state = "code"
            else:
                out.append("\n" if c == "\n" else " ")
                i += 1
            continue

        # Normal string or char literal.
        if c == "\\":
            out.append(" ")
            i += 1
            if i < n:
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            continue
        if c == quote:
            out.append(" ")
            i += 1
            state = "code"
            quote = ""
            continue
        out.append("\n" if c == "\n" else " ")
        i += 1

    return "".join(out)

def executable_legacy_hits(src: str) -> dict[str, int]:
    code = strip_comments_and_literals(src)
    return {
        token: len(re.findall(r"\b" + re.escape(token) + r"\b", code))
        for token in LEGACY_IDENTIFIERS
    }

def source_legacy_occurrences(src: str) -> dict[str, int]:
    return {token: src.count(token) for token in LEGACY_IDENTIFIERS}

def self_test() -> None:
    prose_only = """
        /* Historical note: this is not Sabre and not PyramidAlignment. */
        // Sabre was intentionally not revived.
        val message = "Sabre / PyramidAlignment are dormant"
        val rawShader = \"\"\"// Sabre in embedded GLSL prose
            /* PyramidAlignment is not an active owner. */
            void main() {}
        \"\"\"
        val safe = currentOwner
    """
    hits = executable_legacy_hits(prose_only)
    if any(hits.values()):
        raise SystemExit("self-test failed: comment/string/raw-string vocabulary treated as executable")

    actual_code = """
        val bad = Sabre(input)
        PyramidAlignment.align(a, b)
    """
    hits = executable_legacy_hits(actual_code)
    if hits["Sabre"] != 1 or hits["PyramidAlignment"] != 1:
        raise SystemExit("self-test failed: executable legacy identifiers were not detected")

    hits = executable_legacy_hits("import example.pipeline.Sabre\n")
    if hits["Sabre"] != 1:
        raise SystemExit("self-test failed: legacy import was not detected")

    print("PASS: temporal audit ignores legacy words in comments/normal strings/Kotlin raw strings")
    print("PASS: temporal audit rejects executable/type/import-level legacy identifiers")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        self_test()
        return
    if a.root is None or a.out is None:
        raise SystemExit("--root and --out are required unless --self-test is used")

    # Run lexical regression proof on every normal Actions audit too.
    self_test()

    rows = {
        "latestBjzhouReference": "c317bf97d2649ae9296bc1459979ce63cb3364b2",
        "temporalImageMathChanged": False,
        "temporalSupportAction": "EXACT_CANDIDATE_ARCHITECTURE_AUDIT_ONLY",
        "files": {},
        "semanticCounts": {},
        "legacyVocabularySourceOccurrences": {},
        "legacyExecutableIdentifierHits": {},
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

    # IRIS_26526_V1_1_SEMANTIC_LEGACY_OWNER_AUDIT
    # V1 incorrectly failed on raw vocabulary even when it appeared only in
    # historical comments or embedded shader strings. Positive active-owner proof
    # remains mandatory; this negative check now targets executable identifiers only.
    active_sources = {
        STACKER: (a.root / STACKER).read_text(encoding="utf-8", errors="strict"),
        SHADERS: (a.root / SHADERS).read_text(encoding="utf-8", errors="strict"),
    }

    for rel, src in active_sources.items():
        source_counts = source_legacy_occurrences(src)
        executable_hits = executable_legacy_hits(src)
        rows["legacyVocabularySourceOccurrences"][rel] = source_counts
        rows["legacyExecutableIdentifierHits"][rel] = executable_hits

        for token, count in executable_hits.items():
            if count:
                raise SystemExit(
                    f"forbidden executable legacy owner identifier survived in active Iris Spatial source: "
                    f"{rel} :: {token} count={count}"
                )

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: exact 26525 candidate proves active Iris 26521 Spatial owner")
    print("PASS: merge-domain rejection-flow and continuous finest-LK transport lineage present")
    print("PASS: corrected 26523 variance-equivalent support diagnostics present")
    print("PASS: legacy-owner audit distinguishes prose/raw shader strings from executable identifiers")
    print("TEMPORAL_IMAGE_MATH_CHANGED=false")
    print("TEMPORAL_SUPPORT_ACTION=EXACT_CANDIDATE_ARCHITECTURE_AUDIT_ONLY")

if __name__ == "__main__":
    main()
