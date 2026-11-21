#ifndef IRIS_26972_C_JPEG444_H
#define IRIS_26972_C_JPEG444_H

#include <cstddef>
#include <cstdint>

namespace iris26972c {

// Only C-owned finalized native-1x, post-Sabre and post-genuine-RAISR pixels
// may be passed by the future Experiment C publication owner. This encoder
// performs no RAW reconstruction or alternate image processing.
struct Jpeg444Input {
    const uint8_t* rgba = nullptr;
    size_t capacity = 0;
    int width = 0;
    int height = 0;
    int stride = 0;
    const uint8_t* icc = nullptr;
    size_t iccSize = 0;
};

// Writes quality-95 4:4:4 JPEG via a private C-owned publication path.
// Returns false on any failure, deleting temporary output and never falling
// back to A/B, HEIC, YUV, 4:2:0 or a different reconstruction.
bool EncodeJpeg444Native1x(const Jpeg444Input& input, const char* finalPath);

// Read a native-size, fully developed sRGB RGBA8 horizontal band directly
// from Experiment C's eventual genuine-RAISR tile producer. No full 50MP RGBA
// buffer is allocated by this codec. The callback must fill exactly rows
// packed RGBA scanlines; false aborts atomically without publishing output.
using Jpeg444BandReader = bool (*)(int top, int rows, uint8_t* destination,
                                   int destinationStride, void* context);
struct Jpeg444BandInput {
    int width = 0;
    int height = 0;
    int bandRows = 0;    // 1..256; at most 20 MiB for the RGBA band
    Jpeg444BandReader reader = nullptr;
    void* context = nullptr;
    const uint8_t* icc = nullptr;
    size_t iccSize = 0;
};

bool EncodeJpeg444Native1xFromBands(const Jpeg444BandInput& input,
                                    const char* finalPath);

}  // namespace iris26972c
#endif
