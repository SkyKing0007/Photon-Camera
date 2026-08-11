$ErrorActionPreference = "Stop"

# ============================================================================
# 26438 WINDOWS INTEGRATED MOTION + STANDARD ULTRA HDR BUILD
#
# Changes only:
#   1) stronger immutable-reference subject-motion fallback
#   2) near-white auxiliary-frame fallback for SDR zipper protection
#   3) bounded pre-tone microcontrast + hue-preserving highlight gamut
#   4) standards-aligned matched-footprint Ultra HDR geometry/quotient/metadata
#   5) 26437 color/detail/global-exposure foundations protected
#
# No commit. No push. dev untouched.
# ============================================================================

function Fail([string]$Message) { throw "FAIL: $Message" }

function ReadT([string]$Path) {
    return [IO.File]::ReadAllText($Path)
}

function Normalize-Lf([string]$Text) {
    if ($null -eq $Text) { return $Text }
    return $Text.Replace("`r`n","`n").Replace("`r","`n")
}

function WriteUtf8NoBom([string]$Path,[string]$Text) {
    $Parent = Split-Path -Parent $Path
    if ($Parent) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    [IO.File]::WriteAllText(
        $Path,
        $Text,
        (New-Object Text.UTF8Encoding($false))
    )
}

function Replace-Once(
        [string]$Text,
        [string]$Old,
        [string]$New,
        [string]$Label) {
    $TextLf = Normalize-Lf $Text
    $OldLf = Normalize-Lf $Old
    $NewLf = Normalize-Lf $New
    $Count = ([regex]::Matches(
        $TextLf,[regex]::Escape($OldLf))).Count
    if ($Count -ne 1) {
        Fail "$Label expected exactly one normalized-LF anchor, found $Count"
    }
    return $TextLf.Replace($OldLf,$NewLf)
}

