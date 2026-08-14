from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
shader = root / "app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
version = root / "app/version.properties"

for p in [shader, version]:
    if not p.exists():
        raise SystemExit("26479 missing candidate source: " + str(p))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

EXPECTED_26478_SHADER_SHA256 = "e02229aa014354ff85c2a9ceb819668dba9e8959ef489f194ae675de94bee523"
if sha256(shader) != EXPECTED_26478_SHADER_SHA256:
    raise SystemExit(
        "26479 exact 26478 reference shader hash mismatch: "
        + sha256(shader))

v = version.read_text()
if "VERSION_NAME=0.9726478" not in v or "VERSION_BUILD=26478" not in v:
    raise SystemExit("26479 exact 26478 version gate failed")

t = shader.read_text()

old = '''        float sample=cfaAt(p);
        refNum[c]+=sample*w;
'''
new = '''        /* IRIS_26479_ADRENO_GLSL_SAMPLE_KEYWORD_PORTABILITY */
        float cfaSample=cfaAt(p);
        refNum[c]+=cfaSample*w;
'''
if t.count(old) != 1:
    raise SystemExit(
        "26479 reserved-keyword shader anchor count=" + str(t.count(old)))
t = t.replace(old, new, 1)

code = re.sub(r"/\*.*?\*/", " ", t, flags=re.S)
code = re.sub(r"//[^\n]*", " ", code)
if re.search(r"\bsample\b", code):
    raise SystemExit("26479 bare GLSL keyword 'sample' remains in executable shader code")

for required in [
    "IRIS_26478_WRONSKI_REFERENCE_ADD_ONCE_NO_IPOL_ACCUMULATED_DENOISER",
    "IRIS_26479_ADRENO_GLSL_SAMPLE_KEYWORD_PORTABILITY",
    "const int RAD=1;",
    "oldNum.rgb+refNum",
    "oldDen.rgb+refDen",
]:
    if required not in t:
        raise SystemExit("26479 reference-add invariant missing: " + required)

shader.write_text(t)

v = v.replace("VERSION_NAME=0.9726478", "VERSION_NAME=0.9726479", 1)
v = v.replace("VERSION_BUILD=26478", "VERSION_BUILD=26479", 1)
version.write_text(v)

print("26479 exact-26478 runtime shader portability transform PASS")
print("26479 reserved GLSL keyword sample removed from executable reference-add code PASS")
print("26479 Wronski reference-add math unchanged PASS")
