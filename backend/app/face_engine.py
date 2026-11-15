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
PROFILE=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_profileface.xml")
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
    """Detect frontal and left/right profiles; suppress overlapping boxes."""
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    found=[]
    def add(x,y,w,h):
        box=(int(x),int(y),int(w),int(h))
        for ax,ay,aw,ah in found:
            ix=max(0,min(x+w,ax+aw)-max(x,ax))
            iy=max(0,min(y+h,ay+ah)-max(y,ay))
            if ix*iy>0.35*min(w*h,aw*ah):
                return
        found.append(box)
    for x,y,w,h in DETECTION.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(70,70)):
        add(x,y,w,h)
    if not PROFILE.empty():
        for flipped in (False,True):
            scan=cv2.flip(gray,1) if flipped else gray
            for x,y,w,h in PROFILE.detectMultiScale(scan,scaleFactor=1.1,minNeighbors=4,minSize=(70,70)):
                add(gray.shape[1]-x-w if flipped else x,y,w,h)
    result=[]
    for x,y,w,h in found[:12]:
        crop=gray[y:y+h,x:x+w]
        if crop.size:
            result.append(((x,y,w,h),cv2.resize(cv2.equalizeHist(crop),SIZE)))
    return result

class FaceStore:
    """Multiple consented pose samples per identity, legacy .npy compatible."""
    MAX_SAMPLES=5
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self._faces={}
        self._recognizer=None
        self._load()
    def _load(self):
        for path in self.root.glob("*.npy"):
            try:
                pid=int(path.stem)
                arr=np.load(path,allow_pickle=False)
                if arr.shape==(160,160) and arr.dtype==np.uint8:
                    self._faces[pid]=[arr]
                elif arr.ndim==3 and arr.shape[1:]==SIZE and arr.dtype==np.uint8 and 1<=len(arr)<=self.MAX_SAMPLES:
                    self._faces[pid]=list(arr)
            except (ValueError,OSError):
                continue
    def _invalidate(self):
        self._recognizer=None
    def enroll(self,pid,face):
        self.enroll_many(pid,[face])
    def enroll_many(self,pid,faces):
        with LOCK:
            if pid in self._faces:
                raise ValueError("Person already enrolled; delete enrollment before replacement")
            if not 1<=len(faces)<=self.MAX_SAMPLES:
                raise ValueError("Provide between 1 and 5 face samples")
            for face in faces:
                if not isinstance(face,np.ndarray) or face.shape!=SIZE or face.dtype!=np.uint8:
                    raise ValueError("Invalid face sample")
                match=self.match(face)
                if match["confidence"] is not None and match["confidence"]<65:
                    raise ValueError("Face resembles an existing enrollment; manual review required")
            path=self.root/f"{pid}.npy"
            temp=self.root/f"{pid}.tmp"
            try:
                with temp.open("wb") as file:
                    np.save(file,np.stack(faces),allow_pickle=False)
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
            self._faces[pid]=list(faces)
            self._invalidate()
    def delete(self,pid):
        with LOCK:
            self._faces.pop(pid,None)
            (self.root/f"{pid}.npy").unlink(missing_ok=True)
            self._invalidate()
    def enrolled_ids(self):
        with LOCK:return sorted(self._faces)
    def sample_counts(self):
        with LOCK:return {pid:len(samples) for pid,samples in self._faces.items()}
    def match(self,face):
        with LOCK:
            if not self._faces:
                return {"person_id":None,"confidence":None,"recognized":False}
            if not hasattr(cv2,"face"):
                raise RuntimeError("opencv-contrib-python is required")
            if self._recognizer is None:
                recognizer=cv2.face.LBPHFaceRecognizer_create()
                samples=[sample for pid in self._faces for sample in self._faces[pid]]
                ids=[pid for pid in self._faces for _ in self._faces[pid]]
                recognizer.train(samples,np.array(ids,dtype=np.int32))
                self._recognizer=recognizer
            pid,distance=self._recognizer.predict(face)
            # Provisional distance threshold; never sufficient for automatic entry.
            recognized=distance<55
            return {"person_id":int(pid) if recognized else None,
                    "confidence":round(float(distance),2),"recognized":bool(recognized)}