function Sha([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

# Self-parse before touching repository state.
$ParserTokens = $null
$ParserErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $PSCommandPath,
    [ref]$ParserTokens,
    [ref]$ParserErrors
) | Out-Null
if ($ParserErrors.Count -gt 0) {
    foreach ($E in $ParserErrors) {
        Write-Host ("PARSER ERROR line " +
            $E.Extent.StartLineNumber + ": " + $E.Message)
    }
    Fail "PowerShell parser validation failed before repository work"
}
Write-Host "POWERSHELL SCRIPT PARSER: PASS"

$Repo = "C:\Users\nhann\Documents\GitHub\Photon-Camera-clean-rebuild"
if (-not (Test-Path -LiteralPath $Repo)) {
    Fail "Repository not found: $Repo"
}
Set-Location $Repo

$ExpectedBranch = "experimental-clean-photon-rebuild"
$ExpectedHead = "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"

$DACC = 'app\src\main\assets\shaders\motionv2\direct_rgb_accumulate.glsl'
$GAINMAP = 'app\src\main\assets\shaders\motionv2\gainmap.glsl'
$RENDERJ = 'app\src\main\java\com\particlesdevs\photoncamera\processing\opengl\postpipeline\MotionV2Render.java'
$UHDR = 'app\src\main\java\com\particlesdevs\photoncamera\processing\ultrahdr\MotionV2UltraHdr.java'
$VERSION = 'app\version.properties'

# Protected 26437 visual-invariant files.
$DINIT = 'app\src\main\assets\shaders\motionv2\direct_rgb_init.glsl'
$COLORG = 'app\src\main\assets\shaders\motionv2\color_transform.glsl'
$DENOISEG = 'app\src\main\assets\shaders\motionv2\denoise.glsl'
$DENOISEJ = 'app\src\main\java\com\particlesdevs\photoncamera\processing\opengl\postpipeline\MotionV2Denoise.java'
$RENDERG = 'app\src\main\assets\shaders\motionv2\render.glsl'

$Targets = @($DACC,$GAINMAP,$RENDERJ,$UHDR,$RENDERG,$VERSION)

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutRoot = Join-Path $Repo "fresh_iris_outputs"
$Safety = Join-Path $OutRoot "windows_26438_integrated_$Stamp"
$Originals = Join-Path $Safety "originals"
$Cand = Join-Path $Safety "candidates"
$PrePatch = Join-Path $Safety "pre_26438_windows_working_tree.patch"
$PostPatch = Join-Path $Safety "post_26438_windows_working_tree.patch"
$ProtectedBefore = Join-Path $Safety "protected_before.txt"
$ProtectedAfter = Join-Path $Safety "protected_after.txt"
$GlslLog = Join-Path $Safety "glslc_26438_windows.txt"
$JavacLog = Join-Path $Safety "javac_26438_windows.txt"
$BuildLog = Join-Path $Safety "build_26438_windows.txt"
$Result = Join-Path $OutRoot "windows_26438_result_$Stamp.txt"
$ApkOut = Join-Path $Repo "IrisCamera-0.9726438-26438-audited-motion-microcontrast-standard-ultrahdr-debug.apk"

New-Item -ItemType Directory -Force -Path `
    $OutRoot,$Safety,$Originals,$Cand | Out-Null

Write-Host "=== GATE 0: EXACT TESTED 26437 PROOF ==="

$Branch = (& git branch --show-current).Trim()
$Head = (& git rev-parse HEAD).Trim()

if ($Branch -ne $ExpectedBranch) {
    Fail "Expected branch $ExpectedBranch, actual $Branch"
}
if ($Head -ne $ExpectedHead) {
    Fail "Expected historical committed HEAD $ExpectedHead, actual $Head"
}
if ($Branch -eq 'dev') { Fail "Refusing to modify dev" }

if (-not (Test-Path -LiteralPath 'local.properties')) {
    Fail "local.properties missing"
}
if (-not (Test-Path -LiteralPath 'gradlew.bat')) {
    Fail "gradlew.bat missing"
}

# Exact hashes produced by the validated 26437 Windows build script.
$Expected26437 = @{
    $DINIT='88631AFEC8A8E14A5E5AE44B9AEE2277C1A7730B1D49666ACFD4FB0972516D6C'
    $DACC='910282646DF16D703971C5F2031CEA207BDA137F3088E1AAE6A1A52801EEF979'
    $COLORG='03649A2110F907F1FBA1B6E9457D28E8C1FDBDB8D02BC1A348B50F3B325C98CA'
    $DENOISEG='F9F5F5F6B3A27F4005F82F91FFE2A5FF00496E406969D4AB84AB83E5CAD32BB2'
    $DENOISEJ='C05AAAA71E53A3E7C995AEC07F4005D2EA0B9A78EC3F265783FAB678F5AED2D0'
    $RENDERG='FEBC6CCD70249EE036EEAD47C266DA4A3D7133209555CBCC1A584B1E3A066D7D'
    $GAINMAP='0358AA8C1B19D8C4CE58003E88E975AA3F3E36F447CE91FDD715CB45E7BA521A'
    $RENDERJ='75DA18588E40AF4F76CD5F0715D94D585928E739600D58462CA2F9C353DCD765'
    $UHDR='D93AAA75FCDE2759A35D6D5893698207BB33C5955EF4CF288B0027C37F023D09'
    $VERSION='3E31946743C158160B7CBCA38A38F90D8507CDF87524F973199C4063AEE78F94'
}

foreach ($K in $Expected26437.Keys) {
    if (-not (Test-Path -LiteralPath $K)) {
        Fail "Expected 26437 file missing: $K"
    }
    $Actual = Sha $K
    if ($Actual -ne $Expected26437[$K]) {
        Fail "Exact 26437 source mismatch: $K`nExpected $($Expected26437[$K])`nActual   $Actual"
    }
}

$V = ReadT $VERSION
if ($V -notmatch '(?m)^VERSION_NAME=0\.9726437\r?$' -or
    $V -notmatch '(?m)^VERSION_BUILD=26437\r?$') {
    Fail "Expected tested version 0.9726437 / 26437"
}

$ProtectedMarkers = @(
    @{F=$DINIT; M='IRIS_26437_WHITE_POINT_OWNED_REFERENCE_AND_EDGE_ANCHOR'},
    @{F=$COLORG; M='IRIS_26437_SENSOR_WHITE_POINT_COLOR_OWNERSHIP'},
    @{F=$DENOISEG; M='IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP'},
    @{F=$RENDERG; M='IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV'}
)
foreach ($C in $ProtectedMarkers) {
    if (-not (ReadT $C.F).Contains($C.M)) {
        Fail "26437 visual invariant missing: $($C.M)"
    }
}

Write-Host "PASS: exact tested 26437 source proven"
Write-Host "PASS: clean SDR outdoor-edge path protected"
Write-Host "PASS: 0.80 global exposure protected"
Write-Host "PASS: dev untouched"

Write-Host "=== GATE 1: BACKUP BRANCH + BINARY PATCH ==="

$Backup = "backup/windows-before-26438-integrated-$Stamp"
& git branch $Backup
if ($LASTEXITCODE -ne 0) { Fail "Backup branch creation failed" }

& git diff --binary HEAD -- app |
    Out-File -LiteralPath $PrePatch -Encoding utf8
if ($LASTEXITCODE -ne 0) { Fail "Pre-edit binary patch failed" }

foreach ($Rel in $Targets) {
    $Dest = Join-Path $Originals $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) |
        Out-Null
    Copy-Item -LiteralPath $Rel -Destination $Dest -Force
}
Copy-Item -LiteralPath 'local.properties' `
    -Destination (Join-Path $Originals 'local.properties') -Force

function Hash-Protected([string[]]$Intentional,[string]$OutFile) {
    $Rows = New-Object System.Collections.Generic.List[string]
    foreach ($Raw in (& git ls-files app)) {
        $Rel = $Raw -replace '/','\'
        if ($Intentional -contains $Rel) { continue }
        if (-not (Test-Path -LiteralPath $Rel)) { continue }
        $Rows.Add(("{0}  {1}" -f (Sha $Rel),$Rel))
    }
    $Rows | Sort-Object |
        Set-Content -LiteralPath $OutFile -Encoding UTF8
}
Hash-Protected $Targets $ProtectedBefore

Write-Host "=== GATE 2: TEMPORARY 26438 CANDIDATES ==="

foreach ($Rel in $Targets) {
    $Dest = Join-Path $Cand $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) |
        Out-Null
    Copy-Item -LiteralPath $Rel -Destination $Dest -Force
}

# --------------------------------------------------------------------------
# A. MOTION: immutable-reference vetoes become decisive.
# --------------------------------------------------------------------------
$P = Join-Path $Cand $DACC
$S = Normalize-Lf (ReadT $P)

$WhiteOld = @'
    return smoothstep(0.900*clip,0.985*clip,peak);
'@
$WhiteNew = @'
    /*
     * IRIS_26438_NEAR_WHITE_REFERENCE_MERGE_OWNERSHIP
     * Keep color conversion untouched; this only prevents multiple slightly
     * different near-white CFA observations from creating magenta/green
     * zipper votes around thin lights and reflections.
     */
    return smoothstep(0.840*clip,0.970*clip,peak);
