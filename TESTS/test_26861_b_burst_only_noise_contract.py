#!/usr/bin/env python3
"""Permanent B burst-noise ownership regression against a full compiled candidate.

This must FAIL on successful 26860 for precise pooled-Camera2 defects, PASS
only after source-level true consumer verification. Preserves A-shared shader.
"""
from pathlib import Path
import re, sys
root = Path(sys.argv[1]) if len(sys.argv)>1 else Path('app')
p = root / 'src/main/java/com/hinnka/mycamera/processor'
noise = (p/'GlesIris26860BBurstNoise.kt').read_text()
stack = (p/'GlesMgcRawSpatialStacker.kt').read_text()
bshade = (p/'GlesIris26858BNoiseHighlight.kt').read_text()
shared = (p/'GlesMgcRawSabreShaders.kt').read_text()
assert not re.search(r'\b(cameraShot|cameraRead|CAMERA2_FALLBACK|BURST_PARTIAL_FIT)\b', noise), '26860 B fitter still consumes Camera2 profile/shape'
assert 'inheritedMoment*phaseVar/baseMean' not in bshade, '26860 B spatial smoother rescales pooled Camera2 moment'
assert 'bCfaNoise = ' not in bshade and 'bResidualChroma = ' not in bshade, '26860 B spatial denoisers remain linked'
assert not re.search(r'\brenderIris26858BNoiseClean\s*\(', stack), 'old pre-AMaZE smoother still runs'
assert not re.search(r'\brenderIris26858BResidualChroma\s*\(', stack), 'old post-AMaZE residual smoother still runs'
assert 'normalCfaTemporalAccumulate26852' in shared, 'protected shared A/B 26852 owner missing'
assert 'bEmpiricalNoise26861 = bBurstNoise26860,' in stack, 'B temporal CFA not fed burst noise'
assert 'uniform4fv(program, "uPhaseNoiseShot26855", bEmpiricalNoise26861?.shot ?: shot26855)' in stack and 'bEmpiricalNoise26861 = bFrameNoise26861' in stack, 'B noise not bound to actual frame-model active temporal shader'
assert 'uniform4fv(program, "uPhaseNoiseRead26855", bEmpiricalNoise26861?.read ?: read26855)' in stack, 'B read variance not bound to active temporal shader'
assert 'bReferenceGuide26861' in stack and 'bCurrentCovariance26861' in stack and 'bTemporalWeight26861' in stack, 'missing B-only guide/rejection/variance inputs'
assert 'bEmpiricalCalibration26861(' in stack and 'bEmpiricalKernelTuning26861(' in stack, 'B temporals do not consume measured coefficients'
assert 'IRIS_26861_B_NOISE_AUTHORITY' in stack and 'selected=${chosen.mode}' in stack, 'no actual B noise source logging'
assert 'renderIris26861BWeightedIdentity(' in stack and 'bWeightedCfaIdentity26861' in bshade, 'unmodified weighted temporal CFA not routed to AMaZE'
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in stack, 'highlight owner removed'
assert stack.index('bRecovered26858 = renderIris26858BHighlightColor(') < stack.index('defringed = renderRawrLabDefringe26856(') < stack.index('fcc = renderRawrFalseColor26856('), 'protected color algorithm order changed'
assert 'renderSabreNormalDngMerge(' in stack and 'if (normalDngCoverage != 0)' in stack, 'DNG ownership modified'
# On pure B, DNG and legacy A/long coverage still use inherited frameWeight.
sc = stack[stack.index('if (frame.role == RawBurstFrameRole.NORMAL) {\n                    if (highlightShortOneTunnel26604)'):]
sc = sc[:sc.index('if (iris26858BClipVotes != 0)')]
assert 'bTemporalWeight26861' not in sc and 'weight = frameWeight,' in sc, 'B empirical rejection leaked into protected DNG coverage'
assert 'bEmpiricalNoise26861' not in (p/'GlesMgcRawSabreShaders.kt').read_text(), 'shared A/B source changed'
assert re.search(r'\bfun fitBlocks\(', noise), 'empirical shot/read variance fitter missing'
print('PASS 26861 B measured-only producer-to-consumer wiring; no Camera2 pooled B denoisers; A/DNG/LONG isolated')
# IRIS_26861_CAMERA2_LAST_RESORT_AFTER_REAL_BURST: accepted scope correction.
# Never choose Camera2 when 4-phase burst fit is fully identifiable. Never
# apply a Camera2 scaling ratio to partial burst coefficients, and never use
# a pooled Camera2 variance moment as a B post-AMaZE denoise authority.
assert 'if (burst.mode == "BURST_ALL_PHASE_SHOT_READ") burst else' in stack
assert 'check(normals.all { bCamera2ProfileForFrame26861(it, burst.mode) != null })' in stack
assert 'IRIS_26861_NO_VALID_NOISE_PROFILE' in stack
assert 'frame.channelNoiseProfile' in stack[stack.index('private fun bCamera2ProfileForFrame26861('):stack.index('private fun bEmpiricalCalibration26861(')]
assert 'RawNoiseModel::fromCamera2NoiseProfile' in stack[stack.index('private fun bCamera2ProfileForFrame26861('):stack.index('private fun bEmpiricalCalibration26861(')]
assert 'RawNoiseModelResolver.resolve(' not in stack[stack.index('private fun bCamera2ProfileForFrame26861('):stack.index('private fun bEmpiricalCalibration26861(')]
assert 'physicalRead[c]=profile.read[phase].coerceAtLeast(1.0e-10f)' not in stack
assert 'bBurstNoise26860.measuredPhases < 4' not in stack
assert 'bEmpiricalNoise26861 = bFrameNoise26861' in stack
assert 'bEmpiricalCalibration26861(calibration,bFrameNoise26861,exposureScale)' in stack
assert 'bFrameNoise26861,' in stack
assert 'IRIS_26861_B_NOISE_AUTHORITY' in stack
assert 'camera2Fallback=${chosen.mode.startsWith("CAMERA2_FALLBACK_")}' in stack
assert 'CAMERA2_FALLBACK_' not in noise, 'RAW burst estimator must never borrow Camera2 to complete a fit'
print('PASS Camera2 is a fully separate per-frame only LAST RESORT after reliable full 4-phase fit, no fake floor or pooled moment')
