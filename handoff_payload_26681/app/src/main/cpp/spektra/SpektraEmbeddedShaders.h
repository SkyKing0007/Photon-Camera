#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
namespace iris_spektra {
struct EmbeddedShader { const char *name; const uint8_t *data; size_t bytes; };
const EmbeddedShader *embeddedShaders(size_t *count);
bool materializeEmbeddedShaders(const std::string &resourceRoot, std::string *error);
}
