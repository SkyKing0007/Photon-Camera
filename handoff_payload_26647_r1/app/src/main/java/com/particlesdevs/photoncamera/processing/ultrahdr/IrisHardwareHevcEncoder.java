package com.particlesdevs.photoncamera.processing.ultrahdr;

import android.graphics.ImageFormat;
import android.media.Image;
import android.media.MediaCodec;
import android.media.MediaCodecInfo;
import android.media.MediaCodecList;
import android.media.MediaFormat;
import android.os.Build;
import android.util.Range;

import com.particlesdevs.photoncamera.util.Log;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * IRIS_26636_HARDWARE_HEVC_ONLY_OWNER
 *
 * Small synchronous still-picture HEVC bridge used only by the HEIC container plugin. No software
 * fallback is allowed. Buffer input deliberately mirrors AndroidX HeifWriter's flexible-YUV
 * contract so vendor row/pixel strides are respected rather than guessed by native code.
 */
public final class IrisHardwareHevcEncoder {
    private static final String TAG = "IrisHardwareHevc";
    private static final String MIME_HEVC = MediaFormat.MIMETYPE_VIDEO_HEVC;
    private static final long IO_TIMEOUT_US = 5_000_000L;
    private static final double MAX_COMPRESS_RATIO = 0.25;
    /* IRIS_26647_AOSP_DISPLAY_P3_HEVC_COLOR_ASPECTS
     * MediaFormat does not publish SDK constants for Android media's Display-P3/sRGB pair, but
     * AOSP ColorUtils has used these stable platform values since Android 8: standard 10 is
     * Display-P3 (legacy internal name DCI_P3) and transfer 2 is IEC 61966-2-1/sRGB. The HEIF
     * container already publishes the same Display-P3/sRGB/full-range NCLX contract. */
    private static final int AOSP_COLOR_STANDARD_DISPLAY_P3 = 10;
    private static final int AOSP_COLOR_TRANSFER_SRGB = 2;

    private IrisHardwareHevcEncoder() {}

    private static final class EncoderChoice {
        final MediaCodecInfo info;
        final String mime;
        EncoderChoice(MediaCodecInfo info, String mime) { this.info = info; this.mime = mime; }
    }

    public static boolean isHeicUltraHdrAvailable() {
        if (Build.VERSION.SDK_INT < 36) return false;
        try {
            return findHardwareEncoder(0, 0) != null;
        } catch (Throwable ignored) {
            return false;
        }
    }

    private static boolean supportsFlexibleYuv(MediaCodecInfo.CodecCapabilities caps) {
        for (int fmt : caps.colorFormats) {
            if (fmt == MediaCodecInfo.CodecCapabilities.COLOR_FormatYUV420Flexible) return true;
        }
        return false;
    }

    private static EncoderChoice findHardwareEncoder(int width, int height) {
        MediaCodecList list = new MediaCodecList(MediaCodecList.REGULAR_CODECS);
        /* IRIS_26636_ANDROID16_HEIC_UHDR_CODEC_CONTRACT
         * AOSP HeicCompositeStream deliberately disables the opaque dedicated HEIC image codec
         * when HDR gain-map publication is active and uses a hardware video/hevc encoder for both
         * the base and gain map. Match that Android 16 behavior exactly; no software fallback.
         */
        for (MediaCodecInfo info : list.getCodecInfos()) {
            if (!info.isEncoder() || !info.isHardwareAccelerated()) continue;
            MediaCodecInfo.CodecCapabilities caps;
            try {
                caps = info.getCapabilitiesForType(MIME_HEVC);
            } catch (Throwable unsupported) {
                continue;
            }
            if (!supportsFlexibleYuv(caps)) continue;
            if (width > 0 && height > 0) {
                try {
                    if (!caps.getVideoCapabilities().isSizeSupported(width, height)) continue;
                } catch (Throwable badCaps) {
                    continue;
                }
            }
            return new EncoderChoice(info, MIME_HEVC);
        }
        return null;
    }

    private static void copyPlane(byte[] src, int srcOffset, int srcRowStride,
                                  int width, int height, Image.Plane dstPlane) {
        ByteBuffer dst = dstPlane.getBuffer();
        int dstRowStride = dstPlane.getRowStride();
        int dstPixelStride = dstPlane.getPixelStride();
        for (int y = 0; y < height; y++) {
            int s = srcOffset + y * srcRowStride;
            int d = y * dstRowStride;
            if (dstPixelStride == 1) {
                dst.position(d);
                dst.put(src, s, width);
            } else {
                for (int x = 0; x < width; x++) dst.put(d + x * dstPixelStride, src[s + x]);
            }
        }
    }

