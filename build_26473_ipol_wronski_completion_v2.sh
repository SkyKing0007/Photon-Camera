#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="b0e9d196b8c0918acf7c91dcaa338515552d090e"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26472-before-26473-ipol-completion"
BACKUP_TARGET="8aa6d4e71402761672115571203b3dcb099a615b"
PRECURSOR_SCRIPT="build_26472_wronski_reference_sdr_authoritative_uhdr_v6.sh"
PRECURSOR_BLOB="180cdec27785231ccac8fe2e1cf2d2e279de33fa"

OLD_VERSION="0.9726472"
OLD_BUILD="26472"
NEW_VERSION="0.9726473"
NEW_BUILD="26473"

OUTDIR="build_26473_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-ipol-wronski-completion-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

AUDIT="$OUTDIR/26473_source_audit.txt"
REPORT="$OUTDIR/26473_build_report.txt"
HASH_INITIAL="$OUTDIR/26473_protected_initial.sha256"
HASH_26472="$OUTDIR/26473_protected_26472_base.sha256"
HASH_AFTER="$OUTDIR/26473_protected_after.sha256"
PREPATCH="$OUTDIR/26473_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26473_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26473_source.patch"

exec > >(tee "$AUDIT") 2>&1

echo "=== 26473 GUARDED IPOL / WRONSKI COMPLETION BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] \
  || fail "backup=$REMOTE_BACKUP expected=$BACKUP_TARGET"
pass "backup branch exact successful 26472 V6 checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties \
  || fail "application source changed before 26473"
pass "application source unchanged before 26473"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] \
  || fail "26472 V6 precursor blob mismatch"
pass "26472 V6 precursor exact"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_INITIAL"
sha256sum app/version.properties >> "$HASH_INITIAL"
pass "binary pre-edit patch created before source modification"
pass "initial protected-file hashes captured before source modification"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PRECURSOR="$TMP/26472_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26472_precursor_outputs" <<'PY_PRECURSOR'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
a='OUTDIR="build_26472_outputs"'
r='OUTDIR="'+sys.argv[2]+'"'
if t.count(a)!=1:
    raise SystemExit(f"26472 precursor OUTDIR anchor count={t.count(a)}")
p.write_text(t.replace(a,r,1))
print("26472 precursor OUTDIR rewrite: PASS")
PY_PRECURSOR
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26472 transform-only precursor syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726472$' app/version.properties || fail "26472 version name"
grep -q '^VERSION_BUILD=26472$' app/version.properties || fail "26472 version build"
for marker in \
  IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
  IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE \
  IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
  IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
  IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY; do
  grep -Rqs "$marker" app/src/main || fail "26472 lineage missing $marker"
done
pass "26472 V6 tested application lineage reproduced"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26472"
sha256sum app/version.properties >> "$HASH_26472"

RECON="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
ALIGNJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
NOISEJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java"

ALIGNGUIDE="app/src/main/assets/shaders/motionv2/alignment_guide.glsl"
PYRGAUSS="app/src/main/assets/shaders/motionv2/mfsr_pyramid_gaussian.glsl"
BLOCKMATCH="app/src/main/assets/shaders/motionv2/mfsr_block_match.glsl"
ICA="app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl"
ROBUST="app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl"

COV="app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl"
ERODE="app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl"
INIT="app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl"
ACCUM="app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl"
REFMERGE="app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl"
FINALIZE="app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl"
GAINMAP="app/src/main/assets/shaders/motionv2/gainmap.glsl"
RENDER="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
ULTRAHDR="app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"
VERSION="app/version.properties"

for f in "$RECON" "$ALIGNJAVA" "$ALIGNGUIDE" "$BLOCKMATCH" "$ICA" "$ROBUST" "$VERSION"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done
for f in "$COV" "$ERODE" "$INIT" "$ACCUM" "$REFMERGE" "$FINALIZE" "$GAINMAP" "$RENDER" "$ULTRAHDR"; do
  mkdir -p "$TMP/candidate/$(dirname "$f")"
  cp "$f" "$TMP/candidate/$f"
done
mkdir -p "$TMP/candidate/$(dirname "$NOISEJAVA")"
mkdir -p "$TMP/candidate/$(dirname "$PYRGAUSS")"

cat > "$TMP/candidate/$NOISEJAVA" <<'JAVA_NOISE'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES
 *
 * Deterministic mobile implementation of public IPOL fast_monte_carlo.py:
 * affine variance, 1001 brightness entries, explicit [0,1] clipping,
 * Monte-Carlo in nonlinear clipping zones, and variance-domain interpolation
 * through the linear middle range.
 */
public final class MotionV2IpolNoiseCurve {
    private static final int LEVELS = 1000;
    private static final int PATCHES = 8192;
    private static final double TOL = 3.0;

    private MotionV2IpolNoiseCurve() {}

    public static final class Curve {
        public final ByteBuffer rgba32f;
        public final float referenceMean;
        public final float snr;
        public final int nonlinearLowEnd;
        public final int nonlinearHighStart;

        Curve(ByteBuffer rgba32f, float referenceMean, float snr,
              int nonlinearLowEnd, int nonlinearHighStart) {
            this.rgba32f = rgba32f;
            this.referenceMean = referenceMean;
            this.snr = snr;
            this.nonlinearLowEnd = nonlinearLowEnd;
            this.nonlinearHighStart = nonlinearHighStart;
        }
    }

