#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace iris_spektra {

struct RawDevelopRequest {
    const uint8_t* source = nullptr;
    size_t sourceBytes = 0;
    int sourceWidth = 0;
    int sourceHeight = 0;
    int rowStride = 0;
    int pixelStride = 0;
    int format = 0;
    int rawBounds[4] = {0,0,0,0};
    int sourceCrop[4] = {0,0,0,0};
    int activeRawDomain[4] = {0,0,0,0};
    int cfaArrangement = -1;
    int bayerOffset = -1;
    int blackLevel4[4] = {0,0,0,0};
    int whiteLevel = 0;
    const float* lensShading = nullptr;
    int lensShadingRows = 0;
    int lensShadingCols = 0;
    float sensorToLinearSrgb[9] = {0};
    int outputWidth = 0;
    int outputHeight = 0;
    bool savedPhoto = false;
    float chromaDenoiseStrength = 0.0f;
    float sensorClipThreshold = 0.985f;
};

/**
 * Spektra-owned packed RAW developer used by both VF-S and saved stills.
 *
 * This owner deliberately has no Vulkan/GL dependency. It consumes only a detached Camera2 RAW
 * buffer plus immutable metadata and produces scene-linear RGBA16F for the existing public
 * SPEKTRA film/print renderer. Preview work is drop-if-busy; saved work has priority.
 */
class SpektraRawCpuOwner {
public:
    static SpektraRawCpuOwner& instance();
    bool process(const RawDevelopRequest& request, std::vector<uint8_t>* rgba16f,
            bool* previewDropped, double* elapsedMicros, std::string* error);
    void release();
    void stats(uint64_t out[6]) const;

private:
    SpektraRawCpuOwner();
    ~SpektraRawCpuOwner();
    SpektraRawCpuOwner(const SpektraRawCpuOwner&) = delete;
    SpektraRawCpuOwner& operator=(const SpektraRawCpuOwner&) = delete;
    struct Impl;
    Impl* impl_;
};

} // namespace iris_spektra