    private static int startCodeLength(byte[] data, int p) {
        if (p + 3 < data.length && data[p] == 0 && data[p + 1] == 0
                && data[p + 2] == 0 && data[p + 3] == 1) return 4;
        if (p + 2 < data.length && data[p] == 0 && data[p + 1] == 0 && data[p + 2] == 1) return 3;
        return 0;
    }

    private static List<byte[]> splitNalUnits(byte[] data) {
        ArrayList<byte[]> out = new ArrayList<>();
        if (data == null || data.length == 0) return out;
        int first = -1;
        for (int i = 0; i < data.length - 2; i++) {
            if (startCodeLength(data, i) != 0) { first = i; break; }
        }
        if (first >= 0) {
            int p = first;
            while (p < data.length) {
                int sc = startCodeLength(data, p);
                if (sc == 0) { p++; continue; }
                int start = p + sc;
                int next = data.length;
                for (int i = start; i < data.length - 2; i++) {
                    if (startCodeLength(data, i) != 0) { next = i; break; }
                }
                if (next > start) out.add(Arrays.copyOfRange(data, start, next));
                p = next;
            }
            return out;
        }
        // Some codecs expose length-prefixed NALs. Accept only a fully self-consistent stream.
        int p = 0;
        ArrayList<byte[]> lengthPrefixed = new ArrayList<>();
        while (p + 4 <= data.length) {
            int n = ((data[p] & 0xff) << 24) | ((data[p + 1] & 0xff) << 16)
                    | ((data[p + 2] & 0xff) << 8) | (data[p + 3] & 0xff);
            p += 4;
            if (n <= 0 || p + n > data.length) { lengthPrefixed.clear(); break; }
            lengthPrefixed.add(Arrays.copyOfRange(data, p, p + n));
            p += n;
        }
        if (!lengthPrefixed.isEmpty() && p == data.length) return lengthPrefixed;
        out.add(data);
        return out;
    }

    private static void addUniqueNals(List<byte[]> output, byte[] chunk) {
        for (byte[] nal : splitNalUnits(chunk)) {
            if (nal.length < 2) continue;
            boolean duplicate = false;
            for (byte[] old : output) {
                if (Arrays.equals(old, nal)) { duplicate = true; break; }
            }
            if (!duplicate) output.add(nal);
        }
    }

