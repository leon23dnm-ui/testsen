from iski.prediction.buffer import RingBufferH


def test_buffer_h_eviction():
    buf = RingBufferH(cap=3)
    buf.push(0, "h0")
    buf.push(1, "h1")
    buf.push(2, "h2")
    buf.push(3, "h3")
    assert buf.get(0) is None
    assert buf.get(1) == "h1"
    assert buf.get(2) == "h2"
    assert buf.get(3) == "h3"
