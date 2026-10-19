// IRIS_26856_PINNED_19_SHADER_ASSET_OWNER
#include "amaze/PinnedSpirvAssets.hpp"
#include <array>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace amaze {
namespace {
constexpr std::array<const char*, 19> kShaderNames = {{
    "amaze_import.comp", "amaze_gradients.wgsl", "amaze_candidates.wgsl",
    "amaze_choose.wgsl", "amaze_cddiff.wgsl", "amaze_weights.wgsl",
    "amaze_nyquist.wgsl", "amaze_nyquist_vote.wgsl", "amaze_area.wgsl",
    "amaze_hvwt_seq.wgsl", "amaze_green.wgsl", "amaze_refine.wgsl",
    "amaze_diagonal.wgsl", "amaze_pmwt_seq.wgsl", "amaze_rbint.wgsl",
    "amaze_correct.wgsl", "amaze_chroma.wgsl", "amaze_finish.wgsl",
    "amaze_export.comp"
}};
constexpr uint32_t kSpirvMagic = 0x07230203;
constexpr size_t kMinWords = 5;
constexpr size_t kMaxShaderBytes = 2 * 1024 * 1024;
}
ShaderProvider makePinnedSpirvProvider(AAssetManager* assets) {
    if (!assets) throw std::invalid_argument("26856 AMaZE: missing AAssetManager");
    return [assets](std::string_view requested) -> std::vector<uint32_t> {
        size_t index = kShaderNames.size();
        for (size_t i = 0; i < kShaderNames.size(); ++i) {
            if (requested == kShaderNames[i]) { index = i; break; }
        }
        if (index == kShaderNames.size())
            throw std::runtime_error("26856 AMaZE: unknown shader name (no fallback)");
        const std::string stem(kShaderNames[index], std::strchr(kShaderNames[index], '.') - kShaderNames[index]);
        const std::string path = "iris26856/rawr/amaze/spv/" + stem + ".spv";
        using AssetPtr = std::unique_ptr<AAsset, decltype(&AAsset_close)>;
        AssetPtr asset(AAssetManager_open(assets, path.c_str(), AASSET_MODE_STREAMING), &AAsset_close);
        if (!asset) throw std::runtime_error("26856 AMaZE: pinned shader asset not found: " + path);
        const off64_t length = AAsset_getLength64(asset.get());
        if (length < static_cast<off64_t>(kMinWords * 4) ||
            length > static_cast<off64_t>(kMaxShaderBytes) || (length & 3))
            throw std::runtime_error("26856 AMaZE: invalid SPIR-V asset size: " + path);
        std::vector<uint32_t> words(static_cast<size_t>(length) / 4);
        auto* ptr = reinterpret_cast<unsigned char*>(words.data());
        size_t bytesRead = 0;
        while (bytesRead < static_cast<size_t>(length)) {
            const int n = AAsset_read(asset.get(), ptr + bytesRead,
                                      static_cast<size_t>(length) - bytesRead);
            if (n <= 0) throw std::runtime_error("26856 AMaZE: truncated shader asset: " + path);
            bytesRead += static_cast<size_t>(n);
        }
        if (words[0] != kSpirvMagic)
            throw std::runtime_error("26856 AMaZE: invalid SPIR-V magic: " + path);
        return words;
    };
}
} // namespace amaze
