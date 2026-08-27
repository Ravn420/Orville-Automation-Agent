from signal_room_launcher import SingleInstanceLock


def test_single_instance_lock_blocks_duplicate_and_releases(tmp_path):
    path = tmp_path / "orville.lock"
    first = SingleInstanceLock(path)
    second = SingleInstanceLock(path)
    assert first.acquire() is True
    try:
        assert second.acquire() is False
    finally:
        first.release()
    try:
        assert second.acquire() is True
    finally:
        second.release()
