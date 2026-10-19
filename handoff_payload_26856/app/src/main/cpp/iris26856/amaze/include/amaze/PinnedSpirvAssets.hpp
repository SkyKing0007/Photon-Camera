// IRIS_26856_PINNED_19_SHADER_ASSET_OWNER
// B-only asset provider. No fallback shaders, no loose path resolution.
#pragma once
#include "amaze/Amaze.hpp"
#include <android/asset_manager.h>

namespace amaze {
// The caller must keep AAssetManager valid while the returned provider is used.
// Every requested shader is checked against the immutable RAWR 19-pass list.
ShaderProvider makePinnedSpirvProvider(AAssetManager* assets);
}
