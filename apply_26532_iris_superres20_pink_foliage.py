#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, tempfile

PATCH_NAME = "26532_RUNTIME_DELTA_FROM_26531.patch"
PATCH_SHA256 = "2cbc59c31cb30c051f9afe17cded9c4752c29cb76a848ba6ef510e1be82b62f7"
BASE_HASHES = {'app/src/main/cpp/CMakeLists.txt': '7bbe3a5e10aae2bb489aaeb56240193c153f53c6f1d05c30bbadf10d42603c79', 'app/src/main/cpp/motionv2_jpeg444_jni.cpp': '97a29782f1813fd0abaf52b960ea1e6f5b3b80d9bae0f5dc29d4f4c511081998', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': 'c69a517b42ef1926641596193505ffcd871e60c4241dae18fee3fd9143784821', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt': '11828e54369dad88b91fb22f59b0759d2d3d9e1c38256f1b162fa84ee31ee25d', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt': 'db7c403d3b96c2af93afae75e7e42a85233f19dba6ae919870442172d6d35727', 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt': '989735bd8cfd257f899be4a0a3f7687b55d8433ea66ef558c693ba9bab17d14b', 'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt': '0aef9b21c1afcf5862330e76e979ac7d7a58a60f65d3f0c2d7e401583351bcde', 'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java': 'e7f0cea2770bc91de05bd85a244c6088019dab1b05bd67559b2680e3c1847933', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java': '30d0e217f3af592fa7650087c3fad4117fb5dc8ddafd11d93d66de54a8f0c0eb', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': '144183179a5bad4f34cd18741b4b59d4079188fc3bdf9e524e1c0e733f44fd0e', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java': 'f26dd769bf84450bfbd87a66bc28e6754845b25d267abf5a1118ad60d0cbdc10', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java': '6229210a2876c2c4576140dd8adf10ba1ffe061281ad52c6406652a56d28b864', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': 'debdd250110264741d7d5a68e68a9f4af7e73b16dbef1ebb2ab34e9a2e0de6db', 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java': 'be11291326f50950338f6c457f1ee701795ab418ccd5ce0877441d7187fab5b1', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java': '4671785a92b6cc19e2bd11f25b3be1c126390f77f6e9625c0e84037739d39d59', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java': '198aa12d7164bb4ee82d4caf01709c2c5659d0a3d29d65e7356c06d543a8f4e5', 'app/src/main/java/com/particlesdevs/photoncamera/settings/SettingType.java': '542919f841e2808cb8db35fb9463e551ef0d69e8e01a1d5364600e1b93183d4d', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java': '1659bd9b3c38bb2df581ba2c329487b9abe6bf8b2ca7531dcf43cd26ad1dc021', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java': 'a68769410d1702c0f232633ebbf7fec6bf308c9000e47feeb14e675561dbf899', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java': '8165f83efd301d3707ebcb5c46c17f9f36a46adcc16425db858a81514ccc20de', 'app/src/main/res/values/ids.xml': 'a9f4432784fe72bdc60daa087b2fee6f9804809f6dec3cf8b3cb3a4c637050ac', 'app/src/main/res/values/strings.xml': '98e30a216852efe16ee5bec95d604a53badfa889aa75d6d2ee2cd8c2b1928388'}
POST_HASHES = {'app/src/main/cpp/CMakeLists.txt': 'f7202b291acb92578dfe822edf45671f5ab0597cd07fcb6e22d5b820b9cf4163', 'app/src/main/cpp/motionv2_jpeg444_jni.cpp': 'a1b24cb8782cd7ce6b884ccf07f49ecb62b3488ddc7c1501c4695aab3467cf93', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': 'f58acc0c5449c1bdf9e95247b48b718c597c2c1de80b61bab27be392a6fde2ce', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt': 'b2a10d7f8168424e65c2286132307333d0066a23edd047f1e99a06e9fb341107', 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt': 'fba9f396fa20b81409342ffd35e5d3fdefaceefb08ebe22181c80be9a927c7be', 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt': '750827e00cc871fac6d7ec5261684c16f91c31e8dc2d7a75f31ebea41ec7b881', 'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt': '9a50d62e6974cdd2ce158db64f7320a0f60097b92a6f5318288bf3bba91d55ed', 'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java': '77be2074c000c47c247d68fa12f77260ca38214f199fd85f69f02a697fefd50a', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java': '218af5736c86c4eddf53e7c91716db1908200fe2d48f6fcc5eb0ae3127871e59', 'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java': 'b0acc38c65ba72b8b36520e585a987d274a3da2af9792fe8010c5d547b6a1e42', 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java': '49a8be8daf88caab5e6defd7ddf694d9875d0767d9c34e6c37457d798c53af55', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java': '242e05cb32a8c5e090d1ea4963e30f4c3089f0daba5ad8e2d962ea7fc57c4fa5', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java': 'c4402fa3ccc86a4bec44c1d03caabb92bd19a38e88ca20a094dc9c440e0a71e2', 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt': 'c0e8ab475c798833c8b165a09d23644216131ab27f3955f1905231bb848dce12', 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java': '48c9ecb75b8348e0c915c494e70a9a04f55ab41c7d433d336ce0889c276f91b3', 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java': '14e4dd6b62d06bc524268c5a3a5006cba62f22f6255b166a575991628b6a97cb', 'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java': '2e638ae2cc1e81da49872161d6b0177593bd80cb5f48d6d4967b5f6102582e41', 'app/src/main/java/com/particlesdevs/photoncamera/settings/SettingType.java': '97ee0c6f815d5b514c55e791fc866bcc22e95995a3400a3c98611634e4bc166a', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java': '69d20895396e9eb31fe8d1c862205b696a5abd997495571999d6f57f8bb827c1', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java': '0819e5848697ba0ee903f2348f0a476432f0339df1c926acaa4082daad2e7d0c', 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java': '33dfc39983d2c80af39be95d78498fc14aedb86e68150401915bfdc1e9e1d2d0', 'app/src/main/res/values/ids.xml': 'c646b13a1b495be072402bb5ce7f3071f34dd77b2f3f737d05babe73dbf4f1d9', 'app/src/main/res/values/strings.xml': '1b5107e230c60a19ca7cb00620bffef78290d5d6beddf4b7c61c9a9269644945'}
NEW_FILES = ['app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java']


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate_base(root: Path):
    version = root / "app/version.properties"
    text = version.read_text(encoding="utf-8")
    if "VERSION_NAME=0.9726531" not in text or "VERSION_BUILD=26531" not in text:
        raise RuntimeError("base version is not exact successful 26531")
    for rel, expected in BASE_HASHES.items():
        p = root / rel
        if not p.is_file(): raise RuntimeError(f"missing base {rel}")
        actual=sha(p)
        if actual != expected: raise RuntimeError(f"base hash mismatch {rel}: {actual}")
    for rel in NEW_FILES:
        if (root/rel).exists(): raise RuntimeError(f"new 26532 file already exists in base: {rel}")


def validate_post(root: Path):
    for rel, expected in POST_HASHES.items():
        p=root/rel
        if not p.is_file(): raise RuntimeError(f"missing post file {rel}")
        actual=sha(p)
        if actual != expected: raise RuntimeError(f"post hash mismatch {rel}: {actual}")


def apply(root: Path, patch_path: Path):
    validate_base(root)
    if sha(patch_path) != PATCH_SHA256:
        raise RuntimeError("certified 26532 patch SHA mismatch")
    subprocess.run(["patch","-d",str(root),"-p1","--batch","--forward","--fuzz=0"],
                   stdin=patch_path.open("rb"), check=True)
    validate_post(root)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", help="candidate source root containing app/")
    ap.add_argument("--self-test", action="store_true")
    args=ap.parse_args()
    here=Path(__file__).resolve().parent
    patch=here/PATCH_NAME
    if args.self_test:
        if not args.root: raise SystemExit("--self-test requires exact 26531 root")
        src=Path(args.root).resolve()
        with tempfile.TemporaryDirectory(prefix="iris26532-selftest-") as td:
            dst=Path(td)/"candidate"
            shutil.copytree(src,dst)
            apply(dst,patch)
            print("PASS: 26532 guarded patch self-test exact post hashes")
        return
    if not args.root: raise SystemExit("candidate root required")
    apply(Path(args.root).resolve(),patch)
    print("PASS: IRIS 26532 exact certified runtime patch applied")

if __name__ == "__main__": main()