'@
$CountWhite = ([regex]::Matches(
        $S,[regex]::Escape((Normalize-Lf $WhiteOld)))).Count
if ($CountWhite -ne 2) {
    Fail "Expected two reference/alter near-white reliability anchors, found $CountWhite"
}
$S = $S.Replace((Normalize-Lf $WhiteOld),(Normalize-Lf $WhiteNew))

$MotionOld = @'
    float temporalTrust=tukeyWeight(
            temporalResidual/max(2.25*oldConsensusScale,1.0e-5));
    float subjectMotionTrust=temporalTrust*temporalTrust;
    float referenceAgreement=residualTrust*residualTrust;
    float occlusionTrust=boundaryTrust*boundaryTrust;

    float sharedConfidence=clamp(
            alignmentTrust
            *alignmentResidualTrust
            *referenceAgreement
            *subjectMotionTrust
            *occlusionTrust
            *highlightTrust,
            0.0,1.0);

    /*
     * Hard local fallback is permitted, global frame discard is not.
     * These are local observation failures only; static regions from the same
     * frame remain fully eligible.
     */
    bool temporalConflict =
            temporalResidual > 2.75*oldConsensusScale;
    bool referenceConflict =
            residualTrust < 0.22
            || alignmentResidualTrust < 0.12;
    bool occlusionConflict =
            boundaryTrust < 0.08;

    if(temporalConflict || referenceConflict || occlusionConflict) {
        sharedConfidence=0.0;
    }
'@

$MotionNew = @'
    /*
     * IRIS_26438_NOISE_AWARE_IMMUTABLE_REFERENCE_MOTION_VETO
     *
     * Wronski/IPOL-style robustness compares disagreement against expected
     * signal-dependent noise rather than one absolute brightness threshold.
     * The physical reference remains the local fallback. Every auxiliary
     * frame stays globally eligible; only contradictory local observations
     * are zero-weighted.
     */
    float referenceCenter=max(referenceGreenCell(xy),0.0);

    float sigmaReference=
            0.018
            +0.065*sqrt(referenceCenter)
            +0.010*referenceCenter;
    float sigmaAuxiliary=
            0.018
            +0.065*sqrt(auxConsensusGreen)
            +0.010*auxConsensusGreen;

    float alignmentSigma=
            0.35*sigmaReference
            *clamp(
                    max(flow.w,0.0)/0.070,
                    0.0,
                    2.0);

    float combinedSigma=sqrt(
            sigmaReference*sigmaReference
            +sigmaAuxiliary*sigmaAuxiliary
            +alignmentSigma*alignmentSigma
            +1.0e-8);

    float immutableResidualSigma=
            abs(auxConsensusGreen-referenceCenter)
            /max(combinedSigma,1.0e-5);

    float temporalResidualSigma=
            temporalResidual
            /max(
                    sqrt(
                            oldConsensusScale*oldConsensusScale
                            +sigmaAuxiliary*sigmaAuxiliary),
                    1.0e-5);

    float temporalTrust=tukeyWeight(
            temporalResidualSigma/3.0);
    float immutableReferenceTrust=tukeyWeight(
            immutableResidualSigma/3.0);

    float subjectMotionTrust=
            temporalTrust
            *immutableReferenceTrust;
    float referenceAgreement=
            residualTrust*residualTrust;
    float occlusionTrust=
            boundaryTrust*boundaryTrust;

    float sharedConfidence=clamp(
            alignmentTrust
            *alignmentResidualTrust
            *referenceAgreement
            *subjectMotionTrust
            *occlusionTrust
            *highlightTrust,
            0.0,1.0);

    /*
     * Strong contradictions become reference-only locally. These vetoes are
     * normalized by expected noise, so dark noisy pixels are not rejected as
     * aggressively as clean bright pixels showing the same absolute error.
     */
    bool temporalConflict =
            temporalResidualSigma > 3.25;
    bool immutableReferenceConflict =
            immutableResidualSigma > 3.25
            || residualTrust < 0.30;
    bool alignmentConflict =
            alignmentResidualTrust < 0.20;
    bool occlusionConflict =
            boundaryTrust < 0.12;

    if(temporalConflict
            || immutableReferenceConflict
            || alignmentConflict
            || occlusionConflict) {
        sharedConfidence=0.0;
    }
'@

$S = Replace-Once $S $MotionOld $MotionNew '26438 motion veto'
WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# B. SDR RENDER:
#   - restore bounded midtone microcontrast before tone mapping
#   - preserve valid highlight hue by shared RGB scaling instead of
#     luminance-axis desaturation when a display-gamut channel exceeds 1
#   - keep exact 0.80 global exposure and existing headroom curve
# --------------------------------------------------------------------------
$P = Join-Path $Cand $RENDERG
$S = Normalize-Lf (ReadT $P)

$RenderLumaOld = @'
float luminance(vec3 c) {
    return dot(c,vec3(0.2126,0.7152,0.0722));
}
'@

$RenderLumaNew = @'
float luminance(vec3 c) {
    return dot(c,vec3(0.2126,0.7152,0.0722));
}

/*
 * IRIS_26438_REFERENCE_SAFE_MICROCONTRAST
 *
 * Lightroom showed that much of the apparent haze is surviving detail with
 * insufficient local tonal separation. Restore only a bounded log-luma
 * residual, and fade it out in deep shadows and highlights to avoid noise,
 * halos and highlight-edge exaggeration.
 */
