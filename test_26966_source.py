#!/usr/bin/env python3
"""Exact 26965 Actions-compiled source to 26966 candidate; all 2049 protected hashes fail closed."""
import argparse,pathlib,sys
from build_26966_incremental import scope,parse,scan,sha,NBASE,NFILES,NPROTECTED,REQUIRED,fail
R=pathlib.Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
 changed,base,cand=scope()
 assert (len(base),len(cand),len(base)-len(changed))==(2055,2055,2049)
 assert changed==REQUIRED and cand['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'] !=base['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt']
 if args.payload:
  payload=R/'handoff_payload_26966'
  assert {x.relative_to(payload).as_posix() for x in payload.rglob('*') if x.is_file()}==changed
  for path in changed:assert sha(payload/path)==cand[path],path
  assert (payload/'app/version.properties').read_text()=='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726966\nVERSION_BUILD=26966\n'
 if args.live:
  actual=scan(R)
  if actual!=cand:
   wrong=sorted(k for k in set(actual)&set(cand) if actual[k]!=cand[k]);missing=sorted(set(cand)-set(actual));added=sorted(set(actual)-set(cand))
   fail(f'LIVE current source differs: wrong={wrong[:8]} missing={missing[:8]} extra={added[:8]}')
 print('PASS 26966 source: 2055 total; six intentional; all 2049 protected; zero add/delete; actual 26965 compiled authority')
if __name__=='__main__':main()
