#pragma once
#include <cstdint>
namespace photon::experiment_c_26975 {
// Sabre C-owned port of bjzhou/PhotonCamera V25 low-frequency chroma stage.
// Input/output is full-frame padded planar signed Q14 Y, Cb, Cr.
// No fallback to any A/B image pipeline, no native source changes outside C.
int ApplyLowFrequencyChroma(
    int16_t* planar_yuv, int padded_width, int padded_height,
    const uint16_t* full_strength_q8, int strength_width, int strength_height,
    const float normalized_yuv_read_q14[3], float chroma_shot_q14,
    float chroma_quadratic, const float correlation[128],
    const float chroma_strength[5], const float chroma_outlier[5],
    int log2_downsample, int chroma_median_filter_type);
}
