#pragma once
#include <android/asset_manager.h>
#include <string>

namespace iris_spektra {
bool initializeProfileData(AAssetManager *manager, std::string *error);
bool profileDataReady();
}
