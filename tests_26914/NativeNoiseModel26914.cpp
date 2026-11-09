#include <rawr/raw_merge_wronski_gpu/RawMergeWronskiGpu.h>
#include <array>
#include <cassert>
#include <cstdio>
int main() {
    using namespace rawr::raw_merge_wronski_gpu;
    constexpr std::array<float,8> noise{.01f,.001f,.02f,.002f,.03f,.003f,.04f,.004f};
    CfaNoiseProfile profile{};
    for (unsigned i=0;i<4;++i) {
        profile.slopeBySite[i]=noise[2*i];
        profile.offsetBySite[i]=noise[2*i+1];
    }
    assert(valid(profile));
    Config config{};config.sensorNoiseProfile=profile;config.estimateNoiseFromBurst=false;
    assert(valid(config));
    assert(config.sensorNoiseProfile->slopeBySite[3]==.04f);
    assert(config.sensorNoiseProfile->offsetBySite[1]==.002f);
    config.sensorNoiseProfile->slopeBySite[2]=0.f;
    assert(!valid(config));
    std::puts("PASS 26914 actual native Wronski site noise model validation and estimated-fit override");
}
