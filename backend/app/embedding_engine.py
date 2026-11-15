"""OpenCV YuNet + SFace: one-reference-photo embedding engine.

Requires two ONNX models installed by scripts/download_face_models.py.
No automatic identity updates or gate actions.
"""
import os
from pathlib import Path
import cv2
import numpy as np

MODEL_DIR=Path(os.environ.get("SMART_GATE_MODEL_DIR",Path(__file__).resolve().parents[1]/"models"))
DETECTOR=MODEL_DIR/"face_detection_yunet_2023mar.onnx"
RECOGNIZER=MODEL_DIR/"face_recognition_sface_2021dec.onnx"
# A conservative *starting* threshold, not validated for a real population.
COSINE_THRESHOLD=float(os.environ.get("SMART_GATE_SFACE_THRESHOLD","0.45"))

class EmbeddingEngine:
    def __init__(self,root):
        if not DETECTOR.is_file() or not RECOGNIZER.is_file():
            raise FileNotFoundError("SFace models missing; run python scripts/download_face_models.py")
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.detector=cv2.FaceDetectorYN.create(str(DETECTOR),"",(320,320),score_threshold=0.8,nms_threshold=0.3,top_k=100)
        self.recognizer=cv2.FaceRecognizerSF.create(str(RECOGNIZER),"")
        self.features={}
        self.reload()
    def reload(self):
        self.features={}
        for path in self.root.glob("*.sface.npy"):
            try:
                arr=np.load(path,allow_pickle=False)
                if arr.shape==(128,) and arr.dtype==np.float32 and np.isfinite(arr).all():
                    self.features[int(path.name.split(".")[0])]=arr
            except (ValueError,OSError):
                continue
    def detect(self,image):
        h,w=image.shape[:2]
        self.detector.setInputSize((w,h))
        _,faces=self.detector.detect(image)
        return [] if faces is None else [face for face in faces if face[2]>=55 and face[3]>=55]
    def encode(self,image,face):
        aligned=self.recognizer.alignCrop(image,face)
        feature=self.recognizer.feature(aligned).flatten().astype(np.float32)
        norm=np.linalg.norm(feature)
        if not np.isfinite(norm) or norm<=1e-8:
            raise ValueError("Invalid face embedding")
        return feature/norm
    def enroll(self,pid,image):
        if pid in self.features:
            raise ValueError("Person already has a reference; remove it before replacement")
        faces=self.detect(image)
        if len(faces)!=1:
            raise ValueError("Reference photo must contain exactly one clearly detected face")
        feature=self.encode(image,faces[0])
        for other_id,other in self.features.items():
            if float(np.dot(feature,other))>=0.65:
                raise ValueError("Reference resembles another identity; manual review required")
        path=self.root/f"{pid}.sface.npy"
        temp=self.root/f"{pid}.sface.tmp"
        try:
            with temp.open("wb") as handle:
                np.save(handle,feature,allow_pickle=False)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
        self.features[pid]=feature
    def delete(self,pid):
        self.features.pop(pid,None)
        (self.root/f"{pid}.sface.npy").unlink(missing_ok=True)
    def enrolled_ids(self):
        return sorted(self.features)
    def sample_counts(self):
        return {pid:1 for pid in self.features}
    def recognize(self,image):
        results=[]
        for face in self.detect(image)[:12]:
            feature=self.encode(image,face)
            ranked=sorted(((float(np.dot(feature,ref)),pid) for pid,ref in self.features.items()),reverse=True)
            score,pid=ranked[0] if ranked else (None,None)
            second=ranked[1][0] if len(ranked)>1 else -1
            recognized=score is not None and score>=COSINE_THRESHOLD and score-second>=0.06
            x,y,w,h=map(int,face[:4])
            results.append({"box":[x,y,w,h],"person_id":pid if recognized else None,
                            "recognized":bool(recognized),"confidence":round(score,3) if score is not None else None})
        return results
