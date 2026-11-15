"""Local, opt-in face recognition prototype.

LBPH is a baseline, NOT suitable for high-stakes access decisions. Never opens gates.
Only a single face per enrollment capture; duplicate identities are rejected by
nearest-neighbor score. The threshold is provisional and needs calibration.
"""
import base64
import io
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

SIZE=(160,160)
MAX_IMAGE_BYTES=2_000_000
DETECTION=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
LOCK=threading.RLock()

def decode_image(data):
    if not isinstance(data,str) or not data.startswith("data:image/jpeg;base64,"):
        raise ValueError("JPEG data URL required")
    encoded=data.split(",",1)[1]
    if len(encoded)>MAX_IMAGE_BYTES*2:
        raise ValueError("Image too large")
    try:
        raw=base64.b64decode(encoded,validate=True)
        if len(raw)>MAX_IMAGE_BYTES:
            raise ValueError("Image too large")
        image=Image.open(io.BytesIO(raw))
        if image.width*image.height>8_000_000:
            raise ValueError("Image dimensions too large")
        image=image.convert("RGB")
        return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
    except (OSError,ValueError) as exc:
        raise ValueError("Invalid image") from exc

def extract_faces(frame):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    boxes=DETECTION.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(70,70))
    result=[]
    for x,y,w,h in boxes:
        crop=gray[y:y+h,x:x+w]
        result.append(((int(x),int(y),int(w),int(h)),cv2.resize(cv2.equalizeHist(crop),SIZE)))
    return result

class FaceStore:
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self._faces={}
        self._load()
    def _load(self):
        for path in self.root.glob("*.npy"):
            try:
                pid=int(path.stem)
                arr=np.load(path,allow_pickle=False)
                if arr.shape==(160,160) and arr.dtype==np.uint8:
                    self._faces[pid]=arr
            except (ValueError,OSError):
                continue
    def enroll(self,pid,face):
        with LOCK:
            if pid in self._faces:
                raise ValueError("Person already enrolled; delete enrollment before replacement")
            match=self.match(face)
            if match["person_id"] is not None and match["confidence"]<65:
                raise ValueError("Face resembles an existing enrollment; manual review required")
            path=self.root/f"{pid}.npy"
            with path.open("wb") as file:
                np.save(file,face,allow_pickle=False)
            self._faces[pid]=face
    def delete(self,pid):
        with LOCK:
            self._faces.pop(pid,None)
            (self.root/f"{pid}.npy").unlink(missing_ok=True)
    def enrolled_ids(self):
        with LOCK:return sorted(self._faces)
    def match(self,face):
        with LOCK:
            if not self._faces:
                return {"person_id":None,"confidence":None,"recognized":False}
            if not hasattr(cv2,"face"):
                raise RuntimeError("opencv-contrib-python is required")
            recognizer=cv2.face.LBPHFaceRecognizer_create()
            ids=list(self._faces)
            recognizer.train([self._faces[pid] for pid in ids],np.array(ids,dtype=np.int32))
            pid,distance=recognizer.predict(face)
            # Conservative provisional threshold, MUST calibrate using real test data.
            recognized=distance<55
            return {"person_id":int(pid) if recognized else None,
                    "confidence":round(float(distance),2),"recognized":bool(recognized)}
