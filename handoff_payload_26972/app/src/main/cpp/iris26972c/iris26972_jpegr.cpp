#include "iris26972_jpegr.h"

#include <ultrahdr_api.h>

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <string>
#include <vector>

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace iris26972c {
namespace {
constexpr size_t kMaxEncodedInput = 256U * 1024U * 1024U;

// Minimal bounded JPEG header parser. Parsing stops at the beginning of the
// entropy stream. The libultrahdr decoder separately validates full streams.
struct JpegHead {
    int width = 0;
    int height = 0;
    bool is444 = false;
};

bool ParseJpegHead(const std::vector<uint8_t>& bytes, JpegHead& head) {
    if (bytes.size() < 10 || bytes[0] != 0xff || bytes[1] != 0xd8 ||
        bytes[bytes.size() - 2] != 0xff || bytes.back() != 0xd9) return false;
    size_t i = 2;
    while (i + 4 <= bytes.size()) {
        if (bytes[i] != 0xff) return false;
        while (i < bytes.size() && bytes[i] == 0xff) ++i;
        if (i >= bytes.size()) return false;
        const uint8_t tag = bytes[i++];
        if (tag == 0x00 || tag == 0xd9 || tag == 0xd8 ||
            (tag >= 0xd0 && tag <= 0xd7)) return false;
        if (i + 2 > bytes.size()) return false;
        const size_t len = static_cast<size_t>(bytes[i]) * 256U + bytes[i + 1];
        if (len < 2 || len > bytes.size() - i) return false;
        if (tag == 0xc0 || tag == 0xc1 || tag == 0xc2) {
            if (len < 11 || head.width != 0) return false;
            head.height = bytes[i + 3] * 256 + bytes[i + 4];
            head.width = bytes[i + 5] * 256 + bytes[i + 6];
            const uint8_t channels = bytes[i + 7];
            if (head.width < 1 || head.height < 1 ||
                head.width > 20000 || head.height > 20000 ||
                len != static_cast<size_t>(8 + 3 * channels)) return false;
            if (channels == 3) {
                head.is444 = true;
                for (int c = 0; c < 3; ++c) {
                    const uint8_t sampling = bytes[i + 9 + 3 * c];
                    if (sampling != 0x11) head.is444 = false;
                }
            }
        }
        if (tag == 0xda) return head.width > 0;
        i += len;
    }
    return false;
}

bool ReadFile(const char* path, std::vector<uint8_t>& bytes) {
    if (!path || !*path) return false;
    struct stat st{};
    if (stat(path, &st) != 0 || !S_ISREG(st.st_mode) ||
        st.st_size < 10 || static_cast<uint64_t>(st.st_size) > kMaxEncodedInput)
        return false;
    FILE* f = std::fopen(path, "rb");
    if (!f) return false;
    bytes.resize(static_cast<size_t>(st.st_size));
    const bool ok = std::fread(bytes.data(), 1, bytes.size(), f) == bytes.size() &&
                    std::fgetc(f) == EOF && !std::ferror(f);
    const bool closed = std::fclose(f) == 0;
    if (!ok || !closed) bytes.clear();
    return ok && closed;
}

bool ValidMetadata(const JpegRGainmapMetadata& m) {
    if (m.baseColorGamut != static_cast<int>(UHDR_CG_BT_709) &&
        m.baseColorGamut != static_cast<int>(UHDR_CG_DISPLAY_P3) &&
        m.baseColorGamut != static_cast<int>(UHDR_CG_BT_2100)) return false;
    if (!std::isfinite(m.capacityMin) || !std::isfinite(m.capacityMax) ||
        m.capacityMin < 1.0f || m.capacityMax <= m.capacityMin ||
        m.capacityMax > 10000.0f) return false;
    for (int i = 0; i < 3; ++i) {
        if (!std::isfinite(m.minContentBoost[i]) ||
            !std::isfinite(m.maxContentBoost[i]) ||
            !std::isfinite(m.gamma[i]) ||
            !std::isfinite(m.offsetSdr[i]) ||
            !std::isfinite(m.offsetHdr[i]) ||
            m.minContentBoost[i] <= 0.0f ||
            m.maxContentBoost[i] < m.minContentBoost[i] ||
            m.maxContentBoost[i] > 10000.0f ||
            m.gamma[i] <= 0.0f || m.gamma[i] > 100.0f ||
            m.offsetSdr[i] < 0.0f || m.offsetHdr[i] < 0.0f) return false;
    }
    return true;
}

struct Encoder {
    uhdr_codec_private_t* handle = uhdr_create_encoder();
    ~Encoder() { if (handle) uhdr_release_encoder(handle); }
    Encoder() = default;
    Encoder(const Encoder&) = delete;
    Encoder& operator=(const Encoder&) = delete;
};

bool Okay(uhdr_error_info_t result) { return result.error_code == UHDR_CODEC_OK; }

// Do not rename() over an existing media photo. Atomic link() refuses existing
// output. C caller must reserve appropriate directory ownership ahead of time.
bool PublishExclusively(const char* path, const uint8_t* data, size_t length) {
    if (!path || !*path || !data || length < 16 ||
        length > kMaxEncodedInput || access(path, F_OK) == 0) return false;
    std::string temporary = std::string(path) + ".iris26972c.XXXXXX";
    if (temporary.size() > 4096) return false;
    std::vector<char> tempName(temporary.begin(), temporary.end());
    tempName.push_back('\0');
    const int fd = mkstemp(tempName.data());
    if (fd < 0) return false;
    size_t offset = 0;
    bool ok = true;
    while (offset < length) {
        const ssize_t written = write(fd, data + offset, length - offset);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) { ok = false; break; }
        offset += static_cast<size_t>(written);
    }
    if (ok && fsync(fd) != 0) ok = false;
    if (close(fd) != 0) ok = false;
    if (ok) ok = (link(tempName.data(), path) == 0);
    unlink(tempName.data());
    return ok;
}
}  // namespace

