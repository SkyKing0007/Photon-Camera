#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>
#include <string>

namespace iris_spektra {

struct RawDevelopRequest {
    const uint8_t* source = nullptr;
    size_t sourceBytes = 0;
    int sourceWidth = 0;
    int sourceHeight = 0;
    int rowStride = 0;
    int pixelStride = 0;
    int format = 0;
    int rawBounds[4] = {};
    int sourceCrop[4] = {};
    int activeRawDomain[4] = {};
    int cfaArrangement = -1;
    int bayerOffset = -1;
    int blackLevel4[4] = {};
    int whiteLevel = 0;
    const float* lensShading = nullptr;
    int lensShadingRows = 0;
    int lensShadingCols = 0;
    float sensorToLinearSrgb[9] = {};
    int outputWidth = 0;
    int outputHeight = 0;
    bool savedPhoto = false;
    float chromaDenoiseStrength = 0.0f;
    float sensorClipThreshold = 0.985f;
};

class SpektraRawVulkanOwner {
public:
    static SpektraRawVulkanOwner& instance();
    bool warmUp(std::string* error);
    bool process(const RawDevelopRequest& request, std::vector<uint8_t>* rgba16f, bool* previewDropped,
                 double* elapsedMicros, std::string* error);
    void release();
    void stats(uint64_t out[6]);

private:
    SpektraRawVulkanOwner();
    ~SpektraRawVulkanOwner();
    SpektraRawVulkanOwner(const SpektraRawVulkanOwner&) = delete;
    SpektraRawVulkanOwner& operator=(const SpektraRawVulkanOwner&) = delete;
    struct Impl;
    Impl* impl_;
};

} // namespace iris_spektra
