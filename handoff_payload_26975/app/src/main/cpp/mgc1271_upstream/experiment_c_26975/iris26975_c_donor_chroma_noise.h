#pragma once
#include "mgc_denoise_static.h"

// C-owned port of pinned bjzhou/PhotonCamera V25 CreateChromaDenoiseNoiseModelBuffers.
// The successful 26974 A/B builder advances with the eight-tap luma kernel.
// Donor chroma advances with [1,3,3,1]/8 instead; do NOT change A/B's builder.
namespace photon::experiment_c_26975 {
bool BuildDonorChromaNoiseBuffers(
    const float read_noise[3], float shot_noise, float quadratic_noise,
    const float correlation[128], const float strength[5],
    const float outlier_threshold[5],
    photon::mgc_denoise::ChromaDenoiseNoiseBuffers* output);
}