    public static Curve build(float alpha, float beta, ByteBuffer referenceRaw,
                              Point rawSize, float[] blackLevel, float whiteLevel,
                              float canonicalGain) {
        alpha = Math.max(alpha, 1.0e-9f);
        beta = Math.max(beta, 0.0f);

        float[] sigma = new float[LEVELS + 1];
        float[] diff = new float[LEVELS + 1];

        double tolSq = TOL * TOL;
        double xmin = tolSq / 2.0
                * (alpha + Math.sqrt(tolSq * alpha * alpha + 4.0 * beta));
        double xmaxTerm = 2.0 + tolSq * alpha;
        double xmaxDisc = Math.max(
                0.0, xmaxTerm * xmaxTerm - 4.0 * (1.0 + tolSq * beta));
        double xmax = (xmaxTerm - Math.sqrt(xmaxDisc)) / 2.0;

        int imin = clampInt((int)Math.ceil(xmin * LEVELS) + 1, 0, LEVELS);
        int imax = clampInt((int)Math.floor(xmax * LEVELS) - 1, 0, LEVELS);

        long seed = 0x9e3779b97f4a7c15L
                ^ Float.floatToIntBits(alpha)
                ^ ((long)Float.floatToIntBits(beta) << 32);

        if (imin >= imax) {
            Rng rng = new Rng(seed);
            for (int i = 0; i <= LEVELS; i++) {
                float[] sd = unitaryMc(
                        alpha, beta, i / (float)LEVELS, 2048, rng);
                sigma[i] = sd[0];
                diff[i] = sd[1];
            }
            imin = LEVELS;
            imax = LEVELS;
        } else {
            Rng rng = new Rng(seed);
            for (int i = 0; i <= imin; i++) {
                float[] sd = unitaryMc(
                        alpha, beta, i / (float)LEVELS, PATCHES, rng);
                sigma[i] = sd[0];
                diff[i] = sd[1];
            }
            for (int i = imax; i <= LEVELS; i++) {
                float[] sd = unitaryMc(
                        alpha, beta, i / (float)LEVELS, PATCHES, rng);
                sigma[i] = sd[0];
                diff[i] = sd[1];
            }

            final float sigmaLo2 = sigma[imin] * sigma[imin];
            final float sigmaHi2 = sigma[imax] * sigma[imax];
            final float diffLo2 = diff[imin] * diff[imin];
            final float diffHi2 = diff[imax] * diff[imax];
            final float denom = Math.max(
                    1.0f, (imax + 1.0f) - (imin - 1.0f));

            for (int i = imin; i <= imax; i++) {
                float t = (i - (imin - 1.0f)) / denom;
                sigma[i] = (float)Math.sqrt(Math.max(
                        0.0f, sigmaLo2 + t * (sigmaHi2 - sigmaLo2)));
                diff[i] = (float)Math.sqrt(Math.max(
                        0.0f, diffLo2 + t * (diffHi2 - diffLo2)));
            }
        }

        float referenceMean = estimateReferenceMean(
                referenceRaw, rawSize, blackLevel, whiteLevel, canonicalGain);
        int noiseIndex = clampInt(
                Math.round(LEVELS * clamp01(referenceMean)), 0, LEVELS);
        float noiseStd = Math.max(sigma[noiseIndex], 1.0e-8f);
        float snr = Math.max(
                6.0f, Math.min(30.0f, referenceMean / noiseStd));

        ByteBuffer tex = ByteBuffer.allocateDirect((LEVELS + 1) * 16)
                .order(ByteOrder.nativeOrder());
        for (int i = 0; i <= LEVELS; i++) {
            tex.putFloat(sigma[i]);
            tex.putFloat(diff[i]);
            tex.putFloat(i / (float)LEVELS);
            tex.putFloat(1.0f);
        }
        tex.position(0);
        return new Curve(tex, referenceMean, snr, imin, imax);
    }

    private static float estimateReferenceMean(
            ByteBuffer raw, Point size, float[] black, float white,
            float exposure) {
        if (raw == null || size == null || size.x <= 0 || size.y <= 0)
            return 0.18f;

        ByteBuffer view = raw.duplicate().order(ByteOrder.nativeOrder());
        int samples = Math.min(view.capacity() / 2, size.x * size.y);
        if (samples <= 0) return 0.18f;

        double sum = 0.0;
        int used = 0;
        for (int index = 0; index < samples; index++) {
            int y = index / size.x;
            int x = index - y * size.x;
            int c = ((y & 1) << 1) | (x & 1);
            float b = black != null && black.length >= 4 ? black[c] : 0.0f;
            float den = Math.max(white - b, 1.0f);
            float code = Short.toUnsignedInt(view.getShort(index * 2));
            float value = Math.max((code - b) / den, 0.0f) * exposure;
            sum += Math.min(value, 1.0f);
            used++;
        }
        return used > 0 ? (float)(sum / used) : 0.18f;
    }

    private static float[] unitaryMc(
            float alpha, float beta, float brightness, int patches, Rng rng) {
        double stdAcc = 0.0;
        double diffAcc = 0.0;
        double noiseStd = Math.sqrt(Math.max(
                brightness * alpha + beta, 0.0));

        for (int p = 0; p < patches; p++) {
            double sum1 = 0.0, sum2 = 0.0;
            double sq1 = 0.0, sq2 = 0.0;
            for (int k = 0; k < 9; k++) {
                double a = clamp01(
                        brightness + noiseStd * rng.gaussian());
                double b = clamp01(
                        brightness + noiseStd * rng.gaussian());
                sum1 += a; sum2 += b;
                sq1 += a * a; sq2 += b * b;
            }
            double mean1 = sum1 / 9.0;
            double mean2 = sum2 / 9.0;
            double var1 = Math.max(
                    sq1 / 9.0 - mean1 * mean1, 0.0);
            double var2 = Math.max(
                    sq2 / 9.0 - mean2 * mean2, 0.0);
            stdAcc += 0.5 * (Math.sqrt(var1) + Math.sqrt(var2));
            diffAcc += Math.abs(mean1 - mean2);
        }
        return new float[] {
                (float)(stdAcc / patches),
                (float)(diffAcc / patches)
        };
    }

    private static float clamp01(float x) {
        return Math.max(0.0f, Math.min(1.0f, x));
    }
    private static double clamp01(double x) {
        return Math.max(0.0, Math.min(1.0, x));
    }
    private static int clampInt(int x, int lo, int hi) {
        return Math.max(lo, Math.min(hi, x));
    }

    private static final class Rng {
        private long state;
        private boolean hasSpare;
        private double spare;

        Rng(long seed) {
            state = seed != 0L ? seed : 0x6a09e667f3bcc909L;
        }

        private double uniform() {
            long x = state;
            x ^= x << 13;
            x ^= x >>> 7;
            x ^= x << 17;
            state = x;
            long bits = (x >>> 11) & ((1L << 53) - 1);
            return (bits + 1.0) / ((1L << 53) + 2.0);
        }

