#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, tempfile, tarfile
SHADERS=[
"app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl",
"app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl",
"app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl",
]
TEXT=[
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt",
"app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
]+SHADERS
def lexical(root):
    for rel in TEXT:
        t=(root/rel).read_text()
        if t.count("{")!=t.count("}"): raise RuntimeError(rel+" brace imbalance")
        if t.count("(")!=t.count(")"): raise RuntimeError(rel+" paren imbalance")
        if "\x00" in t: raise RuntimeError(rel+" contains NUL")
    c=(root/SHADERS[0]).read_text()
    for x in ["uniform float kDetail;","uniform float kDenoise;","uniform float Dth;","uniform float Dtr;","uniform float kStretch;","uniform float kShrink;"]:
        if x not in c: raise RuntimeError("Figure-7 uniform missing: "+x)
    if "mat2 P=mat2(yy,-xy,-xy,xx)/det;" not in c: raise RuntimeError("covariance-to-precision inversion missing")
    q=(root/SHADERS[1]).read_text(); b=(root/SHADERS[2]).read_text()
    if "return exp(-0.5*d);" not in q: raise RuntimeError("Spatial Gaussian law missing")
    if "return exp(-0.5 * distance);" not in b: raise RuntimeError("Bayer Gaussian law missing")
def compile_shader(v,rel,text):
    if rel.endswith("mfsr_mgc_covariance.glsl"):
        text=text.replace("#define LAYOUT //\nLAYOUT\n","#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;\n",1); stage="comp"
    elif rel.endswith("mfsr_bayer_accumulate.glsl"):
        text=text.replace("#define LAYOUT //\nLAYOUT\n","#version 310 es\nlayout(local_size_x=8,local_size_y=8,local_size_z=1) in;\n",1); stage="comp"
    else:
        text="#version 300 es\n"+text; stage="frag"
    with tempfile.NamedTemporaryFile("w",suffix="."+stage,delete=False) as f: f.write(text); name=f.name
    try:
        r=subprocess.run([v,"-S",stage,name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if r.returncode: raise RuntimeError(rel+" glslang failed:\n"+r.stdout)
    finally: Path(name).unlink(missing_ok=True)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root"); ap.add_argument("--validator"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test:
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            with tarfile.open(Path(__file__).resolve().parent/"26542_RUNTIME_PAYLOAD.tar.gz","r:gz") as tf: tf.extractall(r)
            lexical(r)
        print("PASS: 26542 changed syntax self-test"); return
    r=Path(a.root).resolve(); lexical(r)
    if a.validator:
        for rel in SHADERS: compile_shader(a.validator,rel,(r/rel).read_text())
        print("PASS: 26542 changed GLSL compiled with "+a.validator)
    else: print("PASS: 26542 changed lexical syntax")
if __name__=="__main__": main()
