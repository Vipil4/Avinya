import pytest

from app.storage.store import ConflictError, StudentStore, default_profile


@pytest.fixture
def store(tmp_path):
    return StudentStore(data_dir=tmp_path)


def test_load_missing_profile_returns_default(store):
    profile = store.load("newstudent")
    assert profile["name"] == ""
    assert profile["_version"] == 0


def test_save_then_load_round_trips(store):
    profile = default_profile()
    profile["name"] = "Priya Sharma"
    saved = store.save("s1", profile, expected_version=0)
    assert saved["_version"] == 1

    loaded = store.load("s1")
    assert loaded["name"] == "Priya Sharma"
    assert loaded["_version"] == 1


def test_corrupted_json_on_disk_falls_back_to_default_instead_of_raising(store, tmp_path):
    (tmp_path / "s2.json").write_text("{not valid json!!", encoding="utf-8")
    profile = store.load("s2")  # must not raise
    assert profile["name"] == ""


def test_conflicting_save_raises_instead_of_silently_overwriting(store):
    # Simulates two tabs: both load version 0, both try to save.
    profile = default_profile()
    profile["notes"] = {"BMC-505E": "Tab A's notes"}
    store.save("s3", profile, expected_version=0)  # tab A saves -> version 1

    profile_b = default_profile()
    profile_b["notes"] = {"BMC-505E": "Tab B's notes"}
    with pytest.raises(ConflictError):
        store.save("s3", profile_b, expected_version=0)  # tab B still thinks version is 0

    # Tab A's data must still be intact.
    on_disk = store.load("s3")
    assert on_disk["notes"]["BMC-505E"] == "Tab A's notes"


def test_rejects_unsafe_student_id(store):
    with pytest.raises(ValueError):
        store.load("../../etc/passwd")