        double gaussian() {
            if (hasSpare) {
                hasSpare = false;
                return spare;
            }
            double u1 = uniform();
            double u2 = uniform();
            double r = Math.sqrt(-2.0 * Math.log(Math.max(u1, 1.0e-15)));
            double theta = 2.0 * Math.PI * u2;
            spare = r * Math.sin(theta);
            hasSpare = true;
            return r * Math.cos(theta);
        }
    }
}
JAVA_NOISE

cat > "$TMP/candidate/$ALIGNGUIDE" <<'GLSL_GUIDE'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp image2D;

uniform sampler2D InputCfa;
layout(r32f, binding=0) uniform highp writeonly image2D OutputGuide;
uniform int guideScale;
uniform float signalScale;

/*
 * IRIS_26473_IPOL_FFT_GREY_EQUIVALENT
 *
 * Public IPOL suppresses Bayer carrier frequencies by retaining the central
 * half of the RAW FFT spectrum. Motion V2's flow grid is already the 2x2
 * packed-CFA grid, so the Android GPU equivalent forms the physical all-channel
 * quad mean, then a compact circular low-pass. This replaces the old green-only
 * guide and preserves the same anti-CFA / band-limited alignment role.
 */
ivec2 wrapCoord(ivec2 p, ivec2 s) {
    return ivec2((p.x % s.x + s.x) % s.x,
                 (p.y % s.y + s.y) % s.y);
}
float quadMean(ivec2 p) {
    ivec2 s=textureSize(InputCfa,0);
    vec4 v=max(texelFetch(InputCfa,wrapCoord(p,s),0),vec4(0.0));
    return 0.25*(v.r+v.g+v.b+v.a)/max(signalScale,1.0e-6);
}
void main() {
    ivec2 q=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(q,os))) return;

    const float k[5]=float[5](1.0,4.0,6.0,4.0,1.0);
    float sum=0.0,ws=0.0;
    for(int y=-2;y<=2;y++) for(int x=-2;x<=2;x++) {
        float w=k[x+2]*k[y+2];
        sum += w*quadMean(q+ivec2(x,y));
        ws += w;
    }
    imageStore(OutputGuide,q,vec4(sum/max(ws,1.0e-8),0.0,0.0,0.0));
}
GLSL_GUIDE

cat > "$TMP/candidate/$PYRGAUSS" <<'GLSL_GAUSS'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputGuide;
layout(r32f,binding=0) uniform highp writeonly image2D OutputGuide;
uniform int factor;
uniform int direction;

/*
 * IRIS_26473_IPOL_FACTOR_DEPENDENT_GAUSSIAN_PYRAMID
 * Public cuda_downsample(): sigma=factor*0.5, radius=round(4*sigma).
 */
float sampleCircular(ivec2 p){
    ivec2 s=textureSize(InputGuide,0);
    ivec2 q=ivec2((p.x%s.x+s.x)%s.x,(p.y%s.y+s.y)%s.y);
    return texelFetch(InputGuide,q,0).r;
}
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(p,os))) return;

    int f=max(factor,1);
    float sigma=max(0.5*float(f),0.5);
    int radius=min(8,int(floor(4.0*sigma+0.5)));
    ivec2 center=direction==0?p:p*f;

    float sum=0.0,ws=0.0;
    for(int i=-8;i<=8;i++){
        if(abs(i)>radius) continue;
        float w=exp(-float(i*i)/(2.0*sigma*sigma));
        ivec2 q=center+(direction==0?ivec2(i,0):ivec2(0,i));
        sum+=w*sampleCircular(q);
        ws+=w;
    }
    imageStore(OutputGuide,p,vec4(sum/max(ws,1.0e-8),0.0,0.0,0.0));
}
GLSL_GAUSS

cat > "$TMP/candidate/$BLOCKMATCH" <<'GLSL_BLOCK'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D PreviousFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int searchRadius;
uniform int distanceMetric;
uniform int hasPrevious;
uniform float previousToCurrentScale;

/* IRIS_26473_IPOL_ALIGNMENT_BOUNDARY_SEMANTICS */
float sampleReference(ivec2 p) {
    ivec2 s=levelSize;
    ivec2 q=ivec2((p.x%s.x+s.x)%s.x,(p.y%s.y+s.y)%s.y);
    return texelFetch(ReferenceGuide,q,0).r;
}
float sampleMoving(ivec2 p) {
    if(any(lessThan(p,ivec2(0)))||any(greaterThanEqual(p,levelSize)))
        return 0.0;
    return texelFetch(MovingGuide,p,0).r;
}
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec2 pred=vec2(0.0);
    if(hasPrevious!=0) {
        vec2 uv=(vec2(tile)+0.5)/vec2(grid);
        pred=texture(PreviousFlow,clamp(uv,vec2(0.0),vec2(1.0))).xy
                *previousToCurrentScale;
    }
    ivec2 ipred=ivec2(round(pred));
    float best=3.402823e38;
    ivec2 bestShift=ipred;

    for(int sy=-4;sy<=4;sy++) for(int sx=-4;sx<=4;sx++) {
        if(abs(sx)>searchRadius || abs(sy)>searchRadius) continue;
        ivec2 sh=ipred+ivec2(sx,sy);
        float e=0.0;
        int n=0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 rp=tile*tileSize+ivec2(xx,yy);
                float a=sampleReference(rp);
                float b=sampleMoving(rp+sh);
                float d=a-b;
                e += distanceMetric==0 ? abs(d) : d*d;
                n++;
            }
        }
        e/=float(max(n,1));
        if(e<best) { best=e; bestShift=sh; }
    }
    float confidence=exp(-best/max(1e-5,0.02+best));
    imageStore(OutputFlow,tile,vec4(vec2(bestShift),confidence,best));
}
GLSL_BLOCK

cat > "$TMP/candidate/$ICA" <<'GLSL_ICA'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D BlockFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int iterations;