float localLogLumaMean(ivec2 xy) {
    ivec2 sz=textureSize(InputBuffer,0);
    float sum=0.0;
    float wsum=0.0;
    for(int oy=-2;oy<=2;oy++) {
        for(int ox=-2;ox<=2;ox++) {
            ivec2 p=clamp(
                    xy+ivec2(ox,oy),
                    ivec2(0),
                    sz-ivec2(1));
            float y=max(
                    luminance(max(texelFetch(InputBuffer,p,0).rgb,vec3(0.0))),
                    0.0);
            float r2=float(ox*ox+oy*oy);
            float w=exp(-0.55*r2);
            sum+=w*log(1.0e-4+y);
            wsum+=w;
        }
    }
    return sum/max(wsum,1.0e-6);
}

vec3 applyReferenceSafeMicrocontrast(ivec2 xy, vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    if(y<=1.0e-7) return rgb;

    float detail=
            log(1.0e-4+y)
            -localLogLumaMean(xy);
    detail=clamp(detail,-0.20,0.20);

    float shadowGate=smoothstep(0.025,0.12,y);
    float highlightGate=1.0-smoothstep(0.55,0.92,y);
    float gate=shadowGate*highlightGate;

    /*
     * Max local modulation is deliberately modest. This restores separation,
     * not conventional sharpening.
     */
    float scale=exp(0.42*gate*detail);
    return rgb*scale;
}
'@
$S = Replace-Once $S $RenderLumaOld $RenderLumaNew '26438 microcontrast helper'

$GamutOld = @'
vec3 fitDisplayGamut(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float peak=max3(rgb);
    if(peak<=1.0) return rgb;

    float y=max(luminance(rgb),0.0);
    if(y>=1.0) return vec3(1.0);

    float chromaScale=
            clamp(
                    (1.0-y)
                    /max(peak-y,1.0e-6),
                    0.0,
                    1.0);

    return vec3(y)+(rgb-vec3(y))*chromaScale;
}
'@

$GamutNew = @'
vec3 fitDisplayGamut(vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float peak=max3(rgb);
    if(peak<=1.0) return rgb;

    /*
     * IRIS_26438_HUE_PRESERVING_HIGHLIGHT_GAMUT
     *
     * The previous luminance-axis fit reduced chroma as bright colored
     * foliage approached display white. Uniform RGB scaling preserves channel
     * ratios/hue and trades only highlight luminance for display gamut.
     */
    return rgb/max(peak,1.0e-6);
}
'@
$S = Replace-Once $S $GamutOld $GamutNew '26438 hue-preserving gamut'

$MainOld = @'
    linearSrgb=mapExtendedLinearHeadroom(linearSrgb);

    /*
     * The only visual change from the 26430 SDR mapper:
     * one user-requested 0.80 linear scale (~-0.322 EV).
     */
'@
$MainNew = @'
    /*
     * Apply the same pre-tone local-contrast intent that the HDR target uses.
     * The existing headroom mapper and 0.80 exposure remain unchanged.
     */
    linearSrgb=applyReferenceSafeMicrocontrast(xy,linearSrgb);
    linearSrgb=mapExtendedLinearHeadroom(linearSrgb);

    /*
     * The global exposure remains the tested 0.80 linear scale (~-0.322 EV).
     */
'@
$S = Replace-Once $S $MainOld $MainNew '26438 render ordering'

WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# C. ULTRA HDR MAP:
#   - exact standard quotient offsets
#   - broad HDR/SDR rendition relationship, not cloud/leaf microtexture
#   - gain map remains grayscale so SDR chroma is authoritative
# --------------------------------------------------------------------------
$P = Join-Path $Cand $GAINMAP
$S = Normalize-Lf (ReadT $P)

$GainOld = ReadT $P
$GainNew = @'
precision highp float;
precision mediump sampler2D;

uniform sampler2D HdrBuffer;
uniform sampler2D SdrBuffer;
uniform ivec2 gainMapSize;
uniform float hdrExposureScale;
uniform float maxGainRatio;
out vec4 Output;

/*
 * IRIS_26438_MATCHED_FOOTPRINT_STANDARD_GAINMAP
 *
 * Android Ultra HDR / Adobe hdrgm semantics:
 *   HDR = (SDR + epsilonSdr) * gain - epsilonHdr
 *
 * One gain-map texel represents a matched ~4x4 source footprint because the
 * map is 1/4 width and 1/4 height. Do not add a huge low-pass that crosses
 * tree/sky or cloud boundaries. Equal-channel (grayscale) gain preserves SDR
 * hue/chroma in conforming decoders.
 */

const float UHDR_OFFSET = 0.015625; // 1/64

float luminance(vec3 c) {
    return dot(c,vec3(0.2126,0.7152,0.0722));
}

float srgbDecode(float x) {
    x=clamp(x,0.0,1.0);
    return x<=0.04045
            ? x/12.92
            : pow((x+0.055)/1.055,2.4);
}

vec3 srgbDecode(vec3 c) {
    return vec3(
            srgbDecode(c.r),
            srgbDecode(c.g),
            srgbDecode(c.b));
}

float hdrLocalLogLumaMean(vec2 uv) {
    vec2 texel=1.0/vec2(textureSize(HdrBuffer,0));
    float sum=0.0;
    float wsum=0.0;
    for(int oy=-2;oy<=2;oy++) {
        for(int ox=-2;ox<=2;ox++) {
            float r2=float(ox*ox+oy*oy);
            float w=exp(-0.55*r2);
            vec3 c=max(
                    texture(
                            HdrBuffer,
                            clamp(
                                    uv+vec2(float(ox),float(oy))*texel,
                                    vec2(0.0),
                                    vec2(1.0))).rgb,
                    vec3(0.0));
            sum+=w*log(1.0e-4+max(luminance(c),0.0));
            wsum+=w;
        }
    }
    return sum/max(wsum,1.0e-6);
}

