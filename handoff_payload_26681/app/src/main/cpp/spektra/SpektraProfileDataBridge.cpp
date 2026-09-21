#include "SpektraProfileDataBridge.h"
#include "SpektraProfileManifest.h"
#include "SpektraProfileCurves.h"

#include <android/asset_manager.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>

namespace {
std::mutex gMutex;
std::vector<uint8_t> gBlob;
std::array<spektrafilm::ProfileCurveSet, iris_spektra_manifest::kFilmCount> gFilms{};
std::array<spektrafilm::ProfileCurveSet, iris_spektra_manifest::kPaperCount> gPapers{};
bool gReady = false;

const float *fp(iris_spektra_manifest::Span s) {
    if (s.bytes == 0u) return nullptr;
    if (static_cast<uint64_t>(s.offset) + s.bytes > gBlob.size()) return nullptr;
    return reinterpret_cast<const float *>(gBlob.data() + s.offset);
}

const uint32_t *up(iris_spektra_manifest::Span s) {
    if (s.bytes == 0u) return nullptr;
    if (static_cast<uint64_t>(s.offset) + s.bytes > gBlob.size()) return nullptr;
    return reinterpret_cast<const uint32_t *>(gBlob.data() + s.offset);
}

const iris_spektra_manifest::GlobalSpan *global(const char *name) {
    for (const auto &g : iris_spektra_manifest::kGlobals) {
        if (std::strcmp(g.name, name) == 0) return &g;
    }
    return nullptr;
}

template <size_t N>
void fillProfile(const iris_spektra_manifest::Profile &in, spektrafilm::ProfileCurveSet &out) {
    (void)N;
    out.stock = in.stock;
    out.name = in.name;
    out.type = in.type;
    out.referenceIlluminant = in.reference;
    out.wavelengthCount = in.wavelengthCount;
    out.exposureCount = in.exposureCount;
    out.wavelengths = fp(in.wavelengths);
    out.logSensitivity = fp(in.logSensitivity);
    out.bandpassHanatos2025 = fp(in.bandpassHanatos2025);
    out.hanatos2026WindowParams = fp(in.hanatos2026WindowParams);
    out.referenceIlluminantSpectrum = fp(in.referenceIlluminantSpectrum);
    out.inputToReferenceXyz = fp(in.inputToReferenceXyz);
    out.inputToSrgb = fp(in.inputToSrgb);
    out.mallettBasisIlluminant = fp(in.mallettBasisIlluminant);
    out.mallettRawMidgrayGreen = in.mallettRawMidgrayGreen;
    out.logExposure = fp(in.logExposure);
    out.densityCurves = fp(in.densityCurves);
    out.channelDensity = fp(in.channelDensity);
    out.baseDensity = fp(in.baseDensity);
    out.densityCurveMinimum = fp(in.densityCurveMinimum);
    out.densityCurveLayers = fp(in.densityCurveLayers);
    out.densityCurveLayerMaxima = fp(in.densityCurveLayerMaxima);
    out.halationStrength = fp(in.halationStrength);
    out.halationFirstSigmaUm = fp(in.halationFirstSigmaUm);
    out.dirGammaSameLayerRgb = fp(in.dirGammaSameLayerRgb);
    out.dirGammaRToGb = fp(in.dirGammaRToGb);
    out.dirGammaGToRb = fp(in.dirGammaGToRb);
    out.dirGammaBToRg = fp(in.dirGammaBToRg);
    out.scanIlluminant = fp(in.scanIlluminant);
    out.scanToOutputRgb = fp(in.scanToOutputRgb);
}

const float *gf(const char *name) {
    const auto *g = global(name);
    return g ? fp(g->span) : nullptr;
}
const uint32_t *gu(const char *name) {
    const auto *g = global(name);
    return g ? up(g->span) : nullptr;
}

constexpr const char *kColorLabels[26] = {
    "ARRI LogC4", "ARRI LogC3 EI800", "BMDFilm WideGamut Gen5",
    "DaVinci Intermediate WideGamut", "RED Log3G10 REDWideGamutRGB",
    "Sony S-Log3 S-Gamut3", "Sony S-Log3 S-Gamut3.Cine",
    "Canon Log2 CinemaGamut D55", "Canon Log3 CinemaGamut D55",
    "Panasonic V-Log V-Gamut", "ACES2065-1", "ACEScg", "ACEScct", "ACEScc",
    "Linear Rec.2020", "Linear Rec.709", "Linear P3-D65", "sRGB", "Display P3",
    "ProPhoto RGB", "Adobe RGB (1998)", "DCI-P3", "P3-D65 Gamma 2.2",
    "P3-D65 Gamma 2.6", "Rec.709 Gamma 2.2", "Rec.709 Gamma 2.4"
};
}

