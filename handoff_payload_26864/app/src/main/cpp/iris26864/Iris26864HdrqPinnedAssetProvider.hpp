#pragma once
// IRIS_26864_HDRQ_PINNED_NDK_ASSET_PROVIDER_DEVELOPMENT_ONLY
// Complements, does not modify, successful 26863 AMaZE asset provider.
// No runtime binding or shader fallback until all RAWR SPIR-V binaries exist.
#include "Iris26864HdrqPinnedSpirvRegistry.hpp"
#include <android/asset_manager.h>
namespace iris26864 {
// AAssetManager must outlive provider and all calls. Caller holds the Java
// asset manager during its existing GL/Vulkan owner lifetime.
PinnedSpirvBytesProvider makePinnedHdrqAndroidAssetProvider(AAssetManager* manager);
}