float movingAt(vec2 p) {
    if(p.x<0.0||p.y<0.0||p.x>float(levelSize.x-1)||p.y>float(levelSize.y-1))
        return 0.0;
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(MovingGuide,p0,0).r,
                texelFetch(MovingGuide,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(MovingGuide,ivec2(p0.x,p1.y),0).r,
                texelFetch(MovingGuide,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float refCircular(ivec2 p) {
    ivec2 q=ivec2((p.x%levelSize.x+levelSize.x)%levelSize.x,
                  (p.y%levelSize.y+levelSize.y)%levelSize.y);
    return texelFetch(ReferenceGuide,q,0).r;
}
vec2 publicSobel(ivec2 p){
    return vec2(
        refCircular(p+ivec2(1,0))-refCircular(p-ivec2(1,0)),
        refCircular(p+ivec2(0,1))-refCircular(p-ivec2(0,1)));
}

/* IRIS_26473_IPOL_ICA_EXACT_UPDATE */
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 seed=texelFetch(BlockFlow,tile,0);
    vec2 flow=seed.xy;

    float H00=0.0,H01=0.0,H11=0.0;
    for(int yy=0;yy<64;yy++) {
        if(yy>=tileSize) continue;
        for(int xx=0;xx<64;xx++) {
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            vec2 g=publicSobel(p);
            H00+=g.x*g.x; H01+=g.x*g.y; H11+=g.y*g.y;
        }
    }
    float det=H00*H11-H01*H01;
    if(abs(det)<1.0e-10){
        imageStore(OutputFlow,tile,seed);
        return;
    }

    for(int iter=0;iter<3;iter++) {
        if(iter>=iterations) break;
        float b0=0.0,b1=0.0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 p=tile*tileSize+ivec2(xx,yy);
                vec2 g=publicSobel(p);
                float residual=movingAt(vec2(p)+flow)-refCircular(p);
                b0 += -g.x*residual;
                b1 += -g.y*residual;
            }
        }
        vec2 d=vec2(
                ( H11*b0-H01*b1)/det,
                (-H01*b0+H00*b1)/det);
        flow+=d;
    }
    imageStore(OutputFlow,tile,vec4(flow,seed.z,seed.w));
}
GLSL_ICA

cat > "$TMP/candidate/$ROBUST" <<'GLSL_ROBUST'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D noiseCurve;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D alterCfa;
layout(r32f,binding=2) uniform highp writeonly image2D outRobustness;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform int tileSizeRaw;
uniform float wbR;
uniform float wbG;
uniform float wbB;

int colorOf(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
vec3 guideReference(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(referenceCfa,q);
    float s[4]=float[4](v.r,v.g,v.b,v.a);
    vec3 o=vec3(0); float ng=0.0;
    for(int i=0;i<4;i++){
        int c=colorOf(i);
        float x=s[i]/(c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6)));
        if(c==0)o.r=x; else if(c==2)o.b=x; else {o.g+=x;ng+=1.0;}
    }
    o.g/=max(ng,1.0); return o;
}
vec3 guideAlter(ivec2 q){
    q=clamp(q,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(alterCfa,q);
    float s[4]=float[4](v.r,v.g,v.b,v.a);
    vec3 o=vec3(0); float ng=0.0;
    for(int i=0;i<4;i++){
        int c=colorOf(i);
        float x=s[i]/(c==0?max(wbR,1e-6):(c==2?max(wbB,1e-6):max(wbG,1e-6)));
        if(c==0)o.r=x; else if(c==2)o.b=x; else {o.g+=x;ng+=1.0;}
    }
    o.g/=max(ng,1.0); return o;
}
void localStatsRef(ivec2 q,out vec3 mu,out vec3 var){
    vec3 s=vec3(0),ss=vec3(0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        vec3 v=guideReference(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
        s+=v;ss+=v*v;
    }
    mu=s/9.0;var=max(ss/9.0-mu*mu,vec3(0));
}
vec3 localMeanAlt(ivec2 q){
    vec3 s=vec3(0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)
        s+=guideAlter(clamp(q+ivec2(x,y),ivec2(0),rawHalf-ivec2(1)));
    return s/9.0;
}
float dogson(float x){
    float a=abs(x);
    if(a<=0.5) return -2.0*a*a+1.0;
    if(a<=1.5) return a*a-2.5*a+1.5;
    return 0.0;
}
void dogsonRef(vec2 lr,out vec3 mu,out vec3 var){
    ivec2 center=ivec2(round(lr)); vec3 sm=vec3(0),sv=vec3(0); float sw=0.0;
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));
        float w=dogson(float(q.x)-lr.x)*dogson(float(q.y)-lr.y);
        vec3 m,v;localStatsRef(q,m,v);sm+=m*w;sv+=v*w;sw+=w;
    }
    mu=sm/max(sw,1e-8);var=sv/max(sw,1e-8);
}
vec3 dogsonAlt(vec2 lr){
    ivec2 center=ivec2(round(lr)); vec3 sm=vec3(0); float sw=0.0;
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawHalf-ivec2(1));
        float w=dogson(float(q.x)-lr.x)*dogson(float(q.y)-lr.y);
        sm+=localMeanAlt(q)*w;sw+=w;
    }
    return sm/max(sw,1e-8);
}
vec2 denseRawFlowAt(ivec2 rawP){
    ivec2 q=clamp(rawP>>1,ivec2(0),rawHalf-ivec2(1));
    return 2.0*texelFetch(flowTexture,q,0).xy;
}
vec2 ipolNoise(float brightness){
    int idx=clamp(int(round(1000.0*clamp(brightness,0.0,1.0))),0,1000);
    return texelFetch(noiseCurve,ivec2(idx,0),0).rg;
}

/* IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawSize))) return;
    vec2 rawFlow=denseRawFlowAt(p);
    vec2 refLR=(vec2(p)+0.5)/2.0-0.5;
    vec2 altLR=(vec2(p)+rawFlow+0.5)/2.0-0.5;
    if(altLR.x<0.0||altLR.y<0.0||
       altLR.x>=float(rawHalf.x)||altLR.y>=float(rawHalf.y)){
        imageStore(outRobustness,p,vec4(0)); return;
    }

    vec3 refMu,refVar;dogsonRef(refLR,refMu,refVar);
    vec3 altMu=dogsonAlt(altLR);
    vec3 dp=abs(refMu-altMu);

    float d2=0.0,sigma2=0.0;
    for(int c=0;c<3;c++){
        vec2 curve=ipolNoise(refMu[c]);
        float sigmaT=max(curve.x,1.0e-8);
        float dT=max(curve.y,1.0e-8);
        float dp2=dp[c]*dp[c];
        float shrink=dp2/max(dp2+dT*dT,1.0e-12);
        d2+=dp2*shrink*shrink;
        sigma2+=max(refVar[c],sigmaT*sigmaT);
    }

    vec2 mn=vec2(3.402823e38),mx=vec2(-3.402823e38);
    int ts=max(tileSizeRaw,1);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(
            p+ivec2(x,y)*ts,ivec2(0),rawSize-ivec2(1));
        vec2 f=denseRawFlowAt(q); mn=min(mn,f);mx=max(mx,f);
    }
    vec2 span=mx-mn;
    float S=dot(span,span)>0.8*0.8?2.0:12.0;
    float R=clamp(
        S*exp(-d2/max(sigma2,1.0e-12))-0.12,0.0,1.0);
    imageStore(outRobustness,p,vec4(R));
}
GLSL_ROBUST

cat > "$TMP/candidate/$ALIGNJAVA" <<'JAVA_ALIGN'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION
 * IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE
 *
 * Preserves the proven 26467 prepared-reference API and burst lifetime while
 * completing the remaining public/IPOL alignment differences.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p, int d) {
        return new Point(
                Math.max(1, (p.x + d - 1) / d),
                Math.max(1, (p.y + d - 1) / d));
    }

    public static final class PreparedReference implements AutoCloseable {
        private final Point rawHalf;
        private final int cfaPattern;
        private final float signalScale;
        private final float snr;
        private GLTexture[] levels;

        private PreparedReference(
                Point rawHalf,
                int cfaPattern,
                float signalScale,
                float snr,
                GLTexture[] levels) {
            this.rawHalf = new Point(rawHalf);
            this.cfaPattern = cfaPattern;
            this.signalScale = signalScale;
            this.snr = snr;
            this.levels = levels;
        }

        @Override
        public void close() {
            if (levels == null) return;
            for (GLTexture t : levels) {
                if (t != null) t.close();
            }
            levels = null;
        }
    }

    private static GLTexture[] buildGuidePyramid(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            GLProg glProg,
            GLTexture cfa) {

        final int[] stepFactor = new int[] {1, 2, 4, 4};
        GLTexture[] guide = new GLTexture[4];
        GLTexture[] tmp = new GLTexture[4];

        try {
            guide[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", cfa);
            glProg.setTextureCompute("OutputGuide", guide[0], true);
            glProg.computeAuto(rawHalf,1);

            Point prev = rawHalf;
            for (int l=1;l<4;l++) {
                Point levelSize = divCeil(prev, stepFactor[l]);

                tmp[l] = new GLTexture(
                        prev,
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                guide[l] = new GLTexture(
                        levelSize,
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);

                // Public cuda_downsample(): separable Gaussian with
                // sigma=factor/2, radius=4*sigma, then decimation.
                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setVar("direction", 0);
                glProg.setTexture("InputGuide", guide[l-1]);
                glProg.setTextureCompute("OutputGuide", tmp[l], true);
                glProg.computeAuto(prev,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_gaussian", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setVar("direction", 1);
                glProg.setTexture("InputGuide", tmp[l]);
                glProg.setTextureCompute("OutputGuide", guide[l], true);
                glProg.computeAuto(levelSize,1);

                tmp[l].close();
                tmp[l] = null;
                prev = levelSize;
            }
            return guide;
        } catch (Throwable t) {
            for (GLTexture texture : tmp) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            for (GLTexture texture : guide) {
                if (texture != null) {
                    try { texture.close(); } catch (Throwable ignored) {}
                }
            }
            throw t;
        }
    }

    public static PreparedReference prepareReference(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa) {

        long start = System.currentTimeMillis();
        GLTexture[] ref = buildGuidePyramid(
                rawHalf, cfaPattern, signalScale, glProg, referenceCfa);

        Log.d(TAG,
                "IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE"
                + " elapsedMs=" + (System.currentTimeMillis() - start)
                + " levels=4"
                + " reusedAcrossAuxiliaries=true"
                + " ipol26473=true");

        return new PreparedReference(
                rawHalf, cfaPattern, signalScale, snr, ref);
    }

    public static MotionV2Alignment.Result alignPrepared(
            PreparedReference prepared,
            GLProg glProg,
            GLTexture alterCfa) {

        if (prepared == null || prepared.levels == null) {
            throw new IllegalStateException("Wronski prepared reference is closed");
        }

        final Point rawHalf = prepared.rawHalf;
        final float snr = prepared.snr;
        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final int[] tile = new int[] {
                baseTile, baseTile, baseTile, Math.max(8, baseTile / 2)
        };
        final int[] radius = new int[] {1, 4, 4, 4};
        final int[] metric = new int[] {0, 1, 1, 1};
        final int[] stepFactor = new int[] {1, 2, 4, 4};

        final GLTexture[] ref = prepared.levels;
        GLTexture[] alt = null;
        GLTexture previousFlow = null;
        GLTexture denseFlow = null;

        try {
            alt = buildGuidePyramid(
                    rawHalf,
                    prepared.cfaPattern,
                    prepared.signalScale,
                    glProg,
                    alterCfa);

            Point[] levelSize = new Point[4];
            levelSize[0] = rawHalf;
            for (int l=1;l<4;l++) {
                levelSize[l] = divCeil(levelSize[l-1], stepFactor[l]);
            }

            for (int l=3;l>=0;l--) {
                Point grid = new Point(
                        Math.max(1,(levelSize[l].x + tile[l]-1)/tile[l]),
                        Math.max(1,(levelSize[l].y + tile[l]-1)/tile[l]));

                GLTexture block = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                GLTexture refined = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_block_match", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("searchRadius", radius[l]);
                glProg.setVar("distanceMetric", metric[l]);
                glProg.setVar("hasPrevious", previousFlow != null ? 1 : 0);
                glProg.setVar(
                        "previousToCurrentScale",
                        l < 3 ? (float)stepFactor[l+1] : 1.0f);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture(
                        "PreviousFlow",
                        previousFlow != null ? previousFlow : ref[l]);
                glProg.setTextureCompute("OutputFlow", block, true);
                glProg.computeAuto(grid,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_ica_refine", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("iterations", 3);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture("BlockFlow", block);
                glProg.setTextureCompute("OutputFlow", refined, true);
                glProg.computeAuto(grid,1);

                block.close();
                if (previousFlow != null) previousFlow.close();
                previousFlow = refined;
            }

            denseFlow = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16,4),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/mfsr_flow_expand", true);
            glProg.setVar("outputSize", rawHalf);
            glProg.setVar("tileSize", baseTile);
            glProg.setTexture("TileFlow", previousFlow);
            glProg.setTextureCompute("OutputFlow", denseFlow, true);
            glProg.computeAuto(rawHalf,1);

            Log.d(TAG,
                    "IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION"
                    + " snr=" + snr
                    + " baseTile=" + baseTile
                    + " guide=bandlimitedAllCfaFftEquivalent"
                    + " gaussianSigma=factorHalf"
                    + " gaussianRadius=fourSigma"
                    + " factors=1,2,4,4"
                    + " radii=1,4,4,4"
                    + " metrics=L1,L2,L2,L2"
                    + " icaIterations=3"
                    + " icaUpdateClamp=false"
                    + " referenceBoundary=circular"
                    + " movingBoundary=zero"
                    + " flowUpscale=nearest"
                    + " referencePreparedOnce=true");

            GLTexture keep = denseFlow;
            denseFlow = null;
            return new MotionV2Alignment.Result(
                    keep,0.0f,0.0f,1.0f,0.0f);
        } finally {
            if (denseFlow != null) denseFlow.close();
            if (previousFlow != null) previousFlow.close();
            if (alt != null) {
                for (GLTexture t : alt) {
                    if (t != null) t.close();
                }
            }
        }
    }

    public static MotionV2Alignment.Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {
        try (PreparedReference prepared = prepareReference(
                rawHalf, cfaPattern, signalScale, snr, glProg, referenceCfa)) {
            return alignPrepared(prepared, glProg, alterCfa);
        }
    }
}
JAVA_ALIGN

python3 - "$TMP/candidate/$RECON" "$TMP/candidate/$VERSION" <<'PY_RECON'
from pathlib import Path
import sys
recon=Path(sys.argv[1]); version=Path(sys.argv[2])
t=recon.read_text()

old_snr='''        final float mfsrSnr = Math.max(
                6.0f,
                Math.min(
                        30.0f,
                        0.18f / (float)Math.sqrt(
                                Math.max(
                                        noiseS * 0.18f + noiseO,
                                        1.0e-8f))));
'''
new_snr='''        /*
         * IRIS_26473_IPOL_REFERENCE_BRIGHTNESS_SNR
         * Public process() derives SNR from actual reference brightness and
         * the brightness-indexed std curve, clamped to [6,30].
         */
        final MotionV2IpolNoiseCurve.Curve ipolNoiseCurve =
                MotionV2IpolNoiseCurve.build(
                        noiseS,
                        noiseO,
                        images.get(0).buffer,
                        raw,
                        blackLevel,
                        (float) parameters.whiteLevel,
                        canonicalGain);
        final float mfsrSnr = ipolNoiseCurve.snr;
