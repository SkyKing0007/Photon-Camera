#!/usr/bin/env python3
import math

def clamp(x,a=0.,b=1.): return max(a,min(b,x))
def smooth(a,b,x):
    t=clamp((x-a)/max(b-a,1e-9)); return t*t*(3-2*t)
def baseline(x):
    body=.40
    if x<=body:return x
    r=1-body;e=x-body
    return body+r*e/(e+r)
def legacy_map(x,a,b):
    body=.40
    base=baseline(x)
    if x<=body:return base
    if x<=a:
        t=clamp((x-body)/(a-body));m=body+t*(.95-body)
    elif x<=b:
        t=clamp((x-a)/(b-a));m=.95+t*(.995-.95)
    else:
        e=x-b; span=max(b-a,.05);m=.995+(1-.995)*e/(e+span)
    return m

def plan(gain,a,c,b,broad,compact_owned,hard,adaptive):
    gp=smooth(1.,2.10,math.log(max(gain,1.),2))
    sparse=smooth(.0005,.006,hard)*(1-smooth(.35,.75,broad))*adaptive
    ce=max(compact_owned,sparse)
    cp=clamp(ce*(.55+.45*gp)*(1-.35*broad))
    bp=clamp(broad*smooth(.35,.90,gp))
    pos=clamp((c-a)/max(b-a,1e-6))
    legacy995=.95+pos*(.995-.95)
    t99=clamp(.95-.040*bp-.130*cp,.80,.95)
    t995=legacy995-.020*bp-.050*cp
    if bp>1e-6 or cp>1e-6:t995=clamp(t995,t99+.001,.994)
    t998=.995
    hdr99=4.40+.15*bp+.20*cp
    hdr998=min(7.,5.15+.35*bp+1.25*cp)
    h99=max(1.,hdr99/max(a,1e-4)); h998=max(h99,hdr998/max(b,1e-4))
    h995=max(h99,min((h99+pos*(h998-h99))*(1+.08*bp+.16*cp),h998))
    return dict(gp=gp,bp=bp,cp=cp,t99=t99,t995=t995,t998=t998,h99=h99,h995=h995,h998=h998,a=a,c=c,b=b)
def map_sdr(x,p):
    a,c,b=p['a'],p['c'],p['b'];body=.4
    if x<=body:return baseline(x)
    if x<=a:
        t=clamp((x-body)/(a-body));return body+t*(p['t99']-body)
    if x<=c:
        t=clamp((x-a)/(c-a));return p['t99']+t*(p['t995']-p['t99'])
    if x<=b:
        t=clamp((x-c)/(b-c));return p['t995']+t*(p['t998']-p['t995'])
    e=x-b;span=max(b-a,.05);return p['t998']+(1-p['t998'])*e/(e+span)
def hdr_boost(x,p):
    a,c,b=p['a'],p['c'],p['b'];start=max(.4,.75*a)
    if x<=start:return 1.
    if x<=a:
        t=clamp((x-start)/(a-start));return 1+t*(p['h99']-1)
    if x<=c:
        t=clamp((x-a)/(c-a));return p['h99']+t*(p['h995']-p['h99'])
    if x<=b:
        t=clamp((x-c)/(b-c));return p['h995']+t*(p['h998']-p['h995'])
    return p['h998']

def req(cond,msg):
    if not cond: raise SystemExit('FAIL '+msg)
# Representative ordered source anchors; the invariants must not depend on object semantics.
a,c,b=2.2,2.8,3.4
# 1 broad / modest gain = exact 26610 mapping, protecting the good daytime-open-shutter class.
p=plan(2.68,a,c,b,1.0,0.0,0.01,1.0)
req(p['bp']<1e-9 and p['cp']<1e-9,'moderate-lift broad scene not exact legacy')
for i in range(401):
    x=.4+i*(4-.4)/400
    req(abs(map_sdr(x,p)-legacy_map(x,a,b))<2e-6,'legacy broad mapping changed')
# 2 high-lift compact: reserve halo range and expand UHDR tail.
pn=plan(4.2606344,a,c,b,0.0,1.0,.0067,1.0)
req(pn['gp']>.98 and pn['cp']>.98,'night compact pressure not engaged')
req(pn['t99']<=.825 and pn['t995']<.95 and pn['t998']==.995,'compact SDR reservation insufficient')
req(pn['h998']*b>=6.35,'compact UHDR p998 target not expanded')
# 3 tiny coherent compact fallback: compactOwned may be zero, hard+adaptive must still engage.
pt=plan(4.26,a,c,b,0.05,0.0,.006,1.0)
req(pt['cp']>.80,'sparse coherent compact fallback inactive')
# isolated hard pixel without structured/adaptive support must not move presentation.
pi=plan(4.26,a,c,b,0.0,0.0,.006,0.0)
req(pi['cp']==0.0,'isolated hot pixel altered compact presentation')
# 4 broad high lift gets modest extra reservation, not compact-style crushing.
pb=plan(4.26,a,c,b,1.0,0.0,.02,1.0)
req(.90<=pb['t99']<=.915,'broad high-lift p99 target outside bounded range')
req(pb['t99']>pn['t99']+.07,'broad and compact presentations not separated')
# 5 mixed broad+compact remains continuous and supports both.
pm=plan(4.26,a,c,b,.65,.8,.008,1.0)
req(pm['bp']>.6 and pm['cp']>.35,'mixed tail evidence lost')
# 6 body exact invariant and monotonicity for all classes.
for P in (pn,pb,pm):
    for x in [0,.05,.18,.3999,.4]: req(abs(map_sdr(x,P)-x)<1e-12,'body changed')
    prev=-1
    for i in range(1201):
        x=i*5/1200; y=map_sdr(x,P)
        req(y+1e-9>=prev,'SDR mapping not monotonic');prev=y
    prev=1
    for i in range(1201):
        x=.4+i*4.6/1200; q=hdr_boost(x,P)
        req(q+1e-9>=prev,'HDR boost not monotonic');prev=q
# 7 no semantic day/night/object labels are needed to drive plan.
# This is also enforced in source validator; numeric model only uses measured fields.
print('PASS 26612 broad/modest-lift path is mathematically identical to 26610/26611')
print('PASS high-lift compact tail reserves SDR halo range and expands real UHDR tail')
print('PASS tiny coherent compact fallback uses hard-ceiling+structured evidence while isolated hot pixels are ignored')
print('PASS broad high-lift and mixed broad+compact cases remain continuous and distinct')
print('PASS body <=0.40 exact, SDR monotonic, HDR boost monotonic')