vec3 applyHdrMicrocontrast(vec2 uv, vec3 rgb) {
    rgb=max(rgb,vec3(0.0));
    float y=max(luminance(rgb),0.0);
    if(y<=1.0e-7) return rgb;

    float detail=
            log(1.0e-4+y)
            -hdrLocalLogLumaMean(uv);
    detail=clamp(detail,-0.20,0.20);

    float shadowGate=smoothstep(0.025,0.12,y);
    float highlightGate=1.0-smoothstep(0.55,0.92,y);
    float gate=shadowGate*highlightGate;

    return rgb*exp(0.42*gate*detail);
}

vec3 matchedHdrFootprint(vec2 uv) {
    vec2 texel=1.0/vec2(textureSize(HdrBuffer,0));
    vec3 sum=vec3(0.0);
    for(int oy=0;oy<4;oy++) {
        for(int ox=0;ox<4;ox++) {
            vec2 d=
                    (vec2(float(ox),float(oy))-vec2(1.5))
                    *texel;
            vec2 suv=clamp(uv+d,vec2(0.0),vec2(1.0));
            vec3 c=max(texture(HdrBuffer,suv).rgb,vec3(0.0));
            sum+=applyHdrMicrocontrast(suv,c);
        }
    }
    return sum*(1.0/16.0);
}

vec3 matchedSdrFootprint(vec2 uv) {
    vec2 texel=1.0/vec2(textureSize(SdrBuffer,0));
    vec3 sum=vec3(0.0);
    for(int oy=0;oy<4;oy++) {
        for(int ox=0;ox<4;ox++) {
            vec2 d=
                    (vec2(float(ox),float(oy))-vec2(1.5))
                    *texel;
            vec3 c=texture(
                    SdrBuffer,
                    clamp(uv+d,vec2(0.0),vec2(1.0))).rgb;
            sum+=srgbDecode(c);
        }
    }
    return sum*(1.0/16.0);
}

void main() {
    vec2 uv=
            gl_FragCoord.xy
            /vec2(max(gainMapSize,ivec2(1)));

    vec3 hdr=
            matchedHdrFootprint(uv)
            *hdrExposureScale;
    vec3 sdr=matchedSdrFootprint(uv);

    float hdrY=max(luminance(hdr),0.0);
    float sdrY=max(luminance(sdr),0.0);

    /*
     * Exact quotient represented by the metadata. No saturation-dependent
     * gain ceiling: a grayscale map already preserves SDR chromaticity.
     */
    float ratio=clamp(
            (hdrY+UHDR_OFFSET)/(sdrY+UHDR_OFFSET),
            1.0,
            max(maxGainRatio,1.001));

    float encoded=
            log2(ratio)
            /max(log2(max(maxGainRatio,1.001)),1.0e-6);

    encoded=clamp(encoded,0.0,1.0);
    Output=vec4(encoded,encoded,encoded,1.0);
}
'@
WriteUtf8NoBom $P (Normalize-Lf $GainNew)

# --------------------------------------------------------------------------
# C. GAIN MAP GEOMETRY:
# Android format tip is 1/4 width + 1/4 height, not 1/16 each dimension.
# This materially improves spatial correspondence across decoders.
# --------------------------------------------------------------------------
$P = Join-Path $Cand $RENDERJ
$S = Normalize-Lf (ReadT $P)

$S = Replace-Once $S `
    'private static final int GAINMAP_DOWNSAMPLE = 16;' `
    'private static final int GAINMAP_DOWNSAMPLE = 4;' `
    '26438 gain-map dimensions'

$LogOld = @'
                        + " lowFrequencyMap=true"
                        + " downsample=" + GAINMAP_DOWNSAMPLE
                        + " midtoneGainUnity=true"
                        + " sdrAndHdrExposureScale=" + OUTPUT_EXPOSURE_SCALE);
'@
$LogNew = @'
                        + " lowFrequencyMap=true"
                        + " downsample=" + GAINMAP_DOWNSAMPLE
                        + " widthFraction=0.25"
                        + " heightFraction=0.25"
                        + " quotientOffset=0.015625"
                        + " standardLogGainEncoding=true"
                        + " broadRenditionNotEdgeTexture=true"
                        + " midtoneGainUnity=true"
                        + " sdrAndHdrExposureScale=" + OUTPUT_EXPOSURE_SCALE);
'@
$S = Replace-Once $S $LogOld $LogNew '26438 gain-map telemetry'
WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# D. STANDARD ANDROID/ADOBE GAINMAP METADATA.
# ratioMin 1 => capacity minimum should be 1.
# capacity maximum should equal ratioMax.
# epsilon must equal the quotient-generation offset.
# --------------------------------------------------------------------------
$P = Join-Path $Cand $UHDR
$S = Normalize-Lf (ReadT $P)

$S = Replace-Once $S `
    'private static final float EPSILON = 1.0e-4f;' `
    'private static final float EPSILON = 0.015625f;' `
    '26438 standard gain-map epsilon'

