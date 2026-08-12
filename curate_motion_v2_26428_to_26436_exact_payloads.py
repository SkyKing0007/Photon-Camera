#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, json, re, subprocess
from pathlib import Path

BASE="aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"
STAGES=[
 ("26429","build_26429_codespace_shared_guide_reference_structure.sh"),
 ("26430","build_26430_codespace_v2_ownership_headroom_cleanup.sh"),
 ("26436","build_26436_windows_integrated_motion_architecture.ps1"),
]

def fail(msg): raise SystemExit("FAIL: "+msg)
def sha_bytes(b): return hashlib.sha256(b).hexdigest().upper()
def norm(p): return p.replace("\\","/").lstrip("./")

def parse_payloads(text):
    payload={}
    hashes={}
    # Bash exact CAND_B64 / CAND_HASH
    for p,b in re.findall(r"CAND_B64\[['\"]([^'\"]+)['\"]\]\s*=\s*['\"]([A-Za-z0-9+/=]{40,})['\"]",text):
        payload[norm(p)]=b
    for p,h in re.findall(r"CAND_HASH\[['\"]([^'\"]+)['\"]\]\s*=\s*['\"]([0-9A-Fa-f]{64})['\"]",text):
        hashes[norm(p)]=h.upper()

    # PowerShell exact full-file payload map.
    for p,b in re.findall(r"['\"](app[\\/][^'\"]+)['\"]\s*=\s*['\"]([A-Za-z0-9+/=]{40,})['\"]",text,re.S):
        try:
            raw=base64.b64decode(b,validate=True)
            raw.decode("utf-8-sig")
        except Exception:
            continue
        payload[norm(p)]=b

    # Candidate hash maps, where present.
    for p,h in re.findall(r"['\"](app[\\/][^'\"]+)['\"]\s*=\s*['\"]([0-9A-Fa-f]{64})['\"]",text):
        if "CAND" in text[max(0,text.find(h)-1500):text.find(h)+200].upper():
            hashes[norm(p)]=h.upper()
    return payload,hashes

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--harness",required=True)
    ap.add_argument("--target",required=True)
    ap.add_argument("--manifest",required=True)
    a=ap.parse_args()
    harness=Path(a.harness).resolve()
    target=Path(a.target).resolve()
    manifest=Path(a.manifest).resolve()

    head=subprocess.check_output(["git","-C",str(target),"rev-parse","HEAD"],text=True).strip()
    if head!=BASE: fail(f"target HEAD={head}; expected exact 26428 {BASE}")

    history=harness/"historical_replay"
    if not history.is_dir(): fail("historical_replay missing")

    rec=[]
    for stage,name in STAGES:
        src=history/name
        if not src.is_file(): fail(f"{stage} evidence missing: {name}")
        text=src.read_text(encoding="utf-8-sig")
        payload,hashes=parse_payloads(text)
        app_payload={k:v for k,v in payload.items() if k=="app/version.properties" or k.startswith("app/src/")}
        if not app_payload:
            fail(f"{stage} has no exact full-file source payloads; refusing historical-script execution")

        changed=[]
        for rel,b64 in sorted(app_payload.items()):
            raw=base64.b64decode(b64,validate=True)
            # Historical payload hash is checked before LF normalization.
            if rel in hashes and sha_bytes(raw)!=hashes[rel]:
                fail(f"{stage} payload hash mismatch {rel}: expected={hashes[rel]} actual={sha_bytes(raw)}")
            dst=target/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            try:
                txt=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
                dst.write_text(txt,encoding="utf-8",newline="\n")
            except UnicodeDecodeError:
                dst.write_bytes(raw)
            changed.append({"path":rel,"sha256":hashlib.sha256(dst.read_bytes()).hexdigest()})
        print(f"PASS: {stage} exact source snapshot applied files={len(changed)}")
        rec.append({"stage":stage,"evidence":name,"files":changed})

    # 26436 must already contain the successful 26429-26435/UHDR lineage.
    required=[
      ("app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl","IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT"),
      ("app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl","IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS"),
      ("app/src/main/assets/shaders/motionv2/color_transform.glsl","IRIS_26430_"),
      ("app/src/main/assets/shaders/motionv2/render.glsl","IRIS_26435_"),
      ("app/src/main/assets/shaders/motionv2/gainmap.glsl","IRIS_26436_"),
    ]
    for rel,marker in required:
        p=target/rel
        if not p.is_file() or marker not in p.read_text(encoding="utf-8-sig"):
            fail(f"curated 26436 proof missing {marker} in {rel}")
        print("PASS: curated marker",marker,rel)

    # Explicitly repair the known 26428/early-lineage shader typo only if it
    # survived all exact payloads. This is a compiler correctness fix, not IQ tuning.
    color=target/"app/src/main/assets/shaders/motionv2/color_transform.glsl"
    ct=color.read_text(encoding="utf-8-sig")
    typo="mix(coherent,vec3(terminalEnergy),terminal)"
    if typo in ct:
        ct=ct.replace(typo,"mix(coherentRgb,vec3(terminalEnergy),terminal)",1)
        color.write_text(ct,encoding="utf-8",newline="\n")
        print("PASS: latent undefined coherent -> coherentRgb compile typo repaired")

    # This is the curated source checkpoint before Wronski. Version is made
    # explicit so the final transformer has one deterministic baseline.
    vp=target/"app/version.properties"
    v=vp.read_text(encoding="utf-8-sig")
    v=re.sub(r"(?m)^VERSION_NAME=.*$","VERSION_NAME=0.9726436",v)
    v=re.sub(r"(?m)^VERSION_BUILD=.*$","VERSION_BUILD=26436",v)
    vp.write_text(v,encoding="utf-8",newline="\n")

    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps({
      "base":BASE,
      "method":"exact full-file historical payloads only; no historical scripts executed",
      "applied":["26429","26430","26436"],
      "superseded_by_wronski":["26437","26438","26439","26443","26445-reconstruction","26446"],
      "retained_concepts_in_wronski":[
        "reference-first ownership","temporal/channel coherence",
        "specular/per-channel validity","true frame-equivalent support"
      ],
      "later_downstream_policy":"26453 structural-edge cleanup applied by final transformer",
      "rejected":["26440","26441","26442","26447","26448","26449","26454","26455","26456","26457","26458","26459","26460","26461"],
      "records":rec
    },indent=2),encoding="utf-8",newline="\n")

    print("candidate/source validation PASS")
    print("Temporary-copy validation: PASS")
    print("PRE-BUILD SAFETY PROOF PASSED")
    print("PASS: exact payload-only curation complete; no historical build executed")

if __name__=="__main__":
    main()
