// C-only independent port from bjzhou/PhotonCamera pinned commit
// 0a8a11defe7d932d8c8a729120a4d5f159e9d677
// mgc_denoise_static/mgc_denoise_static.cpp (V25 chroma noise model).
// No shared A/B native source/ABI changed.
#include "iris26975_c_donor_chroma_noise.h"

#include <algorithm>
#include <cmath>
#include <cstdint>

namespace {
constexpr double kPi = 3.14159265358979323846264338327950288;

float DownsamplingEnergy(const float spectrum[128], int x_factor, int y_factor,
                         float response_offset, float response_cosine_offset) {
    float total = 0.0f;
    for (int outer = 0; outer < 128; ++outer) {
        float inner_sum = 0.0f;
        for (int inner = 0; inner < 128; ++inner) {
            const int wrapped = (outer * y_factor + inner * x_factor) & 127;
            const double angle = static_cast<double>(wrapped) * kPi / 64.0 -
                static_cast<double>(x_factor + y_factor) * kPi;
            const float cosine = static_cast<float>(std::cos(angle));
            const float response = (response_offset - cosine * cosine) +
                (cosine + response_cosine_offset) *
                (cosine + response_cosine_offset);
            inner_sum += spectrum[inner] * response;
        }
        total += inner_sum * spectrum[outer];
    }
    return total * 0.00006103515625f;
}

bool FilterAndDecimateSpectrum(float spectrum[128], const float* filter,
                              int filter_size, float* coefficient_scale) {
    if (std::all_of(spectrum, spectrum + 128, [](float value) {
            return value == 0.0f;
        })) {
        std::fill_n(spectrum, 128, 1.0f);
        *coefficient_scale = 0.0f;
        return true;
    }
    float filtered[128] = {};
    float energy = 0.0f;
    for (int frequency = 0; frequency < 128; ++frequency) {
        double real = 0.0;
        double imaginary = 0.0;
        const double omega =
            (static_cast<double>(frequency) + 0.5) * 2.0 * kPi / 128.0 - kPi;
        for (int tap = 0; tap < filter_size; ++tap) {
            real += static_cast<double>(filter[tap]) *
                std::cos(omega * tap);
            imaginary -= static_cast<double>(filter[tap]) *
                std::sin(omega * tap);
        }
        const float response = static_cast<float>(real * real + imaginary * imaginary);
        filtered[frequency] = spectrum[frequency] * response;
        energy += filtered[frequency];
    }
    energy *= 1.0f / 128.0f;
    if (!(energy > 0.0f) || !std::isfinite(energy)) return false;
    const float inverse_energy = 1.0f / energy;
    for (int index = 0; index < 128; ++index) {
        spectrum[index] = filtered[index] * inverse_energy;
    }
    const float convolution_scale = energy * energy;

    float expanded[256] = {};
    for (int index = 64; index < 128; ++index) {
        const float left = 0.25f * spectrum[index - 1] + 0.75f * spectrum[index];
        const float right = 0.75f * spectrum[index] +
            0.25f * spectrum[std::min(index + 1, 127)];
        expanded[2 * index] = left;
        expanded[2 * index + 1] = right;
        expanded[255 - 2 * index] = left;
        expanded[254 - 2 * index] = right;
    }
    for (int index = 64; index < 128; ++index) {
        const float value = 0.5f * expanded[(index + 192) & 255] +
            0.5f * expanded[index + 64];
        spectrum[index] = value;
        spectrum[127 - index] = value;
    }
    float downsample_energy = 0.0f;
    for (int index = 0; index < 128; ++index) {
        downsample_energy += spectrum[index];
    }
    downsample_energy *= 1.0f / 128.0f;
    if (!(downsample_energy > 0.0f) || !std::isfinite(downsample_energy)) return false;
    const float inverse_downsample_energy = 1.0f / downsample_energy;
    for (int index = 0; index < 128; ++index) {
        spectrum[index] *= inverse_downsample_energy;
    }
    *coefficient_scale = convolution_scale *
        (downsample_energy * downsample_energy);
    return true;
}

bool AdvanceChromaCorrelation(float spectrum[128], float* coefficient_scale) {
    // Unlike the inherited 26974 A/B eight-tap luma builder, V25 chroma uses four taps.
    constexpr float chroma_filter[4] = {0.125f, 0.375f, 0.375f, 0.125f};
    return FilterAndDecimateSpectrum(spectrum, chroma_filter, 4, coefficient_scale);
}
} // namespace

namespace photon::experiment_c_26975 {
bool BuildDonorChromaNoiseBuffers(
    const float read_noise[3], float shot_noise, float quadratic_noise,
    const float correlation[128], const float strength[5],
    const float outlier_threshold[5],
    photon::mgc_denoise::ChromaDenoiseNoiseBuffers* output) {
    if (!read_noise || !correlation || !strength || !outlier_threshold || !output ||
        !std::isfinite(shot_noise) || !std::isfinite(quadratic_noise)) return false;
    float current_correlation[128] = {};
    for (int index = 0; index < 128; ++index) {
        if (!std::isfinite(correlation[index])) return false;
        current_correlation[index] = correlation[index];
    }
    float current_read[3] = {};
    float current_shot = std::max(shot_noise, 0.0f);
    float current_quadratic = std::max(quadratic_noise, 0.0f);
    for (int channel = 0; channel < 3; ++channel) {
        if (!std::isfinite(read_noise[channel])) return false;
        current_read[channel] = std::max(read_noise[channel], 0.0f);
    }
    std::fill_n(output->shot, 24, 0.0f);
    std::fill_n(output->quadratic, 24, 0.0f);

    constexpr float response_offset = 1.0f; // pinned donor default
    constexpr float response_cosine_offset = -1.0f;
    for (int level = 0; level < 4; ++level) {
        for (int branch = 0; branch < 2; ++branch) {
            const int downsample_factor = branch == 0 ? 2 : 1;
            const int tuning_level = level + (downsample_factor == 2 ? 1 : 0);
            const float tuning_strength = std::max(strength[tuning_level], 0.0f);
            const float scale = tuning_strength * tuning_strength /
                static_cast<float>(downsample_factor) *
                DownsamplingEnergy(current_correlation, downsample_factor, 0,
                                   response_offset, response_cosine_offset);
            const int scalar_index = level + branch * 12;
            output->shot[scalar_index] = current_shot * scale;
            output->quadratic[scalar_index] = current_quadratic * scale;
            for (int channel = 0; channel < 3; ++channel) {
                const int index = level + channel * 4 + branch * 12;
                output->read[index] = current_read[channel] * scale;
            }
            output->outlier_threshold[level + branch * 4] =
                static_cast<uint8_t>(static_cast<int>(outlier_threshold[tuning_level]));
        }
        float coefficient_scale = 0.0f;
        if (!AdvanceChromaCorrelation(current_correlation, &coefficient_scale))
            return false;
        for (int channel = 0; channel < 3; ++channel)
            current_read[channel] *= coefficient_scale;
        current_shot *= coefficient_scale;
        current_quadratic *= coefficient_scale;
    }
    return true;
}
} // namespace photon::experiment_c_26975
