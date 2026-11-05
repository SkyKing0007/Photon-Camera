package com.particlesdevs.photoncamera.processing.parameters;

/** IRIS_26552_NIGHT_DYNAMIC_2_TO_50_FRAME_OWNER
 * Dedicated Night remains a fresh post-shutter bracket, but the shutter-time frame budget is now
 * frozen from the shared frame-count preference. Night never uses Motion ZSL/pre-shutter RAWs.
 * N=2 is SHORT-only; N>=3 preserves the proven 12+3 ratio with deterministic integer rounding.
 */
public final class IrisNightFrameSelector {
    public static final int MIN_NIGHT_FRAMES = 2;
    public static final int MAX_NIGHT_FRAMES = 50;

    public static final class Plan {
        public final int totalFrames;
        public final int shortFrames;
        public final int longFrames;

        private Plan(int totalFrames, int shortFrames, int longFrames, boolean bNormalOnly) {
            if (totalFrames < MIN_NIGHT_FRAMES || totalFrames > MAX_NIGHT_FRAMES)
                throw new IllegalArgumentException("26552 Night total out of range=" + totalFrames);
            if (shortFrames < 2 || longFrames < 0 || shortFrames + longFrames != totalFrames)
                throw new IllegalArgumentException("26552 Night invalid role split short=" + shortFrames
                        + " long=" + longFrames + " total=" + totalFrames);
            if (totalFrames == 2 && longFrames != 0)
                throw new IllegalArgumentException("26552 two-frame Night must be 2 SHORT + 0 LONG");
            if (!bNormalOnly && totalFrames >= 3 && longFrames < 1)
                throw new IllegalArgumentException("26552 Night A >=3 frames requires LONG evidence");
            if (bNormalOnly && (shortFrames != totalFrames || longFrames != 0))
                throw new IllegalArgumentException("26903 Night B requires exactly N NORMAL frames");
            this.totalFrames = totalFrames;
            this.shortFrames = shortFrames;
            this.longFrames = longFrames;
        }

        public boolean isShortFrame(int index) {
            if (index < 0 || index >= totalFrames)
                throw new IndexOutOfBoundsException("26552 Night frame index=" + index + " total=" + totalFrames);
            return index < shortFrames;
        }
    }

    private IrisNightFrameSelector() {}

    public static int clampNightFrames(int requestedMaximum) {
        return Math.max(MIN_NIGHT_FRAMES, Math.min(MAX_NIGHT_FRAMES, requestedMaximum));
    }

    public static Plan freezePlan(int requestedMaximum) {
        final int total = clampNightFrames(requestedMaximum);
        // round(N/5) for integer N, written without floating-point ambiguity.
        final int longFrames = total == 2 ? 0 : Math.max(1, (total + 2) / 5);
        return new Plan(total, total - longFrames, longFrames, false);
    }

    /** Only Night-selected B uses the Photo B N-NORMAL budget, never Night A LONG. */
    public static Plan freezeNormalOnlyB(int selectedBFrameCount) {
        final int n = clampNightFrames(selectedBFrameCount);
        return new Plan(n, n, 0, true);
    }

    public static int getFrames(int requestedMaximum) {
        return freezePlan(requestedMaximum).totalFrames;
    }
}
