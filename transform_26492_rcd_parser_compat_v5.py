#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import tempfile

TARGET = Path("app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl")

COMPACT_TO_SAFE = {
    "layout(std430, binding = 0) buffer CfaBuf { float cfa[]; };":
"""layout(std430, binding = 0) buffer CfaBuf {
    float cfa[];
};""",
    "layout(std430, binding = 1) buffer RedBuf { float red[]; };":
"""layout(std430, binding = 1) buffer RedBuf {
    float red[];
};""",
    "layout(std430, binding = 2) buffer GreenBuf { float green[]; };":
"""layout(std430, binding = 2) buffer GreenBuf {
    float green[];
};""",
    "layout(std430, binding = 3) buffer BlueBuf { float blue[]; };":
"""layout(std430, binding = 3) buffer BlueBuf {
    float blue[];
};""",
}

EXPECTED = {
    "CfaBuf": 0,
    "RedBuf": 1,
    "GreenBuf": 2,
    "BlueBuf": 3,
}

def _java_space_split(s: str):
    # Java String.split(" ") drops trailing empty tokens.
    parts = re.split(r" ", s)
    while parts and parts[-1] == "":
        parts.pop()
    return parts

def photon_get_layouts_emulation(program: str):
    """Emulate the relevant behavior of GLInterface.getLayouts()."""
    layouts = {}
    for val in program.splitlines():
        if "layout" not in val:
            continue
        divided = _java_space_split(val.replace("{", ""))
        last = ""
        if divided:
            last = divided[-1].replace(";", "").replace("\n", "")
        left = val.find("(")
        if left < 0:
            left = 0
        right = val.rfind(")")
        if right < 0:
            right = len(val) - 1
        parameters = val[left + 1:right].split(",")
        binding = 0
        for item in parameters:
            param_val = item.replace(" ", "").split("=")
            if len(param_val) == 2 and param_val[0] == "binding":
                binding = int(param_val[1])
                break
        layouts[last] = binding
    return layouts

def apply(root: Path):
    path = root / TARGET
    if not path.is_file():
        raise SystemExit(f"V5 parser-compat target missing: {path}")
    src = path.read_text(encoding="utf-8")

    before = photon_get_layouts_emulation(src)
    if all(before.get(k) == v for k, v in EXPECTED.items()):
        raise SystemExit("V5 precondition failed: compact 26492 V4 SSBO declarations are not present")
    if "}" not in before:
        raise SystemExit(
            "V5 precondition failed: Photon parser did not reproduce the V4 compact-layout failure"
        )

    changed = 0
    for old, new in COMPACT_TO_SAFE.items():
        count = src.count(old)
        if count != 1:
            raise SystemExit(f"V5 expected exactly one compact declaration, got {count}: {old}")
        src = src.replace(old, new, 1)
        changed += 1

    # Prove no compact declaration survived.
    for old in COMPACT_TO_SAFE:
        if old in src:
            raise SystemExit(f"V5 compact SSBO declaration survived: {old}")

    path.write_text(src, encoding="utf-8")

    after = photon_get_layouts_emulation(src)
    if {k: after.get(k) for k in EXPECTED} != EXPECTED:
        raise SystemExit(
            "V5 Photon parser compatibility failed: "
            + repr({k: after.get(k) for k in EXPECTED})
        )
    if "}" in after and after.get("}") in EXPECTED.values():
        raise SystemExit("V5 Photon parser still exposes compact-layout bogus key '}'")

    # Preserve the intended 26492 architecture markers/consumers.
    required = (
        "HighlightProvenance",
        "PROVENANCE_NORMAL",
        "PROVENANCE_CENSORED",
        "PROVENANCE_SHORT_VALIDATED",
    )
    for token in required:
        if token not in src:
            raise SystemExit(f"V5 architecture-preservation token missing: {token}")

    print(
        "26492 V5 RCD PARSER COMPAT PASS "
        "files=1 ssboBindings=CfaBuf:0,RedBuf:1,GreenBuf:2,BlueBuf:3 "
        "architectureUnchanged=true"
    )

def self_test():
    compact = """#define LAYOUT //
LAYOUT
precision highp float;
layout(std430, binding = 0) buffer CfaBuf { float cfa[]; };
layout(std430, binding = 1) buffer RedBuf { float red[]; };
layout(std430, binding = 2) buffer GreenBuf { float green[]; };
layout(std430, binding = 3) buffer BlueBuf { float blue[]; };
uniform highp sampler2D HighlightProvenance;
const float PROVENANCE_NORMAL = 0.0;
const float PROVENANCE_CENSORED = 1.0;
const float PROVENANCE_SHORT_VALIDATED = 2.0;
"""
    bad = photon_get_layouts_emulation(compact)
    if all(bad.get(k) == v for k, v in EXPECTED.items()):
        raise SystemExit("self-test failed: compact layout unexpectedly parsed correctly")
    if bad.get("}") != 3:
        raise SystemExit("self-test failed: did not reproduce Photon compact-layout key collapse")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p = root / TARGET
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(compact, encoding="utf-8")
        apply(root)
        safe = photon_get_layouts_emulation(p.read_text(encoding="utf-8"))
        if {k: safe.get(k) for k in EXPECTED} != EXPECTED:
            raise SystemExit("self-test failed: parser-safe layout not recovered")
    print("26492 V5 RCD PARSER COMPAT SELF-TEST PASS")

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
    elif len(sys.argv) == 2:
        apply(Path(sys.argv[1]).resolve())
    else:
        raise SystemExit(
            "usage: transform_26492_rcd_parser_compat_v5.py --self-test | <repo-root>"
        )
