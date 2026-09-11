#!/usr/bin/env python3
from pathlib import Path
import hashlib, math, re, shutil, subprocess, sys, tempfile
if len(sys.argv)!=3: raise SystemExit('usage: verify_26628_r3_regressions.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); P=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for root in (B,C):
    for forbidden in ['app/build','app/.cxx']:
        if (root/forbidden).exists(): raise SystemExit(f'FAIL generated path in authority candidate {forbidden}')
for a,b in [
('R3_26628_NATIVE_PROTECTED_BASE.sha256','R3_26628_NATIVE_PROTECTED_CANDIDATE.sha256'),
('R3_26628_VENDOR_PROTECTED_BASE.sha256','R3_26628_VENDOR_PROTECTED_CANDIDATE.sha256'),
('R3_26628_DNG_BASE.sha256','R3_26628_DNG_CANDIDATE.sha256')]:
    if (P/a).read_bytes()!=(P/b).read_bytes(): raise SystemExit(f'FAIL invariance regression {a} {b}')
# Proven reconstruction/highlight/legacy owners remain exact 26627 bytes.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/Initial.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
]:
    if sha(B/rel)!=sha(C/rel): raise SystemExit(f'FAIL protected pink-edge/legacy owner changed {rel}')
# Matrix/profile stage: bypass nonlinear DCP map on negative profile excursions; fit display negatives on common axis.
cts=(C/'app/src/main/assets/shaders/motionv2/color_transform.glsl').read_text()
compact=cts.replace(' ','')
for tok in ['if(min(color.r,min(color.g,color.b))<0.0)returncolor;',
            'floatnegativeFloor=min(linearDisplay.r,min(linearDisplay.g,linearDisplay.b));',
            'if(negativeFloor<0.0)linearDisplay-=vec3(negativeFloor);']:
    if tok not in compact: raise SystemExit(f'FAIL pink/cyan edge invariant {tok}')
prefix=compact.split('floatnegativeFloor=',1)[0]
if 'clamp(linearDisplay' in prefix or 'max(linearDisplay,vec3(0.0))' in prefix:
    raise SystemExit('FAIL per-channel display clipping before neutral-axis gamut floor')
# Restrained presentation: no independent channel floor. One common shift followed by <=1 chroma contraction only.
ads=(C/'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl').read_text(); acompact=ads.replace(' ','')
for tok in ['floatnegativeFloor=min(rgb.r,min(rgb.g,rgb.b));','if(negativeFloor<0.0)rgb-=vec3(negativeFloor);','Output=vec3(y)+chroma*scale;']:
    if tok not in acompact: raise SystemExit(f'FAIL restrained presentation neutral-axis invariant {tok}')
for forbidden in ['max(texelFetch(InputBuffer','Output=max(','1.32','1.22','1.12','requestedGain','coherentColorActivation']:
    if forbidden in ads: raise SystemExit(f'FAIL restrained presentation regression {forbidden}')
# 0.95 contraction theorem using exact Display-P3 luma coefficients and float-tolerant neutral handling.
w=(0.22897456,0.69173852,0.07928691)
for rgb in [(0.2,0.2,0.2),(1.0,1.0,1.0),(0.7,0.2,0.1),(0.1,0.8,0.3),(1.2,0.3,0.7),(-0.1,0.2,0.3)]:
    floor=min(rgb); fit=tuple(x-floor if floor<0.0 else x for x in rgb)
    y=sum(a*b for a,b in zip(fit,w)); out=tuple(y+(x-y)*0.95 for x in fit); yo=sum(a*b for a,b in zip(out,w))
    cin=math.sqrt(sum((x-y)**2 for x in fit)); cout=math.sqrt(sum((x-y)**2 for x in out))
    if cout>cin*0.950001+1e-9: raise SystemExit('FAIL presentation enlarged chroma fixture')
    if min(out)<-1e-9: raise SystemExit('FAIL presentation created negative channel fixture')
    if abs(yo-y)>1e-8: raise SystemExit('FAIL presentation luminance drift fixture')
    if max(fit)-min(fit)<1e-12 and max(abs(out[i]-fit[i]) for i in range(3))>1e-8:
        raise SystemExit('FAIL presentation moved neutral fixture')
# Xiaomi regression: equal dual ForwardMatrix is valid and old placeholder predicate is absent.
solver=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java').read_text()
for forbidden in ['DUAL_ILLUMINANT_FORWARD_PLACEHOLDER_REJECT','forwardDelta','colorMatrixDelta']:
    if forbidden in solver: raise SystemExit(f'FAIL Xiaomi equal-ForwardMatrix regression {forbidden}')
for tok in ['equalForwardAccepted=true','interpolateOptional(p.forward1, p.forward2, firstWeight)']:
    if tok not in solver: raise SystemExit(f'FAIL equal ForwardMatrix path missing {tok}')
