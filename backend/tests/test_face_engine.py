import numpy as np
import pytest
from app.face_engine import FaceStore

def test_enrollment_duplicate_and_delete(tmp_path):
    store=FaceStore(tmp_path)
    face=np.full((160,160),120,dtype=np.uint8)
    store.enroll(10,face)
    assert store.enrolled_ids()==[10]
    with pytest.raises(ValueError,match="already enrolled"):
        store.enroll(10,face)
    store.delete(10)
    assert store.enrolled_ids()==[]

def test_persisted_template(tmp_path):
    store=FaceStore(tmp_path)
    store.enroll(12,np.full((160,160),100,dtype=np.uint8))
    assert FaceStore(tmp_path).enrolled_ids()==[12]
