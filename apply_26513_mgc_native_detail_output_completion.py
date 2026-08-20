#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

CHANGED = (
    'app/src/main/java/com/hinnka/mycamera/processor/MgcSpatialMergeTuning.kt',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
    'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


def transform_spatial_tuning(text: str) -> str:
    if 'IRIS_26513_MGC_NATIVE_DETAIL_FOOTPRINT' in text:
        raise RuntimeError('26513 Spatial detail marker unexpectedly pre-exists')
    const_anchor = '''    private const val DEFAULT_SELECTED_FRAME_MULTIPLIER = 1f\n'''
    const_new = '''    private const val DEFAULT_SELECTED_FRAME_MULTIPLIER = 1f\n\n    /* IRIS_26513_MGC_NATIVE_DETAIL_FOOTPRINT\n     * Keep the exact MGC 9.6 Spatial-RGB curve as the authority, then narrow only\n     * its spatial reconstruction footprint by 10%, never beyond MGC's own 0.40\n     * RGB scale ceiling. Alignment, rejection, Bento, opponent-color equations,\n     * covariance, luma/chroma denoise and all output rendering remain unchanged.\n     */\n    private const val IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER = 1.10f\n    private const val IRIS_26513_RGB_DETAIL_SCALE_MAX = 0.40f\n'''
    text = replace_once(text, const_anchor, const_new, 'Spatial detail constants')

    old = '''        val snr = mergedSnr(referenceSnr, frameCount)\n        return when (outputMode) {\n            MgcSpatialOutputMode.BAYER -> interpolate(\n                snr,\n                14.5f to 0.6f,\n                29.5f to 0.42f,\n                44f to 0.35f,\n            )\n            MgcSpatialOutputMode.RGB -> interpolate(\n                snr,\n                2.3f to 0.32f,\n                40.1f to 0.365f,\n                51.1f to 0.4f,\n                71f to 0.28f,\n            )\n        }\n'''
    new = '''        val snr = mergedSnr(referenceSnr, frameCount)\n        val nativeMgcScale = when (outputMode) {\n            MgcSpatialOutputMode.BAYER -> interpolate(\n                snr,\n                14.5f to 0.6f,\n                29.5f to 0.42f,\n                44f to 0.35f,\n            )\n            MgcSpatialOutputMode.RGB -> interpolate(\n                snr,\n                2.3f to 0.32f,\n                40.1f to 0.365f,\n                51.1f to 0.4f,\n                71f to 0.28f,\n            )\n        }\n        return if (outputMode == MgcSpatialOutputMode.RGB) {\n            (nativeMgcScale * IRIS_26513_RGB_DETAIL_SCALE_MULTIPLIER)\n                .coerceIn(nativeMgcScale, IRIS_26513_RGB_DETAIL_SCALE_MAX)\n        } else {\n            nativeMgcScale\n        }\n'''
    return replace_once(text, old, new, 'Spatial RGB footprint transform')


def transform_hdrx(text: str) -> str:
    if 'IRIS_26513_JPEG_COMPLETION_AFTER_SAVE' in text:
        raise RuntimeError('26513 JPEG completion marker unexpectedly pre-exists')
    early = '''        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));\n        try {\n            processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");\n        }\n        catch (Exception e){\n            Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));\n        }\n        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");\n        //Saves the final bitmap\n        final boolean imageSaved;\n'''
    early_new = '''        img = overlay(img, pipeline.debugData.toArray(new Bitmap[0]));\n        /* Keep non-Motion completion timing equivalent to 26512.\n         * Only Motion waits for its actual JPEG_R save/publication boundary.\n         */\n        if (cameraMode != CameraMode.MOTION) {\n            try {\n                processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");\n            }\n            catch (Exception e){\n                Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));\n            }\n        }\n        imageFile = Paths.get(imageFile.toAbsolutePath() + ".jpg");\n        // Saves the final bitmap before Motion announces JPG completion.\n        final long iris26513JpegSaveStartNs =\n                cameraMode == CameraMode.MOTION ? System.nanoTime() : 0L;\n        final boolean imageSaved;\n'''
    text = replace_once(text, early, early_new, 'remove premature Motion JPG completion callback')

    notify = '''        try {\n            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);\n        }\n        catch (Exception e){\n            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));\n        }\n        if(cameraMode==CameraMode.MOTION&&iris26480DeferredDng!=null){\n'''
    notify_new = '''        try {\n            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);\n        }\n        catch (Exception e){\n            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));\n        }\n        if (cameraMode == CameraMode.MOTION) {\n            /* IRIS_26513_JPEG_COMPLETION_AFTER_SAVE\n             * Motion UI completion follows the actual JPEG_R write and image-saved\n             * notification. Deferred DNG remains background-only.\n             */\n            final long iris26513JpegSaveMs =\n                    (System.nanoTime() - iris26513JpegSaveStartNs) / 1_000_000L;\n            Log.d(TAG,"IRIS_26513_JPEG_COMPLETION_AFTER_SAVE"\n                    + " imageSaved=" + imageSaved\n                    + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs\n                    + " nonMotionCompletionUnchanged=true"\n                    + " deferredDngExcluded=true");\n            try {\n                processingEventsListener.onProcessingFinished("HdrX JPG Processing Finished");\n            }\n            catch (Exception e){\n                Log.d(TAG,"Error in processingEventsListener.onProcessingFinished:"+Log.getStackTraceString(e));\n            }\n        }\n        if(cameraMode==CameraMode.MOTION&&iris26480DeferredDng!=null){\n'''
    return replace_once(text, notify, notify_new, 'move Motion JPG completion after save')


def transform_motion_render(text: str) -> str:
    if 'IRIS_26513_GAINMAP_DIAGNOSTIC_DECIMATION' in text:
        raise RuntimeError('26513 gain-map diagnostic marker unexpectedly pre-exists')
    old = '''                StringBuilder grid = new StringBuilder();\n                final int gridW = 12;\n                final int gridH = 8;\n                for (int gy = 0; gy < gridH; gy++) {\n                    if (gy > 0) grid.append('/');\n                    int sy = Math.min(gainSize.y - 1,\n                            (int)(((gy + 0.5f) * gainSize.y) / gridH));\n                    for (int gx = 0; gx < gridW; gx++) {\n                        int sx = Math.min(gainSize.x - 1,\n                                (int)(((gx + 0.5f) * gainSize.x) / gridW));\n                        int code = rgba.get(sy * gainSize.x + sx) & 0xff;\n                        if (code < 16) grid.append('0');\n                        grid.append(Integer.toHexString(code));\n                    }\n                }\n\n                long roughSum = 0L;\n                long roughCount = 0L;\n                for (int y = 0; y < gainSize.y; y++) {\n                    for (int x = 0; x < gainSize.x; x++) {\n                        int idx = y * gainSize.x + x;\n                        int c = rgba.get(idx) & 0xff;\n                        if (x + 1 < gainSize.x) {\n                            int r = rgba.get(idx + 1) & 0xff;\n                            roughSum += Math.abs(c - r);\n                            roughCount++;\n                        }\n                        if (y + 1 < gainSize.y) {\n                            int d = rgba.get(idx + gainSize.x) & 0xff;\n                            roughSum += Math.abs(c - d);\n                            roughCount++;\n                        }\n                    }\n                }\n                float meanNeighborDelta = roughCount > 0\n                        ? roughSum / (float)roughCount\n                        : 0.0f;\n'''
    new = '''                /* IRIS_26513_GAINMAP_DIAGNOSTIC_DECIMATION\n                 * Keep the actual full-resolution gain map byte-for-byte unchanged.\n                 * Only the diagnostic roughness measurement is reduced from a second\n                 * 12.6 MP full-image walk to 12x8 sampled local pixel neighborhoods.\n                 */\n                StringBuilder grid = new StringBuilder();\n                final int gridW = 12;\n                final int gridH = 8;\n                long roughSum = 0L;\n                long roughCount = 0L;\n                for (int gy = 0; gy < gridH; gy++) {\n                    if (gy > 0) grid.append('/');\n                    int sy = Math.min(gainSize.y - 1,\n                            (int)(((gy + 0.5f) * gainSize.y) / gridH));\n                    for (int gx = 0; gx < gridW; gx++) {\n                        int sx = Math.min(gainSize.x - 1,\n                                (int)(((gx + 0.5f) * gainSize.x) / gridW));\n                        int idx = sy * gainSize.x + sx;\n                        int code = rgba.get(idx) & 0xff;\n                        if (code < 16) grid.append('0');\n                        grid.append(Integer.toHexString(code));\n                        if (sx + 1 < gainSize.x) {\n                            int right = rgba.get(idx + 1) & 0xff;\n                            roughSum += Math.abs(code - right);\n                            roughCount++;\n                        }\n                        if (sy + 1 < gainSize.y) {\n                            int down = rgba.get(idx + gainSize.x) & 0xff;\n                            roughSum += Math.abs(code - down);\n                            roughCount++;\n                        }\n                    }\n                }\n                float meanNeighborDelta = roughCount > 0\n                        ? roughSum / (float)roughCount\n                        : 0.0f;\n'''
    text = replace_once(text, old, new, 'gain-map full-image diagnostic scan')
    log_anchor = '''                        + " meanNeighborDeltaCode=" + meanNeighborDelta\n                        + " provenance=actualGainMapBeforeJpegAttach"\n'''
    log_new = '''                        + " meanNeighborDeltaCode=" + meanNeighborDelta\n                        + " roughnessSampling=12x8_local_neighbors"\n                        + " fullImageRoughnessScan=false"\n                        + " provenance=actualGainMapBeforeJpegAttach"\n'''
    return replace_once(text, log_anchor, log_new, 'gain-map diagnostic telemetry')


def transform_jpeg_native(text: str) -> str:
    if 'IRIS_26513_FAST_HUFFMAN' in text:
        raise RuntimeError('26513 JPEG entropy marker unexpectedly pre-exists')
    anchor = '#define TAG "MotionV2Jpeg444"\n'
    text = replace_once(
        text,
        anchor,
        anchor + '/* IRIS_26513_FAST_HUFFMAN: entropy-table optimization disabled; quantization, 4:4:4 sampling and pixels unchanged. */\n',
        'JPEG entropy marker',
    )
    count = text.count('tj3Set(h,TJPARAM_OPTIMIZE,1)')
    if count != 2:
        raise RuntimeError(f'JPEG optimize anchors: expected 2, found {count}')
    return text.replace('tj3Set(h,TJPARAM_OPTIMIZE,1)', 'tj3Set(h,TJPARAM_OPTIMIZE,0)')


TRANSFORMS = {
    CHANGED[0]: transform_spatial_tuning,
    CHANGED[1]: transform_hdrx,
    CHANGED[2]: transform_motion_render,
    CHANGED[3]: transform_jpeg_native,
}


def expected_text(rel: str, text: str) -> str:
    return TRANSFORMS[rel](text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--patch-out', type=Path, required=True)
    ap.add_argument('--patch-sha-out', type=Path, required=True)
    ns = ap.parse_args()
    root = ns.root.resolve()

    before: dict[str, str] = {}
    after: dict[str, str] = {}
    for rel in CHANGED:
        p = root / rel
        if not p.is_file():
            raise SystemExit(f'missing 26512 source file: {rel}')
        before[rel] = p.read_text()
        after[rel] = expected_text(rel, before[rel])
        if before[rel] == after[rel]:
            raise SystemExit(f'no change produced for {rel}')

    # Safety rule: materialize the complete rollback/audit patch BEFORE writing any source file.
    diff: list[str] = []
    for rel in CHANGED:
        diff.extend(difflib.unified_diff(
            before[rel].splitlines(keepends=True),
            after[rel].splitlines(keepends=True),
            fromfile='a/' + rel,
            tofile='b/' + rel,
        ))
    patch_text = ''.join(diff)
    if not patch_text:
        raise SystemExit('26513 runtime patch unexpectedly empty')
    ns.patch_out.parent.mkdir(parents=True, exist_ok=True)
    ns.patch_out.write_text(patch_text)
    patch_sha = hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{patch_sha}  {ns.patch_out.name}\n')
    print(f'PASS: 26513 rollback/audit patch created BEFORE runtime writes sha256={patch_sha}')

    for rel in CHANGED:
        (root / rel).write_text(after[rel])
        print('CHANGED', rel)
    print('PASS: 26513 applied exactly four runtime paths')


if __name__ == '__main__':
    main()