    /** Called synchronously from the libheif encoder plugin through JNI. */
    public static byte[][] encodeI420(
            int width, int height, byte[] i420, int quality, boolean gainMap) throws Exception {
        if (Build.VERSION.SDK_INT < 36) throw new IllegalStateException("HEIC Ultra HDR requires API 36");
        if (width <= 0 || height <= 0 || (width & 1) != 0 || (height & 1) != 0)
            throw new IllegalArgumentException("HEVC I420 dimensions must be positive/even");
        int ySize = Math.multiplyExact(width, height);
        int expected = Math.addExact(ySize, ySize / 2);
        if (i420 == null || i420.length != expected)
            throw new IllegalArgumentException("I420 byte count mismatch");

        EncoderChoice choice = findHardwareEncoder(width, height);
        if (choice == null) throw new IllegalStateException("No hardware HEIC/HEVC encoder supports " + width + "x" + height);
        MediaCodecInfo info = choice.info;
        MediaCodecInfo.CodecCapabilities caps = info.getCapabilitiesForType(choice.mime);
        // IRIS_26637_HEVC_CAPABILITY_PROOF: diagnostic only; encoding contract is unchanged.
        StringBuilder profileLevels = new StringBuilder();
        for (MediaCodecInfo.CodecProfileLevel pl : caps.profileLevels) {
            if (profileLevels.length() > 0) profileLevels.append(',');
            profileLevels.append(pl.profile).append('/').append(pl.level);
        }
        Log.i(TAG, "IRIS_26637_HEVC_CAPS codec=" + info.getName()
                + " colorFormats=" + Arrays.toString(caps.colorFormats)
                + " profileLevels=" + profileLevels);
        MediaCodec codec = null;
        try {
            codec = MediaCodec.createByCodecName(info.getName());
            MediaFormat format = MediaFormat.createVideoFormat(choice.mime, width, height);
            format.setInteger(MediaFormat.KEY_COLOR_FORMAT,
                    MediaCodecInfo.CodecCapabilities.COLOR_FormatYUV420Flexible);
            format.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 0);
            format.setInteger(MediaFormat.KEY_FRAME_RATE, 1);
            /* IRIS_26644_CPU_I420_HEVC_FULL_RANGE_OWNER
             * Our CPU-I420 path does not inherit HeicCompositeStream's full-range P010 dataspace
             * or MPEG4Writer's per-sample range metadata. libheif supplies full-range YUV bytes
             * and the HEIF NCLX items are full-range, so explicitly request FULL from MediaCodec. */
            format.setInteger(MediaFormat.KEY_COLOR_RANGE, MediaFormat.COLOR_RANGE_FULL);
            /* IRIS_26647_HARDWARE_HEVC_BASE_COLOR_CONTRACT
             * The base I420 bytes were generated from the Display-P3 SDR bitmap. If primaries and
             * transfer are left unspecified, AOSP may default a >=4K HEVC stream to BT.2020 plus
             * video transfer, which contradicts the HEIF Display-P3/sRGB NCLX and can visibly lose
             * color after Android decodes the saved file. Request the same AOSP Display-P3/sRGB
             * aspects on the hardware base stream. Gain-map HEVC remains scalar/unspecified; only
             * its full-range sample contract is authoritative. */
            if (!gainMap) {
                format.setInteger(MediaFormat.KEY_COLOR_STANDARD, AOSP_COLOR_STANDARD_DISPLAY_P3);
                format.setInteger(MediaFormat.KEY_COLOR_TRANSFER, AOSP_COLOR_TRANSFER_SRGB);
            }
            MediaCodecInfo.EncoderCapabilities enc = caps.getEncoderCapabilities();
            int q = Math.max(1, Math.min(100, quality));
            if (enc.isBitrateModeSupported(MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CQ)) {
                format.setInteger(MediaFormat.KEY_BITRATE_MODE,
                        MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CQ);
                Range<Integer> range = enc.getQualityRange();
                int mapped = (int) Math.round(range.getLower()
                        + (range.getUpper() - range.getLower()) * (q / 100.0));
                format.setInteger(MediaFormat.KEY_QUALITY, mapped);
            } else {
                int mode = enc.isBitrateModeSupported(MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR)
                        ? MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR
                        : MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR;
                format.setInteger(MediaFormat.KEY_BITRATE_MODE, mode);
                long wanted = Math.round(width * (double) height * 1.5 * 8.0
                        * MAX_COMPRESS_RATIO * (q / 100.0));
                Range<Integer> br = caps.getVideoCapabilities().getBitrateRange();
                int bitrate = br.clamp((int) Math.max(1L, Math.min(Integer.MAX_VALUE, wanted)));
                format.setInteger(MediaFormat.KEY_BIT_RATE, bitrate);
            }

            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE);
            codec.start();

            int input = codec.dequeueInputBuffer(IO_TIMEOUT_US);
            if (input < 0) throw new IllegalStateException("Timed out waiting for HEVC input buffer");
            Image image = codec.getInputImage(input);
            if (image == null || image.getFormat() != ImageFormat.YUV_420_888)
                throw new IllegalStateException("Hardware HEVC encoder did not expose flexible YUV input Image");
            Image.Plane[] planes = image.getPlanes();
            if (planes.length < 3) throw new IllegalStateException("HEVC YUV input plane count < 3");
            copyPlane(i420, 0, width, width, height, planes[0]);
            int uvOffset = ySize;
            copyPlane(i420, uvOffset, width / 2, width / 2, height / 2, planes[1]);
            copyPlane(i420, uvOffset + ySize / 4, width / 2,
                    width / 2, height / 2, planes[2]);
            ByteBuffer inputBuffer = codec.getInputBuffer(input);
            if (inputBuffer == null) throw new IllegalStateException("Hardware HEVC input ByteBuffer unavailable");
            // Match AndroidX HeifWriter: after writing through getInputImage(), queue the full
            // codec buffer capacity so vendor row-stride/pixel-stride storage is not truncated.
            codec.queueInputBuffer(input, 0, inputBuffer.capacity(), 0L, 0);

            int eos = codec.dequeueInputBuffer(IO_TIMEOUT_US);
            if (eos < 0) throw new IllegalStateException("Timed out waiting for HEVC EOS buffer");
            codec.queueInputBuffer(eos, 0, 0, 1_000_000L, MediaCodec.BUFFER_FLAG_END_OF_STREAM);

