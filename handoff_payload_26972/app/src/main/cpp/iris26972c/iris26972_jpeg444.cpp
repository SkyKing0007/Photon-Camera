#include "iris26972_jpeg444.h"

#include <cstdio>
#include <cerrno>
#include <fcntl.h>
#include <cstdlib>
#include <cstring>
#include <csetjmp>
#include <limits>
#include <string>
#include <vector>
#include <unistd.h>

extern "C" {
#include <jpeglib.h>
}

namespace iris26972c {
namespace {
struct JpegFailure {
    jpeg_error_mgr base;
    jmp_buf point;
};

void OnJpegError(j_common_ptr pointer) {
    auto* error = reinterpret_cast<JpegFailure*>(pointer->err);
    longjmp(error->point, 1);
}

bool Valid(const Jpeg444Input& input, const char* path) {
    if (!path || !*path || !input.rgba || input.width < 1 ||
        input.height < 1 || input.width > 20000 || input.height > 20000 ||
        input.stride < 1) return false;
    const size_t widthBytes = static_cast<size_t>(input.width) * 4U;
    if (static_cast<size_t>(input.stride) < widthBytes) return false;
    const size_t rows = static_cast<size_t>(input.height - 1);
    if (rows > (std::numeric_limits<size_t>::max() - widthBytes) /
                   static_cast<size_t>(input.stride)) return false;
    if (input.capacity < rows * static_cast<size_t>(input.stride) + widthBytes)
        return false;
    if ((input.icc == nullptr) != (input.iccSize == 0)) return false;
    // A nonempty profile is optional; when supplied, never silently omit it.
    if (input.iccSize > 4U * 1024U * 1024U) return false;
    return true;
}
} // namespace

bool EncodeJpeg444Native1x(const Jpeg444Input& input, const char* path) {
    if (!Valid(input, path)) return false;
    const std::string name(path);
    if (name.size() > 4000 || access(path, F_OK) == 0) return false;
    std::string pattern = name + ".iris26972c.partial.XXXXXX";
    std::vector<char> temporary(pattern.begin(), pattern.end());
    temporary.push_back('\0');
    // Exclusively reserve a unique scratch path; never share a stale .partial.
    const int fd = mkstemp(temporary.data());
    if (fd < 0) return false;
    FILE* output = fdopen(fd, "wb");
    if (!output) { close(fd); unlink(temporary.data()); return false; }
    jpeg_compress_struct compress{};
    JpegFailure error{};
    compress.err = jpeg_std_error(&error.base);
    error.base.error_exit = OnJpegError;
    // setjmp must not jump over C++ objects with destructors: the scanline
    // scratch is malloc-owned, and other C++ objects were constructed above.
    uint8_t* volatile row = nullptr;
    volatile bool created = false;
    volatile bool ok = false;
    if (setjmp(error.point) == 0) {
        jpeg_create_compress(&compress);
        created = true;
        jpeg_stdio_dest(&compress, output);
        compress.image_width = static_cast<JDIMENSION>(input.width);
        compress.image_height = static_cast<JDIMENSION>(input.height);
        compress.input_components = 3;
        compress.in_color_space = JCS_RGB;
        jpeg_set_defaults(&compress);
        jpeg_set_quality(&compress, 95, TRUE);
        compress.optimize_coding = TRUE; // Matches bjzhou's optimized JPEG444 policy.
        for (int i = 0; i < compress.num_components; ++i) {
            compress.comp_info[i].h_samp_factor = 1;
            compress.comp_info[i].v_samp_factor = 1;
        }
        jpeg_start_compress(&compress, TRUE);
        if (input.icc) {
            jpeg_write_icc_profile(&compress, input.icc,
                                   static_cast<unsigned int>(input.iccSize));
        }
        row = static_cast<uint8_t*>(std::malloc(static_cast<size_t>(input.width) * 3U));
        if (row) {
            ok = true;
            while (compress.next_scanline < compress.image_height) {
                const size_t y = compress.next_scanline;
                const uint8_t* src = input.rgba + y * static_cast<size_t>(input.stride);
                for (int x = 0; x < input.width; ++x) {
                    row[static_cast<size_t>(x) * 3U] = src[static_cast<size_t>(x) * 4U];
                    row[static_cast<size_t>(x) * 3U + 1U] = src[static_cast<size_t>(x) * 4U + 1U];
                    row[static_cast<size_t>(x) * 3U + 2U] = src[static_cast<size_t>(x) * 4U + 2U];
                }
                JSAMPROW scan = row;
                if (jpeg_write_scanlines(&compress, &scan, 1) != 1) {
                    ok = false;
                    break;
                }
            }
            if (ok) jpeg_finish_compress(&compress);
        }
    }
    if (row) std::free(row);
    if (created) jpeg_destroy_compress(&compress);
    if (ok && std::fflush(output) != 0) ok = false;
    if (ok && fsync(fd) != 0) ok = false;
    if (std::fclose(output) != 0) ok = false;
    // rename() would overwrite a competing image despite the earlier access()
    // check. POSIX link() refuses publication if another capture owns the path.
    if (ok && link(temporary.data(), path) != 0) ok = false;
    unlink(temporary.data());
    return ok;
}

// C-only row-band JPEG444: a single bounded RGBA band and one RGB scanline.
bool EncodeJpeg444Native1xFromBands(const Jpeg444BandInput& input,
                                    const char* path) {
    if (!path || !*path || !input.reader || input.width < 1 || input.height < 1 ||
        input.width > 20000 || input.height > 20000 ||
        input.bandRows < 1 || input.bandRows > 256 ||
        (input.icc == nullptr) != (input.iccSize == 0) ||
        input.iccSize > 4U * 1024U * 1024U || access(path, F_OK) == 0) return false;
    const std::string name(path);
    if (name.size() > 4000) return false;
    const size_t rgbaStride = static_cast<size_t>(input.width)*4U;
    const size_t rgbStride = static_cast<size_t>(input.width)*3U;
    if (rgbaStride > std::numeric_limits<size_t>::max() /
         static_cast<size_t>(input.bandRows)) return false;

    // One horizontal band (max 256 rows) plus one JPEG scanline. Construct all
    // C++ objects before setjmp; no exceptions may cross libjpeg's C boundary.
    std::vector<uint8_t> band;
    std::vector<uint8_t> rgbRow;
    try {
        band.resize(rgbaStride*static_cast<size_t>(input.bandRows));
        rgbRow.resize(rgbStride);
    } catch (...) { return false; }

    std::string scratch = name + ".iris26972c.stream.XXXXXX";
    std::vector<char> temp(scratch.begin(),scratch.end());
    temp.push_back('\0');
    const int fd=mkstemp(temp.data());
    if(fd<0) return false;
    FILE* file=fdopen(fd,"wb");
    if(!file) { close(fd); unlink(temp.data()); return false; }
    jpeg_compress_struct jpeg{};
    JpegFailure failure{};
    jpeg.err=jpeg_std_error(&failure.base);
    failure.base.error_exit=OnJpegError;
    volatile bool created=false, ok=false;
    if(setjmp(failure.point)==0) {
        jpeg_create_compress(&jpeg);
        created=true;
        jpeg_stdio_dest(&jpeg,file);
        jpeg.image_width=static_cast<JDIMENSION>(input.width);
        jpeg.image_height=static_cast<JDIMENSION>(input.height);
        jpeg.input_components=3;
        jpeg.in_color_space=JCS_RGB;
        jpeg_set_defaults(&jpeg);
        jpeg_set_quality(&jpeg,95,TRUE);
        jpeg.optimize_coding=TRUE;
        for(int c=0;c<jpeg.num_components;c++) {
            jpeg.comp_info[c].h_samp_factor=1;
            jpeg.comp_info[c].v_samp_factor=1;
        }
        jpeg_start_compress(&jpeg,TRUE);
        if(input.icc)
            jpeg_write_icc_profile(&jpeg,input.icc,static_cast<unsigned int>(input.iccSize));
        ok=true;
        for(int top=0;top<input.height && ok;top+=input.bandRows) {
            const int rows=std::min(input.bandRows,input.height-top);
            if(!input.reader(top,rows,band.data(),static_cast<int>(rgbaStride),
                             input.context)) { ok=false; break; }
            for(int y=0;y<rows && ok;y++) {
                const uint8_t* rgba=band.data()+static_cast<size_t>(y)*rgbaStride;
                for(int x=0;x<input.width;x++) {
                    const size_t src=static_cast<size_t>(x)*4U;
                    const size_t dst=static_cast<size_t>(x)*3U;
                    rgbRow[dst]=rgba[src];
                    rgbRow[dst+1]=rgba[src+1];
                    rgbRow[dst+2]=rgba[src+2];
                }
                JSAMPROW scan=rgbRow.data();
                if(jpeg_write_scanlines(&jpeg,&scan,1)!=1) ok=false;
            }
        }
        if(ok) jpeg_finish_compress(&jpeg);
    }
    if(created) jpeg_destroy_compress(&jpeg);
    if(ok && fflush(file)!=0) ok=false;
    if(ok && fsync(fd)!=0) ok=false;
    if(fclose(file)!=0) ok=false;
    if(ok && link(temp.data(),path)!=0) ok=false;
    unlink(temp.data());
    return ok;
}

}  // namespace iris26972c
