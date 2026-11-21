#pragma once

#include <cstddef>
#include <cstdint>

namespace iris26972c {

// Actual donor bjzhou/PhotonCamera 1.29.0 RAISR C ABI from its Actions-compiled
// ARM64 libmy-native-lib.so, isolated under a unique pinned SONAME.
using DonorRaisr2x = int (*)(const float* encodedSrgbRgba, int sourceWidth,
                            int sourceHeight, uint8_t* coreRgba2x,
                            int coreLeft, int coreTop, int coreWidth,
                            int coreHeight, float resampleRate);

struct DonorRaisrTile {
    const float* encodedSrgbRgba;
    size_t sourceCapacityBytes;
    int sourceRowStrideBytes;
    int sourceGlobalLeft, sourceGlobalTop;
    int sourceWidth, sourceHeight;
    int nativeFullWidth, nativeFullHeight;
    int nativeCoreLeft, nativeCoreTop;
    int nativeCoreWidth, nativeCoreHeight;
};

// C-only full native-grid finishing tile: actual learned donor RAISR 2x ->
// global-phase anti-aliased 1x, never an alternative interpolation path.
// The source tile must include the donor's 16-pixel context plus the final
// decimator's 3-pixel halo. The caller retains all ownership.
// No output bytes are modified if either stage fails.
bool ProcessRealDonorRaisrTile(const DonorRaisrTile& tile, uint8_t* finalNativeRgba,
                              size_t finalCapacityBytes, int finalStrideBytes);

// Unit-only dependency injection for proving the host geometry/ownership.
// This is not used as a synthetic fallback by production JNI.
bool ProcessRaisrTileWithFunction(const DonorRaisrTile& tile, uint8_t* finalNativeRgba,
                                  size_t finalCapacityBytes, int finalStrideBytes,
                                  DonorRaisr2x verifiedDonorFunction);

}  // namespace iris26972c