            ArrayList<byte[]> nals = new ArrayList<>();
            MediaCodec.BufferInfo bi = new MediaCodec.BufferInfo();
            boolean ended = false;
            int emptyPolls = 0;
            while (!ended && emptyPolls < 20) {
                int out = codec.dequeueOutputBuffer(bi, IO_TIMEOUT_US);
                if (out == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                    MediaFormat of = codec.getOutputFormat();
                    int outStandard = of.containsKey(MediaFormat.KEY_COLOR_STANDARD)
                            ? of.getInteger(MediaFormat.KEY_COLOR_STANDARD) : -1;
                    int outTransfer = of.containsKey(MediaFormat.KEY_COLOR_TRANSFER)
                            ? of.getInteger(MediaFormat.KEY_COLOR_TRANSFER) : -1;
                    int outRange = of.containsKey(MediaFormat.KEY_COLOR_RANGE)
                            ? of.getInteger(MediaFormat.KEY_COLOR_RANGE) : -1;
                    Log.i(TAG, "IRIS_26641_HW_HEVC_COLOR_ASPECTS gainMap=" + gainMap
                            + " standard=" + outStandard + " transfer=" + outTransfer
                            + " range=" + outRange);
                    /* IRIS_26647_HEVC_COLOR_ASPECT_RUNTIME_PROOF
                     * Fail closed when the base stream contradicts the exact Display-P3/sRGB/full
                     * contract. The gain map is scalar and keeps unspecified primaries/transfer,
                     * but it must still remain full-range. */
                    if (outRange != MediaFormat.COLOR_RANGE_FULL) {
                        throw new IllegalStateException("Hardware HEVC did not honor full-range I420 contract: range="
                                + outRange + " gainMap=" + gainMap);
                    }
                    if (!gainMap && (outStandard != AOSP_COLOR_STANDARD_DISPLAY_P3
                            || outTransfer != AOSP_COLOR_TRANSFER_SRGB)) {
                        throw new IllegalStateException("Hardware HEVC did not honor Display-P3/sRGB contract: standard="
                                + outStandard + " transfer=" + outTransfer);
                    }
                    Log.i(TAG, "IRIS_26647_HEVC_COLOR_ASPECT_PROOF gainMap=" + gainMap
                            + " requestedRange=FULL outputRange=" + outRange
                            + " requestedStandard=" + (gainMap ? "UNSPECIFIED" : "DISPLAY_P3(10)")
                            + " outputStandard=" + outStandard
                            + " requestedTransfer=" + (gainMap ? "UNSPECIFIED" : "SRGB(2)")
                            + " outputTransfer=" + outTransfer);
                    for (int i = 0; i < 4; i++) {
                        ByteBuffer csd = of.getByteBuffer("csd-" + i);
                        if (csd == null) continue;
                        ByteBuffer dup = csd.duplicate();
                        byte[] bytes = new byte[dup.remaining()];
                        dup.get(bytes);
                        addUniqueNals(nals, bytes);
                    }
                    continue;
                }
                if (out == MediaCodec.INFO_TRY_AGAIN_LATER) { emptyPolls++; continue; }
                if (out < 0) continue;
                emptyPolls = 0;
                ByteBuffer ob = codec.getOutputBuffer(out);
                if (ob != null && bi.size > 0) {
                    ByteBuffer dup = ob.duplicate();
                    dup.position(bi.offset);
                    dup.limit(bi.offset + bi.size);
                    byte[] bytes = new byte[bi.size];
                    dup.get(bytes);
                    addUniqueNals(nals, bytes);
                }
                ended = (bi.flags & MediaCodec.BUFFER_FLAG_END_OF_STREAM) != 0;
                codec.releaseOutputBuffer(out, false);
            }
            if (!ended || nals.isEmpty()) throw new IllegalStateException("Incomplete hardware HEVC output");
            boolean hasVps = false, hasSps = false, hasPps = false, hasImage = false;
            for (byte[] nal : nals) {
                int type = (nal[0] >> 1) & 0x3f;
                hasVps |= type == 32;
                hasSps |= type == 33;
                hasPps |= type == 34;
                hasImage |= type <= 31;
            }
            if (!(hasVps && hasSps && hasPps && hasImage))
                throw new IllegalStateException("Hardware HEVC output missing VPS/SPS/PPS/image NAL");
            Log.i(TAG, "IRIS_26636_HW_HEVC encoded=" + width + "x" + height
                    + " codec=" + info.getName() + " mime=" + choice.mime
                    + " gainMap=" + gainMap + " nals=" + nals.size()
                    + " softwareFallback=false dedicatedHeicCodec=false");
            return nals.toArray(new byte[0][]);
        } finally {
            if (codec != null) {
                try { codec.stop(); } catch (Throwable ignored) {}
                try { codec.release(); } catch (Throwable ignored) {}
            }
        }
    }
}