'''
if t.count(old_snr)!=1:
    raise SystemExit(f"SNR anchor count={t.count(old_snr)}")
t=t.replace(old_snr,new_snr,1)

old_decl='''        GLTexture referenceRaw = null;
        GLTexture referenceCfa = null;
'''
new_decl='''        GLTexture referenceRaw = null;
        GLTexture referenceCfa = null;
        GLTexture ipolNoiseCurveTexture = null;
'''
if t.count(old_decl)!=1:
    raise SystemExit(f"texture declaration anchor count={t.count(old_decl)}")
t=t.replace(old_decl,new_decl,1)

old_try='''        try {
            /*
             * IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT
'''
new_try='''        try {
            if (directBayer) {
                ipolNoiseCurve.rgba32f.position(0);
                ipolNoiseCurveTexture = new GLTexture(
                        new Point(1001, 1),
                        new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                        ipolNoiseCurve.rgba32f,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                Log.d(TAG,
                        "IRIS_26473_IPOL_FAST_MC_CURVES"
                        + " brightnessEntries=1001"
                        + " referenceMean=" + ipolNoiseCurve.referenceMean
                        + " snr=" + ipolNoiseCurve.snr
                        + " nonlinearLowEnd=" + ipolNoiseCurve.nonlinearLowEnd
                        + " nonlinearHighStart=" + ipolNoiseCurve.nonlinearHighStart
                        + " clippingModel=true"
                        + " varianceInterpolation=true"
                        + " deterministicMobileMonteCarlo=true");
            }

            /*
             * IRIS_26420_MOTION_V2_NO_LEGACY_ALIGNMENT
'''
if t.count(old_try)!=1:
    raise SystemExit(f"outer try anchor count={t.count(old_try)}")
t=t.replace(old_try,new_try,1)

old_rob='''                                glProg.setVar("noiseS", noiseS);
                                glProg.setVar("noiseO", noiseO);
                                glProg.setVar(
                                        "tileSizeRaw",
'''
new_rob='''                                glProg.setTexture(
                                        "noiseCurve",
                                        ipolNoiseCurveTexture);
                                glProg.setVar(
                                        "tileSizeRaw",
'''
if t.count(old_rob)!=1:
    raise SystemExit(f"robustness noise binding anchor count={t.count(old_rob)}")
t=t.replace(old_rob,new_rob,1)

old_close='''            /* IRIS_26413 pack-fix: no temporary uint16 result texture is allocated. */
            if (directFrameSupportB != null) directFrameSupportB.close();
'''
new_close='''            /* IRIS_26413 pack-fix: no temporary uint16 result texture is allocated. */
            if (ipolNoiseCurveTexture != null) ipolNoiseCurveTexture.close();
            if (directFrameSupportB != null) directFrameSupportB.close();
'''
if t.count(old_close)!=1:
    raise SystemExit(f"noise texture close anchor count={t.count(old_close)}")
t=t.replace(old_close,new_close,1)

recon.write_text(t)

v=version.read_text()
if v.count("VERSION_NAME=0.9726472")!=1 or v.count("VERSION_BUILD=26472")!=1:
    raise SystemExit("26472 version anchors not unique")
v=v.replace("VERSION_NAME=0.9726472","VERSION_NAME=0.9726473",1)
v=v.replace("VERSION_BUILD=26472","VERSION_BUILD=26473",1)
version.write_text(v)
print("26473 reconstruction/version transform: PASS")
PY_RECON

python3 - "$TMP/candidate" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1])
required={
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2IpolNoiseCurve.java':[
 'IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES','LEVELS = 1000',
 'PATCHES = 8192','unitaryMc','sigmaLo2'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java':[
 'IRIS_26473_IPOL_REFERENCE_BRIGHTNESS_SNR',
 'IRIS_26473_IPOL_FAST_MC_CURVES','MotionV2IpolNoiseCurve.build',
 '"noiseCurve"'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java':[
 'IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION',
 'mfsr_pyramid_gaussian','icaUpdateClamp=false',
 'referenceBoundary=circular','movingBoundary=zero'],
'app/src/main/assets/shaders/motionv2/alignment_guide.glsl':[
 'IRIS_26473_IPOL_FFT_GREY_EQUIVALENT','quadMean'],
'app/src/main/assets/shaders/motionv2/mfsr_pyramid_gaussian.glsl':[
 'IRIS_26473_IPOL_FACTOR_DEPENDENT_GAUSSIAN_PYRAMID',
 'sigma=max(0.5*float(f),0.5)','radius=min(8'],
'app/src/main/assets/shaders/motionv2/mfsr_block_match.glsl':[
 'IRIS_26473_IPOL_ALIGNMENT_BOUNDARY_SEMANTICS',
 'sampleReference','sampleMoving'],
'app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl':[
 'IRIS_26473_IPOL_ICA_EXACT_UPDATE','publicSobel','flow+=d'],
'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl':[
 'IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES',
 'uniform highp sampler2D noiseCurve','texelFetch(noiseCurve'],
}
for rel,markers in required.items():
    txt=(root/rel).read_text()
    for marker in markers:
        if marker not in txt:
            raise SystemExit(f"candidate missing {marker} in {rel}")

align_java=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java').read_text()
for api in (
    'public static final class PreparedReference implements AutoCloseable',
    'public static PreparedReference prepareReference(',
    'public static MotionV2Alignment.Result alignPrepared(',
    'IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE',
    'referencePreparedOnce=true',
):
    if api not in align_java:
        raise SystemExit(f"26467 prepared-reference API lost: {api}")

recon_java=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
if 'MotionV2WronskiAlignment.PreparedReference' not in recon_java:
    raise SystemExit("reconstruction no longer owns PreparedReference")
if 'MotionV2WronskiAlignment.prepareReference(' not in recon_java:
    raise SystemExit("reconstruction prepareReference call missing")
if 'MotionV2WronskiAlignment.alignPrepared(' not in recon_java:
    raise SystemExit("reconstruction alignPrepared call missing")

ica=(root/'app/src/main/assets/shaders/motionv2/mfsr_ica_refine.glsl').read_text()
if 'clamp(d,vec2(-1.5),vec2(1.5))' in ica:
    raise SystemExit("old Photon ICA update clamp survived")

rob=(root/'app/src/main/assets/shaders/motionv2/mfsr_robustness.glsl').read_text()
for obsolete in ('clippedVariance','normalPdf','normalCdf','sampleStdFactor','diffMeanFactor'):
    if obsolete in rob:
        raise SystemExit(f"old analytic robustness shortcut survived: {obsolete}")

align=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java').read_text()
if 'mfsr_pyramid_down' in align:
    raise SystemExit("old fixed 5x5 alignment pyramid still active")

preserve={
'app/src/main/assets/shaders/motionv2/direct_rgb_init.glsl':[
 'IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR'],
'app/src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl':[
 'IRIS_26472_WRONSKI_PUBLIC_AUX_ACCUMULATION_ACCUMULATED_ROBUSTNESS',
 'IRIS_26469_CENSORED_HIGHLIGHT_DUAL_EVIDENCE_AUX'],
'app/src/main/assets/shaders/motionv2/mfsr_low_support_reference.glsl':[
 'IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE',
 'MAX_FRAME_COUNT=2.0','RAD_MAX=2','MAX_MULTIPLIER=8.0'],
'app/src/main/assets/shaders/motionv2/mfsr_finalize.glsl':[
 'IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER'],
'app/src/main/assets/shaders/motionv2/mfsr_kernel_covariance.glsl':[
 'float vst(float x)','IRIS_26469_STABLE_SYMMETRIC_TENSOR_EIGENVECTOR'],
'app/src/main/assets/shaders/motionv2/mfsr_robustness_erode.glsl':[
 'IRIS_26462_WRONSKI_5X5_ROBUSTNESS_MIN'],
'app/src/main/assets/shaders/motionv2/gainmap.glsl':[
 'IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM',
 'IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java':[
 'IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY'],
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java':[
 'IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY'],
}
for rel,markers in preserve.items():
    txt=(root/rel).read_text()
    for marker in markers:
        if marker not in txt:
            raise SystemExit(f"lost protected lineage {marker} in {rel}")

ver=(root/'app/version.properties').read_text()
if 'VERSION_NAME=0.9726473' not in ver or 'VERSION_BUILD=26473' not in ver:
    raise SystemExit("26473 version missing")

print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
PY_VALIDATE
pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"

for f in "$RECON" "$ALIGNJAVA" "$ALIGNGUIDE" "$BLOCKMATCH" "$ICA" "$ROBUST" "$VERSION"; do
  cp "$TMP/candidate/$f" "$f"
done
cp "$TMP/candidate/$NOISEJAVA" "$NOISEJAVA"
cp "$TMP/candidate/$PYRGAUSS" "$PYRGAUSS"

find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

python3 - "$HASH_26472" "$HASH_AFTER" \
  "$RECON" "$ALIGNJAVA" "$ALIGNGUIDE" "$BLOCKMATCH" "$ICA" "$ROBUST" \
  "$NOISEJAVA" "$PYRGAUSS" "$VERSION" <<'PY_HASH'
from pathlib import Path
import sys
def load(p):
    d={}
    for line in Path(p).read_text().splitlines():
        h,f=line.split('  ',1); d[f]=h
    return d
before=load(sys.argv[1]); after=load(sys.argv[2]); allowed=set(sys.argv[3:])
new=set(after)-set(before)
unexpected_new=[p for p in new if p not in allowed]
if unexpected_new:
    raise SystemExit("unexpected new app source paths: "+", ".join(sorted(unexpected_new)))
missing=set(before)-set(after)
if missing:
    raise SystemExit("protected source paths missing: "+", ".join(sorted(missing)))
bad=[p for p in before if p not in allowed and before[p]!=after[p]]
if bad:
    raise SystemExit("unexpected protected-file changes: "+", ".join(bad))
print("Protected-file hashes: PASS")
PY_HASH
pass "protected-file hashes PASS"

for marker in \
  IRIS_26473_IPOL_FAST_MONTE_CARLO_NOISE_CURVES \
  IRIS_26473_IPOL_REFERENCE_BRIGHTNESS_SNR \
  IRIS_26473_IPOL_FAST_MC_CURVES \
  IRIS_26473_IPOL_FFT_GREY_EQUIVALENT \
  IRIS_26473_IPOL_FACTOR_DEPENDENT_GAUSSIAN_PYRAMID \
  IRIS_26473_IPOL_ALIGNMENT_BOUNDARY_SEMANTICS \
  IRIS_26473_IPOL_ICA_EXACT_UPDATE \
  IRIS_26473_IPOL_FAST_MC_ROBUSTNESS_CURVES \
  IRIS_26473_IPOL_WRONSKI_ALIGNMENT_COMPLETION \
  IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
  IRIS_26472_WRONSKI_PUBLIC_ACCUMULATED_ROBUSTNESS_REFERENCE_MERGE \
  IRIS_26472_WRONSKI_MINIMAL_CENSORED_HIGHLIGHT_FINALIZER \
  IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
  IRIS_26472_EDGE_CONSTRAINED_GAIN_SPIKE_LIMITER \
  IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY \
  IRIS_26470_UHDR_EXACT_ORTHOGONAL_GEOMETRY; do
  grep -Rqs "$marker" app/src/main || fail "lost required marker $marker"
done
pass "historical lineage/ownership preservation PASS"

! grep -q 'clippedVariance' "$ROBUST" || fail "old analytic robustness shortcut survived"
! grep -q 'clamp(d,vec2(-1.5),vec2(1.5))' "$ICA" || fail "old ICA update clamp survived"
! grep -q 'mfsr_pyramid_down' "$ALIGNJAVA" || fail "old fixed alignment pyramid remains active"
pass "IPOL replacement retirement checks PASS"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  protected-file hashes PASS"
echo "  exact successful 26472 V6 backup PASS"
echo "  exact successful 26472 V6 precursor PASS"
echo "  1001-entry clipped-noise std/diff curves PASS"
echo "  actual-reference-brightness SNR tuning PASS"
echo "  anti-CFA band-limited all-channel alignment guide PASS"
echo "  factor-dependent Gaussian alignment pyramid PASS"
echo "  26467 prepared-reference API/lifetime preserved PASS"
echo "  public ICA derivative/update behavior PASS"
echo "  public alignment boundary semantics PASS"
echo "  26472 aux-first/reference-last merge preserved PASS"
echo "  26472 accumulated-robustness reference ownership preserved PASS"
echo "  26472 SDR-authoritative UHDR preserved PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF_REPORT
26473 IPOL / Wronski completion
==============================
Corrective infrastructure parent: $PROTECTED_HEAD
Protected app-source backup target: $BACKUP_TARGET
Backup branch: $BACKUP_BRANCH
Build: $NEW_VERSION / $NEW_BUILD

New:
- 1001-entry clipped-noise std/diff curves.
- Fast-MC nonlinear-region estimation + variance interpolation.
- Actual-reference-brightness SNR tuning.
- All-CFA anti-carrier alignment guide replacing green-only guide.
- Factor-dependent Gaussian alignment pyramid.
- IPOL ICA derivative/update behavior; old +/-1.5 clamp removed.
- Circular reference / zero moving boundary semantics.

Android equivalence note:
- Public IPOL uses a full-frame FFT spectral crop for the grey alignment guide.
  26473 implements the same anti-CFA band-limited role in spatial form on the
  already packed 2x2 CFA flow grid. It is not bit-identical desktop FFT math.
- Public fast MC uses 1e5 random patches. 26473 uses deterministic 8192-patch
  nonlinear estimates to bound camera latency while preserving the same
  clipped-noise curve architecture and 1001-entry consumer contract.

Preserved:
- 26472 aux-first/reference-last merge.
- accumulated-robustness reference overwrite/add.
- GAT/VST steerable per-frame covariance.
- public robustness 5x5 local-min.
- censored clipped brightness + separate unsaturated RGB support.
- SDR-authoritative UHDR geometry/headroom and razor limiter.
- sharpening remains disabled.

Primary test:
- grow light/window at 1 frame and 15 frames;
- then moving-subject ghosting and HDR ON/OFF spatial parity.
EOF_REPORT

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
sha="$(sha256sum "$APK_NAME" | awk '{print $1}')"
{
  echo "BUILD SUCCESS"
  echo "APK=$APK_NAME"
  echo "SHA256=$sha"
  echo "VERSION=$NEW_VERSION"
  echo "BUILD=$NEW_BUILD"
  echo "dev_untouched=true"
  echo "experimental_source_not_committed=true"
} | tee -a "$REPORT"
pass "26473 IPOL / WRONSKI COMPLETION BUILD SUCCESS"
