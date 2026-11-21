#ifndef IRIS_26972_C_JPEGR_H
#define IRIS_26972_C_JPEGR_H

#include <cstdint>

namespace iris26972c {

// The renderer must supply actual, measured scene gainmap metadata and the
// matching base JPEG ICC / gamut. No invented gainmap or SDR-only fallback.
struct JpegRGainmapMetadata {
    float minContentBoost[3]{};
    float maxContentBoost[3]{};
    float gamma[3]{};
    float offsetSdr[3]{};
    float offsetHdr[3]{};
    float capacityMin = 1.0f;
    float capacityMax = 1.0f;
    bool useBaseColorSpace = true;
    // Google's published libultrahdr gamut enum: BT.709=0, P3=1, BT.2100=2.
    // Caller must identify its developed base image; never guess P3.
    int baseColorGamut = -1;
};

// C-owned Ultra HDR assembly. Expects an already-completed C RAW/Sabre/RAISR
// native-1x JPEG444 base plus a genuine independently produced gain map JPEG.
// Never modifies A/B paths, does not synthesize gain maps or fall back to SDR.
// Exclusive publication: the requested output must not exist already.
bool PublishJpegRFromEncodedJpegs(const char* baseJpegPath,
                                  const char* gainmapJpegPath,
                                  const char* finalJpegRPath,
                                  const JpegRGainmapMetadata& metadata);

}  // namespace iris26972c

#endif
