#pragma once

#include <cstddef>
#include <cstdint>

namespace iris26972c {

// C-only reference HDR gainmap mathematics, not a substitute for RAW development.
// The caller MUST provide an independently developed, pixel-registered extended
// linear-sRGB HDR reference and the actual finalized sRGB SDR base. RAISR and
// Adobe curve are upstream; this component never synthesizes either source.
constexpr float kGainmapMinRatio = 0.25f;
constexpr float kGainmapMaxRatio = 4.0f;
constexpr float kGainmapOffset = 0.0001f;
constexpr int kGainmapQuality = 95;

struct GainmapTile {
    const uint8_t* sdrRGBA;  // sRGB-encoded, 4 channels, top-to-bottom
    const float* hdrLinearRGB;  // extended linear sRGB, 3 channels, top-to-bottom
    size_t sdrCapacityBytes;
    size_t hdrCapacityBytes;
    int sdrRowStrideBytes;
    int hdrRowStrideBytes;
    int fullWidth;
    int fullHeight;
    int left;
    int top;
    int width;
    int height;
};

// The output is a caller-owned full-image, half-resolution gray gainmap buffer.
// Even-grid tile boundaries plus clipped last tiles give bit-identical output
// to whole-frame evaluation without a full-resolution HDR CPU allocation.
// A failure performs no writes. Caller serializes nonoverlapping tile writes.
bool WriteGainmapTile(const GainmapTile& tile, uint8_t* output,
                      size_t outputCapacityBytes, int outputStrideBytes,
                      float strength = 1.0f);

// Encodes the real gainmap at quality=95, grayscale 4:4:4-equivalent (1 plane).
// Atomic hardlink publication refuses an already existing final pathname.
// The generated JPEG is an INTERMEDIATE, not a published photograph.
bool WriteGainmapJpeg(const uint8_t* gray, size_t capacityBytes,
                      int width, int height, int strideBytes, const char* path);

}  // namespace iris26972c