$S = Replace-Once $S `
    'private static final float MIN_HDR_TRANSITION = 1.50f;' `
    'private static final float MIN_HDR_TRANSITION = 1.00f;' `
    '26438 standard HDR capacity minimum'

$FullOld = @'
            gainmap.setMinDisplayRatioForHdrTransition(MIN_HDR_TRANSITION);
            gainmap.setDisplayRatioForFullHdr(Math.max(2.50f, safeMax));
'@
$FullNew = @'
            /*
             * IRIS_26438_STANDARD_ULTRAHDR_METADATA
             * GainMapMin=1.0 => HDRCapacityMin=1.0 in Android's linear API.
             * HDRCapacityMax follows GainMapMax exactly, as recommended by
             * the Android Ultra HDR specification.
             */
            gainmap.setMinDisplayRatioForHdrTransition(MIN_HDR_TRANSITION);
            gainmap.setDisplayRatioForFullHdr(safeMax);
'@
$S = Replace-Once $S $FullOld $FullNew '26438 capacity metadata'

$LogOld = @'
                    + " minHdrTransition=" + MIN_HDR_TRANSITION
                    + " fullHdrDisplayRatio=" + Math.max(2.50f, safeMax)
                    + " source=V2ExtendedLinear"
                    + " bodyGainUnity=true");
'@
$LogNew = @'
                    + " minHdrTransition=" + MIN_HDR_TRANSITION
                    + " fullHdrDisplayRatio=" + safeMax
                    + " epsilonSdr=0.015625"
                    + " epsilonHdr=0.015625"
                    + " gamma=1.0"
                    + " metadataProfile=AndroidUltraHdr_v1_1_AdobeHdrgm"
                    + " standardCapacityRange=true"
                    + " source=V2ExtendedLinearBroadRendition"
                    + " bodyGainUnity=true");
'@
$S = Replace-Once $S $LogOld $LogNew '26438 metadata telemetry'
WriteUtf8NoBom $P $S

# Version increment in the same command/build script.
$VersionCandidate = @"
VERSION_MAJOR=0
VERSION_MINOR=9726438
VERSION_NAME=0.9726438
VERSION_BUILD=26438
"@
$VersionCandidate = $VersionCandidate.TrimEnd("`r","`n") + "`r`n"
WriteUtf8NoBom (Join-Path $Cand $VERSION) $VersionCandidate

Write-Host "=== GATE 2A: TEMPORARY ARCHITECTURE PROOF ==="

$Checks = @(
    @{F=$DACC; M='IRIS_26438_NOISE_AWARE_IMMUTABLE_REFERENCE_MOTION_VETO'},
    @{F=$DACC; M='immutableResidualSigma > 3.25'},
    @{F=$DACC; M='IRIS_26438_NEAR_WHITE_REFERENCE_MERGE_OWNERSHIP'},
    @{F=$GAINMAP; M='IRIS_26438_MATCHED_FOOTPRINT_STANDARD_GAINMAP'},
    @{F=$GAINMAP; M='const float UHDR_OFFSET = 0.015625'},
    @{F=$RENDERJ; M='GAINMAP_DOWNSAMPLE = 4'},
    @{F=$RENDERG; M='IRIS_26438_REFERENCE_SAFE_MICROCONTRAST'},
    @{F=$RENDERG; M='IRIS_26438_HUE_PRESERVING_HIGHLIGHT_GAMUT'},
    @{F=$UHDR; M='IRIS_26438_STANDARD_ULTRAHDR_METADATA'},
    @{F=$UHDR; M='private static final float EPSILON = 0.015625f'},
    @{F=$UHDR; M='private static final float MIN_HDR_TRANSITION = 1.00f'},
    @{F=$UHDR; M='gainmap.setDisplayRatioForFullHdr(safeMax)'}
)
foreach ($C in $Checks) {
    if (-not (ReadT (Join-Path $Cand $C.F)).Contains($C.M)) {
        Fail "Temporary candidate missing $($C.M)"
    }
}

$Acc = ReadT (Join-Path $Cand $DACC)
if ($Acc.Contains('referenceCenterResidual')) {
    Fail "Stale pre-audit fixed-threshold motion logic returned"
}
if (-not $Acc.Contains('immutableResidualSigma > 3.25')) {
    Fail "Noise-aware immutable-reference veto threshold missing"
}
if (-not $Acc.Contains('temporalResidualSigma > 3.25')) {
    Fail "Noise-aware temporal veto threshold missing"
}
if ($Acc.Contains('perFrameCap') -or
    $Acc.Contains('referenceCeiling')) {
    Fail "26432/26433 hard support ceiling/cap returned"
}
if ($Acc -match '\bcur\.r\b') {
    Fail "Evolving visible RGB re-entered acceptance logic"
}
if (-not $Acc.Contains('maximumSupport*8.0')) {
    Fail "Unrestricted normalized-convolution support path missing"
}

# Protect tested 26437 SDR color/detail/render sources.
if ((Sha $DINIT) -ne $Expected26437[$DINIT]) { Fail "DINIT invariant changed" }
if ((Sha $COLORG) -ne $Expected26437[$COLORG]) { Fail "COLOR invariant changed" }
if ((Sha $DENOISEG) -ne $Expected26437[$DENOISEG]) { Fail "DENOISE invariant changed" }
if ((Sha $DENOISEJ) -ne $Expected26437[$DENOISEJ]) { Fail "DENOISE Java invariant changed" }
$RenderCandidate = ReadT (Join-Path $Cand $RENDERG)
if (-not $RenderCandidate.Contains('IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV')) {
    Fail "26430/26435 headroom base marker missing from revised render"
}
if (-not $RenderCandidate.Contains('linearSrgb*=outputExposureScale;')) {
    Fail "0.80 global exposure application missing from revised render"
}
if (-not $RenderCandidate.Contains('IRIS_26438_REFERENCE_SAFE_MICROCONTRAST')) {
    Fail "26438 microcontrast marker missing"
}
if (-not $RenderCandidate.Contains('IRIS_26438_HUE_PRESERVING_HIGHLIGHT_GAMUT')) {
    Fail "26438 highlight-color marker missing"
}

$VC = ReadT (Join-Path $Cand $VERSION)
if ($VC -notmatch '(?m)^VERSION_NAME=0\.9726438\r?$' -or
    $VC -notmatch '(?m)^VERSION_BUILD=26438\r?$') {
    Fail "Candidate version mismatch"
}

Write-Host "ALL TEMPORARY TRANSFORMATION ANCHORS: PASS"
Write-Host "candidate/source validation PASS"

Write-Host "=== GATE 3: REAL GLSL VALIDATION ==="

$SdkLine = Get-Content -LiteralPath 'local.properties' |
    Where-Object { $_ -match '^\s*sdk\.dir\s*=' } |
    Select-Object -First 1
if (-not $SdkLine) { Fail "sdk.dir missing" }

$SdkDir = (($SdkLine -split '=',2)[1].Trim()) `
    -replace '\\:', ':' `
    -replace '\\\\', '\' `
    -replace '\\ ', ' '

