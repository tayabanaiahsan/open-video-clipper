from clipper.core import choose_clips


def test_short_video():
    assert choose_clips(12, [], 30, 3) == [(0.0, 12)]


def test_non_overlapping():
    clips = choose_clips(120, [5, 10, 45, 50, 90], 20, 3)
    assert len(clips) == 3
    assert all(b[0] - a[0] >= 16 for a, b in zip(clips, clips[1:]))


def test_invalid_inputs():
    import pytest
    with pytest.raises(ValueError):
        choose_clips(0, [], 20, 2)
