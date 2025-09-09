from backend.utils.metrics import Counter, Gauge, Histogram, generate_latest


def test_generate_latest_contains_counter_value():
    c = Counter("test_counter", "a test counter", ("label",))
    c.labels("value").inc()
    output = generate_latest().decode()
    assert "test_counter{label=\"value\"} 1" in output


def test_gauge_operations():
    g = Gauge("test_gauge", "a test gauge", ("label",))
    gauge_label = g.labels("value")
    gauge_label.inc(2)
    gauge_label.dec(1)
    gauge_label.set(5)
    output = generate_latest().decode()
    assert "test_gauge{label=\"value\"} 5" in output


def test_histogram_observe():
    h = Histogram("test_histogram", "a test histogram", [0.1, 1.0, 5.0], ("label",))
    h.labels("value").observe(0.5)
    output = generate_latest().decode()
    assert "test_histogram_bucket{label=\"value\",le=\"1.0\"} 1" in output
    assert "test_histogram_count{label=\"value\"} 1" in output
    assert "test_histogram_sum{label=\"value\"} 0.5" in output


def test_generate_latest_has_trailing_newline():
    c = Counter("newline_counter", "newline test")
    c.labels().inc()
    assert generate_latest().endswith(b"\n")
