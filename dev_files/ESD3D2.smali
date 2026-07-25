.class public Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;
.super Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;
.source "SourceFile"


# instance fields
.field enable:Z
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 1.0f
        description = "Enable ESD3D Denoising"
        max = 1.0f
        min = 0.0f
        step = 1.0f
        title = "Enable"
    .end annotation
.end field

.field luma:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 0.8f
        description = "Luma strength multiplier for denoising"
        max = 2.0f
        title = "Luma"
    .end annotation
.end field

.field maxSize:I
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 9.0f
        description = "Maximum kernel size for denoising. Lower preserves more color (9 recommended)"
        max = 51.0f
        min = 1.0f
        step = 1.0f
        title = "Max Kernel"
    .end annotation
.end field

.field minSize:I
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 7.0f
        description = "Minimum kernel size for denoising"
        max = 21.0f
        min = 1.0f
        step = 1.0f
        title = "Min Kernel"
    .end annotation
.end field

.field moire:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 1.5f
        description = "Moire reduction strength"
        max = 5.0f
        step = 0.1f
        title = "Moire Reduction"
    .end annotation
.end field

.field noiseTarget:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 0.00390625f
        description = "Target noise level to map to minimum kernel size (1/256 = 0.00390625)"
        max = 0.1f
        step = 1.0E-4f
        title = "Noise Target"
    .end annotation
.end field

.field noiseToKernelSize:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 24.0f
        max = 50.0f
        title = "Noise To Kernel Size"
    .end annotation
.end field

.field shadowBoost:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 0.5f
        description = "Boost denoising in deep shadows to prevent noise amplification after tonemap"
        max = 2.0f
        min = 0.0f
        step = 0.01f
        title = "Shadow Boost"
    .end annotation
.end field

.field useColorDenoising:Z
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 1.0f
        description = "Whether to apply subsampling denoising to color channels (in addition to luma)"
        max = 1.0f
        min = 0.0f
        step = 1.0f
        title = "Use Color Denoising"
    .end annotation
.end field

.field chromaStrength:F
    .annotation runtime Lcom/particlesdevs/photoncamera/settings/annotations/Tunable;
        category = "Denoise"
        defaultValue = 1.0f
        description = "Chroma denoise strength. Lower preserves more color (try 0.3-0.7)"
        max = 1.0f
        min = 0.0f
        step = 0.05f
        title = "Chroma Strength"
    .end annotation
.end field


# virtual methods
.method public final c()V
    .locals 0

    return-void
.end method