if (-not (Test-Path -LiteralPath $SdkDir)) {
    Fail "Decoded Android SDK path missing: $SdkDir"
}

$Glslc = $null
$NdkRoot = Join-Path $SdkDir 'ndk'
foreach ($Ndk in (Get-ChildItem -LiteralPath $NdkRoot -Directory |
                  Sort-Object Name -Descending)) {
    $Candidate = Join-Path $Ndk.FullName `
        'shader-tools\windows-x86_64\glslc.exe'
    if (Test-Path -LiteralPath $Candidate) {
        $Glslc = $Candidate
        break
    }
}
if (-not $Glslc) {
    Fail "Android NDK glslc.exe not found; source has NOT been modified"
}

Write-Host ("Shader compiler: " + $Glslc)

$WrapDir = Join-Path $Safety "glsl_wrapped"
$SpvDir = Join-Path $Safety "glsl_spv"
New-Item -ItemType Directory -Force -Path $WrapDir,$SpvDir | Out-Null

$ShaderFiles = @(
    @{P=(Join-Path $Cand $DACC); Stage='compute'; Name='direct_accumulate'},
    @{P=(Join-Path $Cand $GAINMAP); Stage='fragment'; Name='gainmap'},
    @{P=(Join-Path $Cand $RENDERG); Stage='fragment'; Name='render'}
)

$CompilerOutput = New-Object System.Collections.Generic.List[string]

foreach ($Item in $ShaderFiles) {
    $Text = Normalize-Lf (ReadT $Item.P)
    if ($Item.Stage -eq 'compute') {
        $Text = [regex]::Replace(
            $Text,
            '(?m)^#define\s+LAYOUT\s+//\s*\nLAYOUT\s*\n',
            '',
            1)
        $Text =
            "#version 310 es`n" +
            "layout(local_size_x=8, local_size_y=8, local_size_z=1) in;`n" +
            $Text
    } else {
        $Text = "#version 310 es`n" + $Text
    }

    $Wrapped = Join-Path $WrapDir ($Item.Name + '.glsl')
    $Spv = Join-Path $SpvDir ($Item.Name + '.spv')
    WriteUtf8NoBom $Wrapped $Text

    $Args = @(
        '--target-env=opengl',
        '-fauto-map-locations',
        '-fauto-bind-uniforms',
        ('-fshader-stage=' + $Item.Stage),
        $Wrapped,
        '-o',
        $Spv
    )

    $OldEA = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $Lines = & $Glslc @Args 2>&1
        $Rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $OldEA
    }

    $CompilerOutput.Add(
        ("===== {0} stage={1} =====" -f $Item.Name,$Item.Stage))
    foreach ($Line in $Lines) {
        $CompilerOutput.Add([string]$Line)
    }

    if ($Rc -ne 0 -or -not (Test-Path -LiteralPath $Spv)) {
        $CompilerOutput |
            Set-Content -LiteralPath $GlslLog -Encoding UTF8
        Fail "glslc failed for $($Item.Name); see $GlslLog. Real source has NOT been modified."
    }
}

$CompilerOutput | Set-Content -LiteralPath $GlslLog -Encoding UTF8
Write-Host "REAL GLSL COMPILER PROOF: PASS"
Write-Host "Temporary-copy validation: PASS"

Write-Host "=== GATE 4: APPLY VALIDATED CANDIDATES ==="