bool PublishJpegRFromEncodedJpegs(const char* baseJpegPath,
                                  const char* gainmapJpegPath,
                                  const char* finalJpegRPath,
                                  const JpegRGainmapMetadata& metadata) {
    if (!baseJpegPath || !gainmapJpegPath || !finalJpegRPath ||
        std::strcmp(baseJpegPath, finalJpegRPath) == 0 ||
        std::strcmp(gainmapJpegPath, finalJpegRPath) == 0 ||
        std::strcmp(baseJpegPath, gainmapJpegPath) == 0 ||
        !ValidMetadata(metadata)) return false;
    std::vector<uint8_t> base, gain;
    if (!ReadFile(baseJpegPath, base) || !ReadFile(gainmapJpegPath, gain)) return false;
    JpegHead baseHead{}, gainHead{};
    if (!ParseJpegHead(base, baseHead) || !baseHead.is444 ||
        !ParseJpegHead(gain, gainHead)) return false;
    // Gain map must describe the *same* complete image with uniform scale.
    const int64_t aspect = static_cast<int64_t>(baseHead.width) * gainHead.height -
                           static_cast<int64_t>(baseHead.height) * gainHead.width;
    if (std::abs(aspect) > std::max(baseHead.width, baseHead.height) ||
        gainHead.width > baseHead.width || gainHead.height > baseHead.height)
        return false;
    Encoder encoder;
    if (!encoder.handle) return false;
    uhdr_compressed_image_t b{};
    b.data = base.data(); b.data_sz = b.capacity = base.size();
    b.cg = static_cast<uhdr_color_gamut_t>(metadata.baseColorGamut);
    b.ct = UHDR_CT_SRGB; b.range = UHDR_CR_FULL_RANGE;
    uhdr_compressed_image_t g{};
    g.data = gain.data(); g.data_sz = g.capacity = gain.size();
    g.cg = UHDR_CG_UNSPECIFIED;
    g.ct = UHDR_CT_UNSPECIFIED;
    g.range = UHDR_CR_UNSPECIFIED;
    uhdr_gainmap_metadata_t m{};
    for (int i = 0; i < 3; ++i) {
        m.min_content_boost[i] = metadata.minContentBoost[i];
        m.max_content_boost[i] = metadata.maxContentBoost[i];
        m.gamma[i] = metadata.gamma[i];
        m.offset_sdr[i] = metadata.offsetSdr[i];
        m.offset_hdr[i] = metadata.offsetHdr[i];
    }
    m.hdr_capacity_min = metadata.capacityMin;
    m.hdr_capacity_max = metadata.capacityMax;
    m.use_base_cg = metadata.useBaseColorSpace ? 1 : 0;
    if (!Okay(uhdr_enc_set_compressed_image(encoder.handle, &b, UHDR_BASE_IMG)) ||
        !Okay(uhdr_enc_set_gainmap_image(encoder.handle, &g, &m)) ||
        !Okay(uhdr_enc_set_output_format(encoder.handle, UHDR_CODEC_JPG)) ||
        !Okay(uhdr_encode(encoder.handle))) return false;
    uhdr_compressed_image_t* encoded = uhdr_get_encoded_stream(encoder.handle);
    if (!encoded || !encoded->data || encoded->data_sz < 16 ||
        encoded->data_sz > kMaxEncodedInput ||
        !is_uhdr_image(encoded->data, static_cast<int>(encoded->data_sz)))
        return false;
    // The JPEG/R container must not convert the SDR base to 4:2:0 or scale it.
    // Inspect the primary image: libultrahdr preserves the source jpeg data.
    std::vector<uint8_t> output(static_cast<const uint8_t*>(encoded->data),
        static_cast<const uint8_t*>(encoded->data) + encoded->data_sz);
    JpegHead outputHead{};
    if (!ParseJpegHead(output, outputHead) || !outputHead.is444 ||
        outputHead.width != baseHead.width || outputHead.height != baseHead.height)
        return false;
    return PublishExclusively(finalJpegRPath, output.data(), output.size());
}

}  // namespace iris26972c
