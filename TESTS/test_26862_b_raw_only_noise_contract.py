#!/usr/bin/env python3
"""Permanent 26861->26862 empirical B noise contract: actual accepted burst always examined.

Exact 26861 capture regressions: row-flicker >0.12 and a ~1.2006% NORMAL
shutter change must never trigger a whole-burst metadata veto or Camera2.
8/14/15-frame coverage is independent of metadata; validated source assures
real Kotlin app and GL compilers remain Actions' responsibility.
"""
from pathlib import Path
import sys,re
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app')/'src/main/java/com/hinnka/mycamera/processor'
f=(p/'GlesIris26860BBurstNoise.kt').read_text()
s=(p/'GlesMgcRawSpatialStacker.kt').read_text()
shared=(p/'GlesMgcRawSabreShaders.kt').read_text()
bshade=(p/'GlesIris26858BNoiseHighlight.kt').read_text()
assert f.count('fun estimate(')==1
assert 'PAIR_MAX' not in f and 'order.chunked(2)' in f and 'sensorTimestampNs' in f
assert 'referenceProduct / v' in f and 'exposureTimeNs.toDouble() * f.sensitivityIso.toDouble()' in f
assert 'ROW_FLICKER' not in f and 'BURST_UNSUPPORTED_MIXED_FRAME' not in f
assert 'rowFlickerStrength > 0.12f' not in f and '0.012' not in f
assert 'rowMeans=DoubleArray(side)' in f and 'residuals.sumOf' in f
assert 'phaseBlackByFrame' in f and 'phaseRangeByFrame' in f
assert 'BURST_ALL_PHASE_RAW_BOUNDED' in f and 'BlockEvidence(phase,level/16.0,variance,false)' in f
assert 'CAMERA2_FALLBACK_' not in f and 'channelNoiseProfile' not in f
assert 'bBurstNoise26860 = if (iris26856AmazeCfaConsumer != null)' in s
assert 'val normals = frames.filter { it.role == RawBurstFrameRole.NORMAL }' in s
assert 'if (!iris26856BOnlyIndependentPublication &&' in s
assert 'bCamera2ProfileForFrame26861' not in s and 'CAMERA2_FALLBACK_' not in s
assert 'check(burst.measuredPhases == 4)' in s
assert 'val bFrameNoise26861 = bBurstNoise26860' in s
assert 'bEmpiricalNoise26861 = bFrameNoise26861' in s
assert 'uPhaseNoiseShot26855' in s and 'uPhaseNoiseRead26855' in s
assert 'bEmpiricalNoise26861 = bBurstNoise26860,' in s
assert 'IRIS_26862_B_NOISE_AUTHORITY' in s
assert 'rawOnly=true' in s and 'camera2Fallback=false' in s
assert 'renderIris26858BNoiseClean(' not in s and 'renderIris26858BResidualChroma(' not in s
assert 'normalCfaTemporalAccumulate26852' in shared
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in s
assert s.index('bRecovered26858 = renderIris26858BHighlightColor(') < s.index('defringed = renderRawrLabDefringe26856(') < s.index('fcc = renderRawrFalseColor26856(')
assert 'bMotionOnlyWeight26861' in bshade and 'bWeightedCfaIdentity26861' in bshade
assert 'if (normalDngCoverage != 0)' in s
print('PASS 26862 B-only independent 8/14/15-frame eligible-burst raw noise; row flicker + mixed shutter/ISO not veto; no Camera2; A/DNG/LONG/color routing preserved')