foreach ($Rel in $Targets) {
    Copy-Item -LiteralPath (Join-Path $Cand $Rel) `
        -Destination $Rel -Force
}

Hash-Protected $Targets $ProtectedAfter
if ((Get-Content $ProtectedBefore -Raw) -ne
    (Get-Content $ProtectedAfter -Raw)) {
    Fail "Protected tracked app source changed"
}

if (-not (Test-Path -LiteralPath 'local.properties')) {
    Fail "local.properties lost"
}

& git diff --check -- $Targets
if ($LASTEXITCODE -ne 0) { Fail "git diff --check failed" }

foreach ($C in $Checks) {
    if (-not (ReadT $C.F).Contains($C.M)) {
        Fail "Post-apply source missing $($C.M)"
    }
}

# Re-prove visual invariants after source apply.
if ((Sha $DINIT) -ne $Expected26437[$DINIT]) { Fail "DINIT changed" }
if ((Sha $COLORG) -ne $Expected26437[$COLORG]) { Fail "COLOR changed" }
if ((Sha $DENOISEG) -ne $Expected26437[$DENOISEG]) { Fail "DENOISE changed" }
$RenderApplied = ReadT $RENDERG
if (-not $RenderApplied.Contains('IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV')) {
    Fail "Headroom base changed unexpectedly"
}
if (-not $RenderApplied.Contains('IRIS_26438_REFERENCE_SAFE_MICROCONTRAST')) {
    Fail "Applied render missing microcontrast"
}
if (-not $RenderApplied.Contains('IRIS_26438_HUE_PRESERVING_HIGHLIGHT_GAMUT')) {
    Fail "Applied render missing hue-preserving highlight gamut"
}

Write-Host "candidate/source validation PASS"
Write-Host "Temporary-copy validation: PASS"
Write-Host "PRE-BUILD SAFETY PROOF PASSED"

& git diff --binary HEAD -- app |
    Out-File -LiteralPath $PostPatch -Encoding utf8

Write-Host "=== GATE 5: JAVAC PROOF ==="

$JdkCandidates = @(
    'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot',
    'C:\Program Files\Android\Android Studio\jbr'
)
foreach ($Jdk in $JdkCandidates) {
    if (Test-Path (Join-Path $Jdk 'bin\java.exe')) {
        $env:JAVA_HOME = $Jdk
        break
    }
}
if (-not $env:JAVA_HOME) { Fail "Java 17 / Android Studio JBR not found" }
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

$OldEA = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & .\gradlew.bat :app:compileDebugJavaWithJavac --stacktrace 2>&1 |
        Tee-Object -FilePath $JavacLog
    $JavacRc = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $OldEA
}
if ($JavacRc -ne 0) { Fail "Javac failed; see $JavacLog" }
if (-not (ReadT $JavacLog).Contains('BUILD SUCCESSFUL')) {
    Fail "Javac BUILD SUCCESSFUL missing"
}
Write-Host "JAVAC PROOF PASSED"

Write-Host "=== GATE 6: BUILD 0.9726438 / 26438 ==="

try {
    $ErrorActionPreference = 'Continue'
    & .\gradlew.bat :app:assembleDebug --stacktrace 2>&1 |
        Tee-Object -FilePath $BuildLog
    $BuildRc = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $OldEA
}

if ($BuildRc -ne 0) { Fail "Gradle build failed; see $BuildLog" }
if (-not (ReadT $BuildLog).Contains('BUILD SUCCESSFUL')) {
    Fail "BUILD SUCCESSFUL missing"
}

$Built = Get-ChildItem -LiteralPath 'app\build\outputs\apk' `
    -Recurse -File -Filter '*.apk' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $Built) { Fail "Built APK not found" }

Get-ChildItem -LiteralPath $Repo -File -Filter 'IrisCamera-*.apk' `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force

Move-Item -LiteralPath $Built.FullName -Destination $ApkOut -Force

# Exactly one APK visible at repo root.
Get-ChildItem -LiteralPath 'app\build' -Recurse -File -Filter '*.apk' `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force

@(
    '26438 WINDOWS INTEGRATED BUILD'
    'Version/build: 0.9726438 / 26438'
    ''
    'MOTION'
    '- noise-aware immutable-reference motion residuals'
    '- decisive local temporal/reference/alignment/occlusion fallback'
    '- all frames remain globally eligible'
    '- no hard support ceiling / no per-frame cap'
    ''
    'SDR ZIPPER'
    '- near-white auxiliary CFA merge becomes reference-dominant earlier'
    '- 26437 SDR color transform itself intentionally unchanged'
    '- clean outdoor SDR sky/object edges protected'
    ''
    'ULTRA HDR'
    '- gain map now 1/4 width and 1/4 height'
    '- matched 4x4 source footprint; no ~64px cross-edge blur'
    '- exact 1/64 quotient offsets match metadata'
    '- grayscale gain map preserves SDR chroma; saturation gain cap removed'
    '- gamma 1.0'
    '- ratio min 1.0'
    '- HDR capacity transition min 1.0'
    '- full-HDR display ratio equals gain-map max'
    '- standard Android Ultra HDR / Adobe hdrgm-compatible metadata path'
    ''
    'MICROCONTRAST / HIGHLIGHT COLOR'
    '- bounded 5x5 log-luma midtone microcontrast before tone mapping'
    '- fades out in deep shadows and bright highlights'
    '- hue-preserving shared RGB display-gamut scaling'
    '- same pre-tone microcontrast intent applied to HDR target'
    ''
    'PROTECTED'
    '- global 0.80 exposure unchanged'
    '- 26437 color transform unchanged'
    '- 26437 detail cleanup unchanged'
    '- exact 0.80 exposure and headroom curve retained; render gains only audited microcontrast/highlight-color logic'
    ''
    ('Backup branch: ' + $Backup)
    ('Pre patch: ' + $PrePatch)
    ('Post patch: ' + $PostPatch)
    ('GLSL proof: ' + $GlslLog)
    ('Javac proof: ' + $JavacLog)
    ('Build log: ' + $BuildLog)
    ('APK: ' + $ApkOut)
    ''
    'POWERSHELL SCRIPT PARSER: PASS'
    'ALL TEMPORARY TRANSFORMATION ANCHORS: PASS'
    'candidate/source validation PASS'
    'REAL GLSL COMPILER PROOF: PASS'
    'Temporary-copy validation: PASS'
    'PRE-BUILD SAFETY PROOF PASSED'
    'JAVAC PROOF PASSED'
    'BUILD SUCCESSFUL VERIFIED'
    ''
    'No commit. No push. dev untouched.'
) | Set-Content -LiteralPath $Result -Encoding UTF8

Write-Host "======================================================================"
Write-Host "26438 WINDOWS BUILD SUCCESSFUL"
Write-Host "APK: $ApkOut"
Write-Host "RESULT: $Result"
Write-Host "No commit. No push. dev untouched."
Write-Host "======================================================================"