namespace iris_spektra {
bool initializeProfileData(AAssetManager *manager, std::string *error) {
    std::lock_guard<std::mutex> lock(gMutex);
    if (gReady) return true;
    if (!manager) {
        if (error) *error = "Spektra AssetManager is null";
        return false;
    }
    AAsset *asset = AAssetManager_open(manager, "spektra/data/SpektraProfileData.bin", AASSET_MODE_BUFFER);
    if (!asset) {
        if (error) *error = "SpektraProfileData.bin missing";
        return false;
    }
    const off_t length = AAsset_getLength(asset);
    if (length != static_cast<off_t>(iris_spektra_manifest::kProfileDataBytes)) {
        if (error) *error = "Spektra profile bundle size mismatch";
        AAsset_close(asset);
        return false;
    }
    gBlob.resize(static_cast<size_t>(length));
    const int64_t read = AAsset_read(asset, gBlob.data(), gBlob.size());
    AAsset_close(asset);
    if (read != static_cast<int64_t>(gBlob.size())) {
        gBlob.clear();
        if (error) *error = "Spektra profile bundle read failed";
        return false;
    }
    static const uint8_t magic[8] = {'I','S','P','K','T','B','0','1'};
    if (gBlob.size() < sizeof(magic) || std::memcmp(gBlob.data(), magic, sizeof(magic)) != 0) {
        gBlob.clear();
        if (error) *error = "Spektra profile bundle magic mismatch";
        return false;
    }
    for (uint32_t i = 0; i < iris_spektra_manifest::kFilmCount; ++i) {
        fillProfile<iris_spektra_manifest::kFilmCount>(iris_spektra_manifest::kFilmProfiles[i], gFilms[i]);
    }
    for (uint32_t i = 0; i < iris_spektra_manifest::kPaperCount; ++i) {
        fillProfile<iris_spektra_manifest::kPaperCount>(iris_spektra_manifest::kPaperProfiles[i], gPapers[i]);
    }
    if (std::strcmp(gFilms[2].stock, "kodak_portra_400") != 0 ||
        std::strcmp(gPapers[3].stock, "kodak_supra_endura") != 0) {
        gBlob.clear();
        if (error) *error = "Spektra factory stock ordering mismatch";
        return false;
    }
    gReady = true;
    return true;
}
bool profileDataReady() {
    std::lock_guard<std::mutex> lock(gMutex);
    return gReady;
}
}

namespace spektrafilm {
const ProfileCurveSet *filmProfileCurves(int32_t index) {
    if (!gReady || index < 0 || index >= static_cast<int32_t>(gFilms.size())) return nullptr;
    return &gFilms[static_cast<size_t>(index)];
}
const ProfileCurveSet *paperProfileCurves(int32_t index) {
    if (!gReady || index < 0 || index >= static_cast<int32_t>(gPapers.size())) return nullptr;
    return &gPapers[static_cast<size_t>(index)];
}
const HanatosSpectraLutInfo &hanatosSpectraLutInfo() {
    static const HanatosSpectraLutInfo info{192u, 192u, 81u, 2985984u};
    return info;
}
const float *inputMeterXyzMatrices() { return gf("input_meter_xyz"); }
const uint32_t *colorTransferKinds() { return gu("color_transfer_kinds"); }
const float *colorTransferParams() { return gf("color_transfer_params"); }
const char *colorSpaceLabel(int32_t index) {
    return (index >= 0 && index < 26) ? kColorLabels[index] : "";
}
const float *colorDecodeLuts() { return gf("color_decode_luts"); }
const float *colorEncodeLuts() { return gf("color_encode_luts"); }
const float *standardObserverCmfs() { return gf("standard_observer_cmfs"); }
const float *thKg3Illuminant() { return gf("th_kg3_illuminant"); }
const float *customEnlargerFilters() { return gf("custom_enlarger_filters"); }
const float *neutralPrintFilters() { return gf("neutral_print_filters"); }
const float *academyPrinterDensityResponsivities() { return gf("academy_responsivities"); }
const float *academyPrinterDensityNeutralOffsets() { return gf("academy_neutral_offsets"); }
const float *academyPrinterDensityData() { return gf("academy_density_data"); }
const float *academyPrinterDensityInfluxSpectrum() { return gf("academy_influx"); }
float colorDecodeLutMin() { return -0.125f; }
float colorDecodeLutMax() { return 1.5f; }
float colorEncodeLutMin() { return -0.25f; }
float colorEncodeLutMax() { return 64.0f; }
}
