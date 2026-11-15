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

def test_multi_pose_enrollment_and_reload(tmp_path):
    store=FaceStore(tmp_path)
    base=np.tile(np.arange(160,dtype=np.uint8),(160,1))
    store.enroll_many(21,[base,np.fliplr(base).copy(),np.rot90(base).copy()])
    assert store.sample_counts()=={21:3}
    restored=FaceStore(tmp_path)
    assert restored.sample_counts()=={21:3}
    assert restored.match(base)["person_id"]==21
    restored.delete(21)
    assert restored.sample_counts()=={}

def test_invalid_multi_pose_is_atomic(tmp_path):
    store=FaceStore(tmp_path)
    valid=np.full((160,160),120,dtype=np.uint8)
    with pytest.raises(ValueError,match="Invalid face sample"):
        store.enroll_many(30,[valid,np.zeros((10,10),dtype=np.uint8)])
    assert store.enrolled_ids()==[]
    assert not list(tmp_path.glob("*.npy"))