# Numerical fixture from the known-good Xiaomi 26626 metadata.
expected=[1.9659153,-0.022977002,0.40074044,-0.04073863,1.0738649,-0.103170484,-0.11580317,-0.54703426,2.8735912]
reference=[1.96612468,-0.02295664,0.40076324,-0.04082333,1.07385676,-0.10317979,-0.11583193,-0.54717005,2.87430408]
if max(abs(a-b) for a,b in zip(expected,reference))>0.001: raise SystemExit('FAIL Xiaomi 26626 DNG color numerical reference drift')
# Full 3D DCP logical order must agree between GL and native true2x.
native=(C/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text(); ncompact=native.replace(' ','')
if 'ivec2(sat,value*hueDivisions+hue)' not in compact: raise SystemExit('FAIL GL DCP value-hue-saturation order')
if 'vIdx*(size_t)hDiv*(size_t)sDiv+(size_t)hIdx*(size_t)sDiv+(size_t)sIdx' not in ncompact: raise SystemExit('FAIL native DCP value-hue-saturation order')
# New true2x color functions may not independently clamp after common-axis matrix fit/contraction.
for forbidden in ['*out=clampNonnegative(linear);','*out=clampNonnegative(add(Vec3{y,y,y},mul(c,0.95f)))']:
    if forbidden in native: raise SystemExit(f'FAIL true2x color per-channel clamp regression {forbidden}')
if 'p.dcpHueSatMap.empty()&&p.dcpLookMap.empty()' not in ncompact: raise SystemExit('FAIL true2x DCP profile GPU exclusion')
# Exact failed-R1 native compiler condition is permanent: y is the integer pixel coordinate and cannot be redeclared.
if 'float y=luma(center)' in native: raise SystemExit('FAIL REGRESSION NDK-y-shadow: float y redeclared inside function with int y parameter')
if native.count('float lum=luma(center)') != 2: raise SystemExit('FAIL REGRESSION NDK-y-shadow: corrected lum declaration count')
# Lens UI: request -3dp only when both hard clearances remain satisfied.
ui=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java').read_text()
aux=(C/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java').read_text()
for tok in ['previewClearancePx = 10.0f','chevronClearancePx = 8.0f','preferredLensLiftPx = 3.0f','Math.max(-preferredLensLiftPx, minimumSelectedTop - selectedTop)']:
    if tok not in ui: raise SystemExit(f'FAIL lens hard-clearance regression {tok}')
# Generic algebraic fixture: the chosen shift can never place selectedTop above the hard minimumSelectedTop.
for selectedTop, minimumTop, lift in [(100.0,90.0,3.0),(100.0,99.0,3.0),(100.0,100.0,3.0),(100.0,104.0,3.0)]:
    shift=max(-lift, minimumTop-selectedTop)
    if selectedTop+shift < minimumTop-1e-9: raise SystemExit('FAIL bounded lens lift fixture')
for tok in ['TextView b = new TextView(getContext());','b.setGravity(Gravity.CENTER);','b.setIncludeFontPadding(false);','b.setPadding(0, 0, 0, 0);','b.setMinimumHeight(0);','b.setSingleLine(true);']:
    if tok not in aux: raise SystemExit(f'FAIL lens text clipping regression {tok}')
for tok in ['if (!(child instanceof TextView)) continue;','TextView button = (TextView) child;']:
    if tok not in aux: raise SystemExit(f'FAIL REGRESSION JAVA-lens-type: missing {tok}')
if re.search(r'\bButton\b', aux): raise SystemExit('FAIL REGRESSION JAVA-lens-type: standalone Button type/import/cast survived')

# Supplemental exact-source javac gate for the class that failed R2. This is not the real Android project compiler.
def compile_aux_with_stubs(candidate_root):
    javac=shutil.which('javac')
    if not javac: raise SystemExit('FAIL supplemental AuxButtons javac preflight: javac unavailable')
    with tempfile.TemporaryDirectory(prefix='iris26628_aux_javac_') as td:
        root=Path(td)/'src'; out=Path(td)/'out'
        def w(rel,text):
            q=root/rel; q.parent.mkdir(parents=True,exist_ok=True); q.write_text(text)
        stubs={
          'android/content/Context.java': 'package android.content; public class Context { public android.content.res.Resources getResources(){ return new android.content.res.Resources(); } }',
          'android/content/res/Resources.java': 'package android.content.res; public class Resources { public float getDimension(int id){ return 35f; } }',
          'android/util/AttributeSet.java': 'package android.util; public interface AttributeSet {}',
          'android/view/Gravity.java': 'package android.view; public final class Gravity { public static final int CENTER=17; }',
          'android/view/ViewPropertyAnimator.java': 'package android.view; public class ViewPropertyAnimator { public ViewPropertyAnimator setDuration(long v){return this;} public ViewPropertyAnimator alpha(float v){return this;} public ViewPropertyAnimator scaleX(float v){return this;} public ViewPropertyAnimator scaleY(float v){return this;} public ViewPropertyAnimator withEndAction(Runnable r){return this;} public void start(){} }',
          'android/view/View.java': 'package android.view; public class View { private android.content.Context context=new android.content.Context(); public static final int INVISIBLE=4, VISIBLE=0; private int id; public android.content.Context getContext(){return context;} public interface OnClickListener { void onClick(View v); } public void setOnClickListener(OnClickListener l){} public void setSelected(boolean b){} public boolean isSelected(){return false;} public void setId(int i){id=i;} public int getId(){return id;} public static int generateViewId(){return 1;} public void setLayoutParams(Object p){} public ViewPropertyAnimator animate(){return new ViewPropertyAnimator();} }',
          'android/widget/LinearLayout.java': 'package android.widget; import android.content.Context; import android.util.AttributeSet; import android.view.View; public class LinearLayout extends View { public static class LayoutParams { public LayoutParams(int w,int h){} public void setMargins(int a,int b,int c,int d){} } public LinearLayout(Context c, AttributeSet a){} public void removeAllViews(){} public int getChildCount(){return 0;} public View getChildAt(int i){return null;} public void addView(View v){} public void setVisibility(int v){} }',
          'android/widget/TextView.java': 'package android.widget; import android.content.Context; import android.view.View; public class TextView extends View { public TextView(Context c){} public void setText(CharSequence s){} public void setTextAppearance(int id){} public void setGravity(int g){} public void setIncludeFontPadding(boolean b){} public void setPadding(int a,int b,int c,int d){} public void setMinWidth(int v){} public void setMinHeight(int v){} public void setMinimumWidth(int v){} public void setMinimumHeight(int v){} public void setSingleLine(boolean b){} public void setBackgroundResource(int id){} public void setStateListAnimator(Object o){} public void setTransformationMethod(Object o){} }',
          'androidx/annotation/Nullable.java': 'package androidx.annotation; public @interface Nullable {}',
          'com/particlesdevs/photoncamera/R.java': 'package com.particlesdevs.photoncamera; public final class R { public static final class dimen { public static final int aux_button_internal_margin=1, aux_button_size=2;} public static final class style { public static final int AuxButtonText=3;} public static final class drawable { public static final int aux_button_background=4;} }',
          'com/particlesdevs/photoncamera/control/IrisZoomController.java': 'package com.particlesdevs.photoncamera.control; public final class IrisZoomController { public static boolean isInitialized(){return false;} public static boolean isContinuousZoomEnabledForCurrentMode(){return false;} public static float getGlobalZoom(){return 1f;} public static String getOwnerCameraId(){return "";} }',
          'com/particlesdevs/photoncamera/ui/camera/binding/CustomBinding.java': 'package com.particlesdevs.photoncamera.ui.camera.binding; import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout; import com.particlesdevs.photoncamera.ui.camera.model.AuxButtonsModel; public final class CustomBinding { public static void setAuxButtonModel(AuxButtonsLayout a, AuxButtonsModel b){} }',
          'com/particlesdevs/photoncamera/ui/camera/data/CameraLensData.java': 'package com.particlesdevs.photoncamera.ui.camera.data; public class CameraLensData { public String getCameraId(){return "";} public float getZoomFactor(){return 1f;} }',
          'com/particlesdevs/photoncamera/ui/camera/model/AuxButtonsModel.java': 'package com.particlesdevs.photoncamera.ui.camera.model; import java.util.List; import com.particlesdevs.photoncamera.ui.camera.data.CameraLensData; import com.particlesdevs.photoncamera.ui.camera.views.AuxButtonsLayout; public class AuxButtonsModel { public List<CameraLensData> getFrontCameras(){return null;} public List<CameraLensData> getBackCameras(){return null;} public AuxButtonsLayout.AuxButtonListener getAuxButtonListener(){return null;} public boolean isEnabled(){return true;} }',
        }
        for rel,text in stubs.items(): w(rel,text)
        src=candidate_root/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java'
        dst=root/'com/particlesdevs/photoncamera/ui/camera/views/AuxButtonsLayout.java'; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(src.read_bytes())
        files=[str(q) for q in sorted(root.rglob('*.java'))]
        result=subprocess.run([javac,'-proc:none','--release','17','-d',str(out),*files],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode!=0: raise SystemExit('FAIL supplemental AuxButtons javac preflight:\n'+result.stdout)
compile_aux_with_stubs(C)
print('PASS supplemental AuxButtons exact-source javac preflight')

print('PASS 26628 regressions: generated trees excluded; legacy/reconstruction/pink-edge owners protected; equal-FM Xiaomi valid; common-axis gamut/presentation floors; contraction-only color; full 3D DCP order; true2x profile parity gate; exact NDK y-shadow regression; bounded 3dp lens lift; device-independent centered lens text; exact R2 Java type regression; supplemental AuxButtons javac')
