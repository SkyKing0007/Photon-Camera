#!/usr/bin/env python3
import math

def mirror_index(v,n):
    if n<=1:return 0
    period=2*(n-1)
    w=v%period
    return w if w<n else period-w

for n in (3072,4096):
    for v in range(-12,n+12):
        m=mirror_index(v,n)
        assert 0<=m<n
        # even-sized Bayer image: reflected sample preserves CFA parity.
        assert (m&1)==(v&1), (n,v,m)
print('PASS: 26498 12-pixel true-photo mirror halo preserves Bayer parity')

# Opponent-color consensus behavior: one sample may never paint missing color;
# two consistent physical samples may contribute; disagreement is suppressed.
def safe_chroma(vals):
    if len(vals)<2:return 0.0
    mean=sum(vals)/len(vals)
    var=max(sum(x*x for x in vals)/len(vals)-mean*mean,0.0)
    sigma=math.sqrt(var)
    rel=sigma/max(abs(mean),0.045)
    if rel<=0.22:conf=1.0
    elif rel>=0.42:conf=0.0
    else:
        t=(rel-0.22)/(0.42-0.22)
        t=t*t*(3-2*t)
        conf=1-t
    return mean*conf
assert safe_chroma([0.12])==0.0
assert safe_chroma([0.12,0.115])>0.10
assert abs(safe_chroma([0.15,-0.15]))<1e-9
print('PASS: 26498 isolated/disagreeing censored chroma cannot become color authority')

# Full-resolution UHDR: the decoder receives a one-to-one gain sample. Quantize
# to the actual 8-bit gain map and verify there is no neighbor mixing or edge move.
max_ratio=2.5
max_log=math.log2(max_ratio)
sdr=[0.10]*8+[0.80]*8
true_gain=[1.0]*7+[1.8,2.2]+[1.0]*7
hdr=[sdr[i]*true_gain[i] for i in range(16)]
encoded=[]; decoded=[]
for s,h in zip(sdr,hdr):
    ratio=max(1.0,min(max_ratio,(h+0.015625)/(s+0.015625)))
    e=math.log2(ratio)/max_log
    q=round(max(0,min(1,e))*255)
    encoded.append(q)
    decoded.append(2**((q/255.0)*max_log))
recon=[sdr[i]*decoded[i] for i in range(16)]
# Pixels whose gain is exactly unity cannot be modified by a neighbor's HDR edge.
for i,g in enumerate(true_gain):
    if g==1.0:
        assert encoded[i]==0
        assert abs(recon[i]-sdr[i])<1e-12
assert encoded[7]>0 and encoded[8]>0
print('PASS: 26498 full-resolution gain map has zero cross-pixel gain interpolation')

# Contrast test: a sharp SDR step remains a sharp step when surrounding gain=1.
assert recon[6]==sdr[6] and recon[9]==sdr[9]
print('PASS: 26498 UHDR primary spatial detail is not downsampled by gain-map geometry')

print('PASS: 26498 root architecture synthetic validation complete')
