"""Download the real OpenCV Zoo ONNX weights (not Git LFS pointer files)."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import shutil

root=Path(__file__).resolve().parents[1]/"models"
root.mkdir(parents=True,exist_ok=True)
names={
    "face_detection_yunet_2023mar.onnx":"face_detection_yunet",
    "face_recognition_sface_2021dec.onnx":"face_recognition_sface",
}
base="https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models"

def valid_model(path):
    if not path.is_file() or path.stat().st_size<100_000:
        return False
    with path.open("rb") as handle:
        return not handle.read(64).startswith(b"version https://git-lfs.github.com/spec/v1")

for filename,folder in names.items():
    target=root/filename
    if valid_model(target):
        print("Exists:",target,"(",target.stat().st_size,"bytes)")
        continue
    url=f"{base}/{folder}/{filename}"
    print("Downloading actual model:",filename)
    tmp=target.with_suffix(".download")
    try:
        request=Request(url,headers={"User-Agent":"UniversitySmartGate-ModelDownloader/1.0"})
        with urlopen(request,timeout=120) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response,out)
        if not valid_model(tmp):
            raise RuntimeError(f"Invalid ONNX model or Git LFS pointer received: {filename} ({tmp.stat().st_size} bytes)")
        tmp.replace(target)
    except (URLError,OSError) as exc:
        raise RuntimeError(f"Failed to download {filename}: {exc}") from exc
    finally:
        tmp.unlink(missing_ok=True)
    print("Ready:",target,"(",target.stat().st_size,"bytes)")
print("Models downloaded. Restart backend and confirm recognition engine is sface.")
