#pragma once
// IRIS_26864_HDRQ_SCHEDULE_PROTOTYPE_NOT_RUNTIME
// Source-matched scheduling of RAWR HDR+ Higher quality, UNIFORM mode only.
// See RAWR HdrPlusRecorder.cpp at pinned commit ce767e80bfce2e1641abf7dad6b1bf504d844fd9
// Vulkan dispatch/descriptor/image barriers must be supplied by actual port;
// this typed plan is not a functioning GPU executor.
#include "Iris26864BMergePlan.hpp"
#include <vector>
#include <stdexcept>
namespace iris26864 {
enum class HdrqStep {
    ShiftTable, ReferenceAlignPrepare, ReferenceRgba, ReferenceTileRms,
    ReferenceSeedDft, ClearTileMismatch,
    CompanionAlignCoarse, CompanionAlignFinest, CompanionPaddedOnly,
    CompanionWarpRgba, CompanionTileMismatch, CompanionForwardDft,
    CompanionRegionMean, CompanionMismatchNorm, CompanionHighlightsNorm,
    CompanionWienerMerge,
    PassDeconvolute, PassBackwardDft, PassBorder, PassAccumulateCfa,
    FinalizeCfa
};
struct HdrqDispatch {
    HdrqStep step;
    uint32_t pass; // 0..3 (4 is final full-CFA normalize)
    uint32_t normalIndex; // position in the validated normals[]; UINT32_MAX for pass-wide
};
inline std::vector<HdrqDispatch> makeHdrqSchedule(const Plan& plan) {
    if(plan.path!=Path::HdrPlusFrequency || plan.normals.size()<2 ||
       plan.referenceNormal>=plan.normals.size() ||
       plan.geometry.outputWidth!=plan.geometry.inputWidth ||
       plan.geometry.outputHeight!=plan.geometry.inputHeight ||
       !plan.createBResources||!plan.lscBeforeAmaze||plan.lscAfterAmaze||
       plan.noiseOwner!=NoiseOwner::HdrqReferenceTileRms)
        throw std::invalid_argument("26864 frequency schedule requires valid B HDRq plan");
    std::vector<HdrqDispatch> out;
    const uint32_t sentinel=UINT32_MAX;
    auto add=[&](HdrqStep s,uint32_t pass,uint32_t n=UINT32_MAX){out.push_back({s,pass,n});};
    // Normal-mode RAWR uses setExposureNormalization (not HDR+ bracketed mode).
    // It applies exposure gains in padded RAW preparation but must not execute
    // bracketed weight-sum, dark-source substitution or brighter-frame order.
    for(uint32_t p=0;p<4u;p++){
        const auto& pass=plan.geometry.passes[p];
        if(p==0)add(HdrqStep::ShiftTable,p);
        if(pass.align)add(HdrqStep::ReferenceAlignPrepare,p);
        add(HdrqStep::ReferenceRgba,p);
        add(HdrqStep::ReferenceTileRms,p);
        add(HdrqStep::ReferenceSeedDft,p);
        add(HdrqStep::ClearTileMismatch,p);
        for(uint32_t k=0;k<plan.normals.size();k++){
            if(k==plan.referenceNormal)continue;
            if(pass.align){
                add(HdrqStep::CompanionAlignCoarse,p,k);
                add(HdrqStep::CompanionAlignFinest,p,k);
            }else add(HdrqStep::CompanionPaddedOnly,p,k);
            add(HdrqStep::CompanionWarpRgba,p,k);
            add(HdrqStep::CompanionTileMismatch,p,k);
            add(HdrqStep::CompanionForwardDft,p,k);
            add(HdrqStep::CompanionRegionMean,p,k);
            add(HdrqStep::CompanionMismatchNorm,p,k);
            add(HdrqStep::CompanionHighlightsNorm,p,k);
            add(HdrqStep::CompanionWienerMerge,p,k);
        }
        add(HdrqStep::PassDeconvolute,p);
        add(HdrqStep::PassBackwardDft,p);
        add(HdrqStep::PassBorder,p);
        add(HdrqStep::PassAccumulateCfa,p);
    }
    add(HdrqStep::FinalizeCfa,4u,sentinel);
    return out;
}
inline void verifyHdrqSchedule(const Plan& plan,const std::vector<HdrqDispatch>& stages) {
    if(plan.path!=Path::HdrPlusFrequency||stages.empty()) throw std::invalid_argument("26864 invalid schedule owner");
    const auto actual=makeHdrqSchedule(plan);
    if(actual.size()!=stages.size())throw std::invalid_argument("26864 schedule stage count mismatch");
    for(size_t i=0;i<actual.size();++i){
        if(stages[i].step!=actual[i].step||stages[i].pass!=actual[i].pass||
           stages[i].normalIndex!=actual[i].normalIndex)
            throw std::invalid_argument("26864 stage order/burst index mismatch");
    }
}
}
