"""Download pretrained OpenCV Zoo ONNX models for local SFace inference.

Review model license and provenance before deploying with real biometric data.
"""
from pathlib import Path
from urllib.request import urlopen
import shutil

root=Path(__file__).resolve().parents[1]/"models"
root.mkdir(parents=True,exist_ok=True)
base="https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/"
names={
    "face_detection_yunet_2023mar.onnx":"face_detection_yunet",
    "face_recognition_sface_2021dec.onnx":"face_recognition_sface",
}
for filename,folder in names.items():
    target=root/filename
    if target.exists() and target.stat().st_size>100_000:
        print("Exists:",target)
        continue
    url=f"{base}{folder}/{filename}"
    print("Downloading",filename)
    tmp=target.with_suffix(".download")
    try:
        with urlopen(url,timeout=45) as response, tmp.open("wb") as out:
            shutil.copyfileobj(response,out)
        if tmp.stat().st_size<100_000:
            raise RuntimeError("Downloaded file too small; check Git LFS pointer")
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    print("Ready:",target)
print("Restart backend after download; reference photos must be re-imported for SFace.")
