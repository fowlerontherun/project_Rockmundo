from backend.utils.metrics import Counter, generate_latest


def test_generate_latest_contains_counter_value():
    c = Counter("test_counter", "a test counter", ("label",))
    c.labels("value").inc()
    output = generate_latest().decode()
    assert "test_counter{label=\"value\"} 1" in output
