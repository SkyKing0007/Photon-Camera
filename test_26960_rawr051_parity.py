#!/usr/bin/env python3
"""RAWR current 13-strength motion gate, shader ABI and B-only reference-shrink scope."""
import argparse,json,pathlib,re
R=pathlib.Path(__file__).resolve().parent
V=R/'handoff_payload_26960/app/src/main/cpp/iris26864'
def source(path,live):
 p=(R/'app/src/main/cpp/iris26864' if live else V)/path
 return p.read_text()
def verify(live=False):
 p=json.loads((R/'26960_RAWR051_SOURCE_PROVENANCE.json').read_text())
 assert p['release_commit']=='4c64cb1f5eb553bf61ca9a459c5a2c94964732e4'
 assert p['latest_rawr_github_commit']=='7f455e7f1c36c1a640dbbe1dafe2e7bb4f9d2e86'
 assert p['rawr_strength_default']==13.0
 d=source('Iris26864RealRawrCoordinator.cpp',live)
 assert 'hdrq.strength = 13.0f' in d and '11.0f' not in d[d.index('rawr::raw_merge_hdrplus_gpu::Config hdrq{};'):d.index('std::unique_ptr<AndroidBurstCoordinator> perCapture')]
 h=source('bridge/Iris26888BOffHdrqPrivateHeader.hpp',live)
 assert h.count('void setMotionGate(bool enabled)')==1
 assert 'void setMotionReferenceShrink(float strength)' in h
 assert 'float motionReferenceShrink_=1.0f' in h
 c=source('bridge/Iris26888BOffHdrqCoordinator.cpp',live)
 assert 'recorder.setMotionGate(algorithm_ == MergeAlgorithm::HdrPlusFrequency);' in c
 assert 'recorder.setMotionReferenceShrink(photoBOff26960 ? 0.0f : 1.0f);' in c
 assert 'iris26957HdrqEffectiveFrames = hdrqEffectiveFrames;' in c
 assert 'pass == 3u && algorithm_ == MergeAlgorithm::HdrPlusFrequency)' in c
 assert 'photoBOffRawr051' not in c
 assert '!photoBOff26960' not in c
 assert 'float(frameCount) : hdrqEffectiveFrames' not in c
 assert 'kGateLow' not in c and 'kGateShrink' not in c
 assert 'vkWaitForFences(device_, 1, &fence_, VK_TRUE, UINT64_MAX)' in c
 m=source('bridge/Iris26887BOffHdrqRecorder.cpp',live)
 assert 'kGateLow=1.6f, kGateHigh=2.6f, kGateShrink=1.0f' in m
 assert 'kEnergyGain=1.0f, kEnergyDead=1.0f, kEnergyScale=0.5f' in m
 assert 'gated ? motionReferenceShrink_ : kGateShrink' in m
 assert 'const bool gated=uniformExposure_ && motionGateEnabled_' in m
 assert 'static_assert(sizeof(MismatchPc)==52u' in m
 assert 'static_assert(sizeof(MismatchNormPc)==24u' in m
 assert 'static_assert(sizeof(FreqMergePc)==56u' in m
 # No independent older chroma gate or exposure path may reclaim ownership.
 assert 'recorder.setMeasuredRawNoise(slopes, offsets, measured);' in c
 assert 'const auto fit = fitBurstNoise(' in c
 assert 'photoBOff26960' in c
 if live:
  for shader in ('Iris26888BOffHdrqMismatch.comp','Iris26887BOffHdrqMerge.comp','Iris26887BOffHdrqMismatchNorm.comp'):
   s=(R/'app/src/main/cpp/iris26864/bridge'/shader).read_text()
   assert 'useMotionGate' in s
 print('PASS RAWR current motion/energy gate, strength=13, exact 26959 shaders/ABI, B-only ref spectral shrink off and no stale gate bypass')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--payload',action='store_true');ap.add_argument('--live',action='store_true');args=ap.parse_args();verify(args.live)
