#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, os, sys
import numpy as np
import torch
import onnx
import onnxruntime as ort

PIN='2a0681eae7c2bbc120a019d5bb71bcbd12291df7'
URL='https://www.dropbox.com/s/0ykpsm1d48f74ao/LOL_params_0900000.pt?dl=1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--upstream',required=True); ap.add_argument('--checkpoint',required=True); ap.add_argument('--output',required=True); ap.add_argument('--provenance',required=True); a=ap.parse_args()
    up=Path(a.upstream); out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    commit=os.popen(f'git -C {up} rev-parse HEAD').read().strip()
    if commit!=PIN: raise RuntimeError(f'upstream commit mismatch {commit}')
    ck=Path(a.checkpoint)
    if not ck.is_file() or ck.stat().st_size < 1_000_000: raise RuntimeError('checkpoint missing/suspiciously small')
    cksha=sha(ck)
    sys.path.insert(0,str(up)); from networks import ResnetGenerator
    model=ResnetGenerator(3,3,ngf=64,n_blocks=4,img_size=512).eval()
    params=torch.load(ck,map_location='cpu',weights_only=True)
    if not isinstance(params,dict) or 'genA2B' not in params: raise RuntimeError('checkpoint genA2B state missing')
    state=params['genA2B']; model.load_state_dict(state,strict=True)
    class Wrap(torch.nn.Module):
        def __init__(self,m): super().__init__(); self.m=m
        def forward(self,x): return self.m(x)[0]
    w=Wrap(model).eval(); torch.manual_seed(26533); x=torch.linspace(-1,1,3*512*512,dtype=torch.float32).reshape(1,3,512,512)
    with torch.no_grad(): ref=w(x).cpu().numpy()
    torch.onnx.export(w,x,out,input_names=['input'],output_names=['enhanced'],opset_version=18,do_constant_folding=True,dynamo=False)
    onnx.checker.check_model(onnx.load(out))
    sess=ort.InferenceSession(str(out),providers=['CPUExecutionProvider']); got=sess.run(None,{'input':x.numpy()})[0]
    err=float(np.max(np.abs(ref-got)))
    if not np.isfinite(err) or err>0.0025: raise RuntimeError(f'ONNX equivalence failed max_abs={err}')
    prov={'upstream_commit':PIN,'checkpoint_url':URL,'checkpoint_sha256':cksha,'onnx_sha256':sha(out),'max_abs_pytorch_onnx':err,'shape':[1,3,512,512],'generator':'ResnetGenerator(ch=64,n_res=4,img_size=512)','note':'upstream publishes no immutable checkpoint hash; exact downloaded bytes are recorded and conversion is numerically verified'}
    Path(a.provenance).write_text(json.dumps(prov,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(prov,indent=2))
if __name__=='__main__': main()
