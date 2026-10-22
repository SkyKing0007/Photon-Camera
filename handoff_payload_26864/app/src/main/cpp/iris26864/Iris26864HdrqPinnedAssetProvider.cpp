// IRIS_26864_HDRQ_NO_SUBSTITUTE_SPIRV_ASSET_PROVIDER
#include "Iris26864HdrqPinnedAssetProvider.hpp"
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <limits>

namespace iris26864 {
namespace {
const std::set<std::string>& pinnedPaths() {
    static const std::set<std::string> names = [] {
        std::set<std::string> values;
        for (const auto& contract : pinnedHdrqContracts()) {
            if (!values.insert("iris26864/rawr/hdrq/spv/"+contract.assetStem+".spv").second)
                throw std::runtime_error("26864 duplicate pinned HDRq asset path");
        }
        if (values.size() != 23u) throw std::runtime_error("26864 incomplete pinned HDRq registry");
        return values;
    }();
    return names;
}
using AssetPtr = std::unique_ptr<AAsset, decltype(&AAsset_close)>;
}
PinnedSpirvBytesProvider makePinnedHdrqAndroidAssetProvider(AAssetManager* manager) {
    if (!manager) throw std::invalid_argument("26864 B-only HDRq AAssetManager missing");
    return [manager](const std::string& exactPath) -> std::vector<uint8_t> {
        // Caller cannot request any A-owned, unpinned or directory-traversal asset.
        if (pinnedPaths().count(exactPath) != 1u)
            throw std::invalid_argument("26864 unlisted SPIR-V asset request");
        AssetPtr asset(AAssetManager_open(manager, exactPath.c_str(), AASSET_MODE_STREAMING), &AAsset_close);
        if (!asset) throw std::runtime_error("26864 pinned RAWR SPIR-V missing: " + exactPath);
        const auto n = AAsset_getLength64(asset.get());
        if (n < 84 || n > 2097152 || n % 4)
            throw std::runtime_error("26864 pinned RAWR SPIR-V invalid byte count: " + exactPath);
        std::vector<uint8_t> result(static_cast<size_t>(n));
        size_t offset=0;
        while (offset < result.size()) {
            const size_t remaining = result.size()-offset;
            const int want = static_cast<int>(remaining > static_cast<size_t>(std::numeric_limits<int>::max())
                                  ? std::numeric_limits<int>::max() : remaining);
            const int got = AAsset_read(asset.get(), result.data()+offset, want);
            if (got <= 0 || got > want)
                throw std::runtime_error("26864 truncated pinned RAWR SPIR-V: " + exactPath);
            offset+=static_cast<size_t>(got);
        }
        // Full interface validation is mandatory in requireCompletePinnedHdrqSpirv,
        // which runs *before* Vulkan shader module and scratch allocation.
        return result;
    };
}
}
