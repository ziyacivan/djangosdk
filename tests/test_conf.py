from django_ai_sdk.conf import AiSettings


def test_defaults():
    s = AiSettings()
    assert s.DEFAULT_PROVIDER == "fake"  # from test settings
    assert s.DEFAULT_MODEL == "fake-model"


def test_deep_merge():
    s = AiSettings()
    data = s._deep_merge(
        {"A": {"x": 1, "y": 2}, "B": 3},
        {"A": {"y": 99, "z": 0}},
    )
    assert data["A"]["x"] == 1
    assert data["A"]["y"] == 99
    assert data["A"]["z"] == 0
    assert data["B"] == 3
