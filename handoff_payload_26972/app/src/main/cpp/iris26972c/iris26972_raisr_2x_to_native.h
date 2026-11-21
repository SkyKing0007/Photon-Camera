#pragma once
#include <cstdint>

namespace iris26972c {
// Host-testable, bounded-core post-RAISR reconstruction. This is NOT the RAISR
// filter bank; its input must be the genuine MGC 2x RGBA8 RAISR output.
// Pixel coordinates are globally anchored. The RAISR tile must contain every
// required 6-pixel output-grid halo; otherwise the operation fails closed.
struct Raisr2xTile {
    const uint8_t* rgba = nullptr;
    int width = 0;
    int height = 0;
    int rowStrideBytes = 0;
    int globalX = 0;
    int globalY = 0;
    int fullWidth = 0;
    int fullHeight = 0;
};

// Writes RGBA8 at exact native-grid coordinates; never enlarges or reduces
// the original sensor-grid output dimensions. outStride is in bytes.
// Return false for missing halo, invalid geometry or invalid buffers.
bool downsampleRaisr2xToNative(const Raisr2xTile& input,
                              int dstX, int dstY, int dstWidth, int dstHeight,
                              uint8_t* output, int outStrideBytes);
}
