package com.particlesdevs.photoncamera.processing.opengl.postpipeline;

import androidx.activity.h;
import com.particlesdevs.photoncamera.processing.opengl.GLBasePipeline;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.processing.opengl.nodes.Node;
import com.particlesdevs.photoncamera.settings.annotations.Tunable;
import com.particlesdevs.photoncamera.util.Log;

/* loaded from: classes.dex */
public class ESD3D2 extends Node {

    @Tunable(category = "Denoise", defaultValue = 1.0f, description = "Enable ESD3D Denoising", max = 1.0f, min = 0.0f, step = 1.0f, title = "Enable")
    boolean enable;

    @Tunable(category = "Denoise", defaultValue = 0.8f, description = "Luma strength multiplier for denoising", max = 2.0f, title = "Luma")
    float luma;

    // >>> SHADOW BOOST - ADD THIS FIELD <<<
    @Tunable(category = "Denoise", defaultValue = 0.5f, description = "Boost denoising in deep shadows to prevent noise amplification after tonemap", max = 2.0f, min = 0.0f, step = 0.01f, title = "Shadow Boost")
    float shadowBoost;
    // >>> END SHADOW BOOST <<<

    @Tunable(category = "Denoise", defaultValue = 21.0f, description = "Maximum kernel size for denoising", max = 51.0f, min = 1.0f, step = 1.0f, title = "Max Kernel")
    int maxSize;

    @Tunable(category = "Denoise", defaultValue = 7.0f, description = "Minimum kernel size for denoising", max = 21.0f, min = 1.0f, step = 1.0f, title = "Min Kernel")
    int minSize;

    @Tunable(category = "Denoise", defaultValue = 1.5f, description = "Moire reduction strength", max = 5.0f, step = 0.1f, title = "Moire Reduction")
    float moire;

    @Tunable(category = "Denoise", defaultValue = 0.00390625f, description = "Target noise level to map to minimum kernel size (1/256 = 0.00390625)", max = 0.1f, step = 1.0E-4f, title = "Noise Target")
    float noiseTarget;

    @Tunable(category = "Denoise", defaultValue = 24.0f, max = 50.0f, title = "Noise To Kernel Size")
    float noiseToKernelSize;

    @Tunable(category = "Denoise", defaultValue = 1.0f, description = "Whether to apply subsampling denoising to color channels (in addition to luma)", max = 1.0f, min = 0.0f, step = 1.0f, title = "Use Color Denoising")
    boolean useColorDenoising;

    @Override // com.particlesdevs.photoncamera.processing.opengl.nodes.Node
    public final void c() {
    }

    @Override // com.particlesdevs.photoncamera.processing.opengl.nodes.Node
    public final void d() {
        ESD3D2 esd3d2;
        GLTexture b2;
        GLTexture gLTexture;
        if (!this.enable) {
            this.f7532a = this.f7534c.f7532a;
            return;
        }
        GLBasePipeline gLBasePipeline = this.f7537f;
        float sqrt = ((float) Math.sqrt((gLBasePipeline.f7461n * 0.5d) + gLBasePipeline.o)) / this.noiseTarget;
        if (sqrt < 1.0f) {
            sqrt = 1.0f;
        }
        if (sqrt > 4.0f) {
            sqrt = 4.0f;
        }
        int i = (int) (0.5f + sqrt);
        Log.b(this.f7533b, h.c(i, "Scaling factor:"));
        if (this.useColorDenoising) {
            if (i != 1) {
                this.f7537f.i = this.h.e(this.f7534c.f7532a, i);
                GLTexture b3 = this.f7537f.b();
                this.f7532a = b3;
                k(this.f7537f.i, b3, 0.0f, sqrt * 0.75f);
                b2 = this.f7537f.b();
                esd3d2 = this;
                esd3d2.l(this.f7532a, this.f7537f.i, this.f7534c.f7532a, b2, i);
            } else {
                esd3d2 = this;
                GLTexture b4 = esd3d2.f7537f.b();
                esd3d2.f7532a = b4;
                k(esd3d2.f7534c.f7532a, b4, 0.0f, 1.0f);
                b2 = esd3d2.f7537f.b();
                GLTexture gLTexture2 = esd3d2.f7532a;
                GLTexture gLTexture3 = esd3d2.f7534c.f7532a;
                esd3d2.l(gLTexture2, gLTexture3, gLTexture3, b2, i);
            }
            gLTexture = b2;
        } else {
            gLTexture = this.f7534c.f7532a;
            esd3d2 = this;
        }
        GLTexture b5 = esd3d2.f7537f.b();
        esd3d2.f7532a = b5;
        k(gLTexture, b5, esd3d2.moire, 1.0f);
        esd3d2.i.f7517j = true;
        GLTexture gLTexture4 = esd3d2.f7537f.i;
        if (gLTexture4 != null) {
            gLTexture4.close();
            esd3d2.f7537f.i = null;
        }
    }

    public final void k(GLTexture gLTexture, GLTexture gLTexture2, float f2, float f3) {
        GLBasePipeline gLBasePipeline = this.f7537f;
        float f4 = gLBasePipeline.f7461n / f3;
        float f5 = gLBasePipeline.o / f3;
        Log.b(this.f7533b, "NoiseS:" + f4 + ", NoiseO:" + f5);
        this.i.l("NOISES", f4);
        this.i.l("NOISEO", f5);
        this.i.l("MOIRE", f2);
        this.i.l("LUMA", this.luma);
        this.i.l("SHADOWBOOST", this.shadowBoost);  // >>> SHADOW BOOST - ADD THIS LINE <<<
        this.i.i("INSIZE", this.f7537f.k.f7703e);
        double sqrt = (Math.sqrt(Math.max((f4 + f5) / this.noiseTarget, 1.0E-7d)) * this.noiseToKernelSize) + 1.0d;
        int i = (int) sqrt;
        int min = Math.min((this.minSize + i) - (i % 2), this.maxSize);
        Log.b("ESD3D", "KernelSize: " + sqrt + " MSIZE: " + min);
        this.i.l("KERNELSIZE", (float) sqrt);
        this.i.m("MSIZE", min);
        this.i.t("denoise/esd3d2", false);
        this.i.o("InputBuffer", gLTexture);
        this.i.f(gLTexture2);
    }

    public final void l(GLTexture gLTexture, GLTexture gLTexture2, GLTexture gLTexture3, GLTexture gLTexture4, int i) {
        this.i.m("SCALE", i);
        this.i.t("denoise/guidedupsample", false);
        this.i.o("LowresInput", gLTexture);
        this.i.o("Guide", gLTexture2);
        this.i.o("GuideHigh", gLTexture3);
        this.i.r("noiseS", this.f7537f.f7461n);
        this.i.r("noiseO", this.f7537f.o);
        this.i.g(gLTexture4, gLTexture4.f7522b);
        this.i.f7517j = true;
    }
}
