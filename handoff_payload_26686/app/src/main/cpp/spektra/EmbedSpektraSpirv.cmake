if(NOT DEFINED SPV_DIR OR NOT DEFINED OUT)
  message(FATAL_ERROR "SPV_DIR and OUT are required")
endif()
set(NAMES
  SpektraCopy.comp.spv
  SpektraFormatConvert.comp.spv
  SpektraFilmExposure.comp.spv
  SpektraCurveDevelop.comp.spv
  SpektraPrintScan.comp.spv
  SpektraHalation.comp.spv
  SpektraDiffusion.comp.spv
  SpektraDir.comp.spv
  SpektraScannerPost.comp.spv
  SpektraGrain.comp.spv
  SpektraRawDevelop.comp.spv)
file(WRITE "${OUT}" "#include \"SpektraEmbeddedShaders.h\"\n#include <cerrno>\n#include <cstdio>\n#include <cstring>\n#include <sys/stat.h>\n#include <sys/types.h>\n#include <vector>\nnamespace {\n")
set(INDEX 0)
foreach(NAME IN LISTS NAMES)
  set(PATH "${SPV_DIR}/${NAME}")
  if(NOT EXISTS "${PATH}")
    message(FATAL_ERROR "Missing compiled Spektra shader ${PATH}")
  endif()
  file(READ "${PATH}" HEXDATA HEX)
  string(LENGTH "${HEXDATA}" HEXLEN)
  math(EXPR LAST "${HEXLEN} - 2")
  file(APPEND "${OUT}" "static const uint8_t kShader${INDEX}[] = {\n")
  set(COL 0)
  foreach(POS RANGE 0 ${LAST} 2)
    string(SUBSTRING "${HEXDATA}" ${POS} 2 BYTE)
    file(APPEND "${OUT}" "0x${BYTE},")
    math(EXPR COL "${COL} + 1")
    if(COL EQUAL 24)
      file(APPEND "${OUT}" "\n")
      set(COL 0)
    endif()
  endforeach()
  file(APPEND "${OUT}" "\n};\n")
  math(EXPR INDEX "${INDEX} + 1")
endforeach()
file(APPEND "${OUT}" "static const iris_spektra::EmbeddedShader kShaders[] = {\n")
set(INDEX 0)
foreach(NAME IN LISTS NAMES)
  file(APPEND "${OUT}" "  {\"${NAME}\", kShader${INDEX}, sizeof(kShader${INDEX})},\n")
  math(EXPR INDEX "${INDEX} + 1")
endforeach()
file(APPEND "${OUT}" "};\n\nstatic bool mkdirOne(const std::string &p) { if (::mkdir(p.c_str(), 0700) == 0 || errno == EEXIST) return true; return false; }\n}\nnamespace iris_spektra {\nconst EmbeddedShader *embeddedShaders(size_t *count) { if (count) *count = sizeof(kShaders)/sizeof(kShaders[0]); return kShaders; }\nbool materializeEmbeddedShaders(const std::string &root, std::string *error) {\n  if (!mkdirOne(root)) { if(error)*error=\"Unable to create Spektra resource directory\"; return false; }\n  const std::string dir = root + \"/shaders\"; if (!mkdirOne(dir)) { if(error)*error=\"Unable to create Spektra shader directory\"; return false; }\n  for (const auto &s : kShaders) { const std::string path=dir+\"/\"+s.name; FILE *f=std::fopen(path.c_str(),\"wb\"); if(!f){if(error)*error=\"Unable to create \"+path;return false;} const size_t n=std::fwrite(s.data,1,s.bytes,f); const int rc=std::fclose(f); if(n!=s.bytes||rc!=0){if(error)*error=\"Unable to write \"+path;return false;} } return true; }\n}\n")