.method public final d()V
    .locals 15

    iget-boolean v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->enable:Z

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v0, v0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iput-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    return-void

    :cond_0
    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget v1, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->n:F

    float-to-double v1, v1

    const-wide/high16 v3, 0x3fe0000000000000L    # 0.5

    mul-double/2addr v1, v3

    iget v0, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->o:F

    float-to-double v3, v0

    add-double/2addr v1, v3

    invoke-static {v1, v2}, Ljava/lang/Math;->sqrt(D)D

    move-result-wide v0

    double-to-float v0, v0

    iget v1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->noiseTarget:F

    div-float/2addr v0, v1

    const/high16 v1, 0x3f800000    # 1.0f

    cmpg-float v2, v0, v1

    if-gez v2, :cond_1

    move v0, v1

    :cond_1
    const/high16 v2, 0x40800000    # 4.0f

    cmpl-float v3, v0, v2

    if-lez v3, :cond_2

    move v0, v2

    :cond_2
    const/high16 v2, 0x3f000000    # 0.5f

    add-float/2addr v2, v0

    float-to-int v8, v2

    const-string v2, "Scaling factor:"

    invoke-static {v8, v2}, Landroidx/activity/h;->c(ILjava/lang/String;)Ljava/lang/String;

    move-result-object v2

    iget-object v3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->b:Ljava/lang/String;

    invoke-static {v3, v2}, Lcom/particlesdevs/photoncamera/util/Log;->b(Ljava/lang/String;Ljava/lang/String;)V

    iget-boolean v2, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->useColorDenoising:Z

    const/4 v9, 0x1

    if-nez v2, :cond_3

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v0, v0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-object v3, p0

    goto :goto_1

    :cond_3
    const/4 v2, 0x0

    if-eq v8, v9, :cond_4

    iget-object v3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget-object v4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->h:Lcom/particlesdevs/photoncamera/processing/opengl/GLUtils;

    iget-object v5, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v5, v5, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    invoke-virtual {v4, v5, v8}, Lcom/particlesdevs/photoncamera/processing/opengl/GLUtils;->e(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;I)Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v4

    iput-object v4, v3, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    invoke-virtual {v3}, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->b()Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v3

    iput-object v3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget-object v4, v4, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    const/high16 v5, 0x3f400000    # 0.75f

    mul-float/2addr v0, v5

    iget-object v10, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget v11, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->chromaStrength:F

    const/4 v12, 0x1

    new-array v12, v12, [F

    const/4 v13, 0x0

    aput v11, v12, v13

    const-string v11, "CHROMASTRENGTH"

    invoke-virtual {v10, v11, v12}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    invoke-virtual {p0, v4, v3, v2, v0}, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->k(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;FF)V

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    invoke-virtual {v0}, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->b()Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v7

    iget-object v4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget-object v5, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v6, v0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-object v3, p0

    invoke-virtual/range {v3 .. v8}, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->l(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;I)V

    :goto_0
    move-object v0, v7

    goto :goto_1

    :cond_4
    move-object v3, p0

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    invoke-virtual {v0}, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->b()Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v0

    iput-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v4, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v4, v4, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v10, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget v11, v3, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->chromaStrength:F

    const/4 v12, 0x1

    new-array v12, v12, [F

    const/4 v13, 0x0

    aput v11, v12, v13

    const-string v11, "CHROMASTRENGTH"

    invoke-virtual {v10, v11, v12}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    invoke-virtual {p0, v4, v0, v2, v1}, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->k(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;FF)V

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    invoke-virtual {v0}, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->b()Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v7

    iget-object v4, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->c:Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;

    iget-object v5, v0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-object v6, v5

    invoke-virtual/range {v3 .. v8}, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->l(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;I)V

    goto :goto_0

    :goto_1
    iget-object v2, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    invoke-virtual {v2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->b()Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    move-result-object v2

    iput-object v2, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->a:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    iget v4, v3, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->moire:F

    iget-object v10, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v11, "CHROMASTRENGTH"

    const/4 v12, 0x1

    new-array v12, v12, [F

    const/4 v13, 0x0

    aput v1, v12, v13

    invoke-virtual {v10, v11, v12}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    invoke-virtual {p0, v0, v2, v4, v1}, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->k(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;FF)V

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iput-boolean v9, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->j:Z

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget-object v0, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    if-eqz v0, :cond_5

    invoke-virtual {v0}, Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;->close()V

    iget-object v0, v3, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    const/4 v1, 0x0

    iput-object v1, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;

    :cond_5
    return-void
.end method

.method public final k(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;FF)V
    .locals 6

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget v1, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->n:F

    iget v0, v0, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->o:F

    div-float/2addr v1, p4

    div-float/2addr v0, p4

    new-instance p4, Ljava/lang/StringBuilder;

    const-string v2, "NoiseS:"

    invoke-direct {p4, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {p4, v1}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;

    const-string v2, ", NoiseO:"

    invoke-virtual {p4, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {p4, v0}, Ljava/lang/StringBuilder;->append(F)Ljava/lang/StringBuilder;

    invoke-virtual {p4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p4

    iget-object v2, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->b:Ljava/lang/String;

    invoke-static {v2, p4}, Lcom/particlesdevs/photoncamera/util/Log;->b(Ljava/lang/String;Ljava/lang/String;)V

    iget-object p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v2, "NOISES"

    const/4 v3, 0x1

    new-array v4, v3, [F

    const/4 v5, 0x0

    aput v1, v4, v5

    invoke-virtual {p4, v2, v4}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v2, "NOISEO"

    new-array v4, v3, [F

    aput v0, v4, v5

    invoke-virtual {p4, v2, v4}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v2, "MOIRE"

    new-array v4, v3, [F

    aput p3, v4, v5

    invoke-virtual {p4, v2, v4}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->luma:F

    new-array v2, v3, [F

    aput p4, v2, v5

    const-string p4, "LUMA"

    invoke-virtual {p3, p4, v2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->shadowBoost:F

    new-array v2, v3, [F

    aput p4, v2, v5

    const-string p4, "SHADOWBOOST"

    invoke-virtual {p3, p4, v2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget-object p4, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget-object p4, p4, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->k:Lcom/particlesdevs/photoncamera/processing/render/Parameters;

    iget-object p4, p4, Lcom/particlesdevs/photoncamera/processing/render/Parameters;->e:Landroid/graphics/Point;

    const-string v2, "INSIZE"

    invoke-virtual {p3, v2, p4}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->i(Ljava/lang/String;Landroid/graphics/Point;)V

    add-float/2addr v1, v0

    iget p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->noiseTarget:F

    div-float/2addr v1, p3

    float-to-double p3, v1

    const-wide v0, 0x3e7ad7f29abcaf48L    # 1.0E-7

    invoke-static {p3, p4, v0, v1}, Ljava/lang/Math;->max(DD)D

    move-result-wide p3

    invoke-static {p3, p4}, Ljava/lang/Math;->sqrt(D)D

    move-result-wide p3

    iget v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->noiseToKernelSize:F

    float-to-double v0, v0

    mul-double/2addr p3, v0

    const-wide/high16 v0, 0x3ff0000000000000L    # 1.0

    add-double/2addr p3, v0

    iget v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->minSize:I

    double-to-int v1, p3

    add-int/2addr v0, v1

    rem-int/lit8 v1, v1, 0x2

    sub-int/2addr v0, v1

    iget v1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/postpipeline/ESD3D2;->maxSize:I

    invoke-static {v0, v1}, Ljava/lang/Math;->min(II)I

    move-result v0

    new-instance v1, Ljava/lang/StringBuilder;

    const-string v2, "KernelSize: "

    invoke-direct {v1, v2}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V

    invoke-virtual {v1, p3, p4}, Ljava/lang/StringBuilder;->append(D)Ljava/lang/StringBuilder;

    const-string v2, " MSIZE: "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v2, "ESD3D"

    invoke-static {v2, v1}, Lcom/particlesdevs/photoncamera/util/Log;->b(Ljava/lang/String;Ljava/lang/String;)V

    iget-object v1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    double-to-float p3, p3

    new-array p4, v3, [F

    aput p3, p4, v5

    const-string p3, "KERNELSIZE"

    invoke-virtual {v1, p3, p4}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->l(Ljava/lang/String;[F)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string p4, "MSIZE"

    filled-new-array {v0}, [I

    move-result-object v0

    invoke-virtual {p3, p4, v0}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->m(Ljava/lang/String;[I)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string p4, "denoise/esd3d2"

    invoke-virtual {p3, p4, v5}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->t(Ljava/lang/String;Z)V

    iget-object p3, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string p4, "InputBuffer"

    invoke-virtual {p3, p4, p1}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->o(Ljava/lang/String;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    invoke-virtual {p1, p2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->f(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;)V

    return-void
.end method

.method public final l(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;I)V
    .locals 2

    iget-object v0, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v1, "SCALE"

    filled-new-array {p5}, [I

    move-result-object p5

    invoke-virtual {v0, v1, p5}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->m(Ljava/lang/String;[I)V

    iget-object p5, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v0, "denoise/guidedupsample"

    const/4 v1, 0x0

    invoke-virtual {p5, v0, v1}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->t(Ljava/lang/String;Z)V

    iget-object p5, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string v0, "LowresInput"

    invoke-virtual {p5, v0, p1}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->o(Ljava/lang/String;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string p5, "Guide"

    invoke-virtual {p1, p5, p2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->o(Ljava/lang/String;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    const-string p2, "GuideHigh"

    invoke-virtual {p1, p2, p3}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->o(Ljava/lang/String;Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget-object p2, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget p2, p2, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->n:F

    const/4 p3, 0x1

    new-array p5, p3, [F

    aput p2, p5, v1

    const-string p2, "noiseS"

    invoke-virtual {p1, p2, p5}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->r(Ljava/lang/String;[F)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget-object p2, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->f:Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;

    iget p2, p2, Lcom/particlesdevs/photoncamera/processing/opengl/GLBasePipeline;->o:F

    new-array p5, p3, [F

    aput p2, p5, v1

    const-string p2, "noiseO"

    invoke-virtual {p1, p2, p5}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->r(Ljava/lang/String;[F)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iget-object p2, p4, Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;->b:Landroid/graphics/Point;

    invoke-virtual {p1, p4, p2}, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->g(Lcom/particlesdevs/photoncamera/processing/opengl/GLTexture;Landroid/graphics/Point;)V

    iget-object p1, p0, Lcom/particlesdevs/photoncamera/processing/opengl/nodes/Node;->i:Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;

    iput-boolean p3, p1, Lcom/particlesdevs/photoncamera/processing/opengl/GLProg;->j:Z

    return-void
.end method
