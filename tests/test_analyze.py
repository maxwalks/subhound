import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from analyze import decode_manchester, detect_rolling_code, compute_signal_quality, SubFile, extract_features


def test_manchester_ge_thomas_convention():
    # G.E.Thomas: 1=10, 0=01
    raw = [1,0, 0,1, 1,0, 0,1]  # encodes 1,0,1,0
    bits, convention, error_rate = decode_manchester(raw)
    assert bits == [1, 0, 1, 0]
    assert "Thomas" in convention
    assert error_rate == 0.0

def test_manchester_ieee_convention():
    # IEEE 802.3: 1=01, 0=10
    raw = [0,1, 1,0, 0,1, 1,0]  # encodes 1,0,1,0
    bits, convention, error_rate = decode_manchester(raw)
    assert bits == [1, 0, 1, 0]
    assert "IEEE" in convention
    assert error_rate == 0.0

def test_manchester_with_errors():
    raw = [1,0, 0,0, 1,0]  # middle pair 0,0 is invalid
    bits, convention, error_rate = decode_manchester(raw)
    assert len(bits) == 2   # only valid pairs decoded
    assert error_rate > 0.0

def test_manchester_empty():
    bits, convention, error_rate = decode_manchester([])
    assert bits == []
    assert error_rate == 0.0

def test_manchester_tiebreak_all_errors():
    # All-invalid pairs: both conventions have equal error rate; tiebreak by first pair
    raw = [0, 0, 1, 1]  # both pairs invalid under both conventions
    bits, convention, error_rate = decode_manchester(raw)
    assert error_rate == 1.0
    assert bits == []
    # first pair is (0,0): not 1,0 so tiebreak falls through to IEEE
    assert "IEEE" in convention


def test_rolling_code_detected():
    # Segments differ in last 4 bits (rolling counter)
    seg0 = [1,0,1,1,0,0,1,0,  1,0,0,1,0,1,0,0]
    seg1 = [1,0,1,1,0,0,1,0,  1,0,0,1,0,1,0,1]
    seg2 = [1,0,1,1,0,0,1,0,  1,0,0,1,0,1,1,0]
    result = detect_rolling_code([seg0, seg1, seg2])
    assert result["is_rolling"] is True
    assert result["is_fixed"] is False
    assert 15 in result["diff_positions"]

def test_fixed_code_detected():
    seg = [1,0,1,1,0,0,1,0,1,0,0,1,0,1,0,0]
    result = detect_rolling_code([seg, seg, seg])
    assert result["is_fixed"] is True
    assert result["is_rolling"] is False
    assert result["diff_positions"] == []

def test_rolling_code_single_segment():
    seg = [1,0,1,1,0,0]
    result = detect_rolling_code([seg])
    assert result["is_rolling"] is False
    assert result["is_fixed"] is False

def test_rolling_code_empty_list():
    result = detect_rolling_code([])
    assert result["is_rolling"] is False
    assert result["is_fixed"] is False

def test_rolling_code_truncation_flag():
    # Segments of different lengths — truncated should be True
    seg0 = [1, 0, 1, 0, 1, 0]
    seg1 = [1, 0, 1, 0]
    result = detect_rolling_code([seg0, seg1])
    assert result["truncated"] is True


def _make_sub(segs, freq=433_920_000, te=174):
    return SubFile(path="test", frequency=freq, te_us=te,
                   total_bit_header=0, segments=segs, lat=0.0, lon=0.0, preset="")

def test_signal_quality_range():
    sub = _make_sub([[0]*100])
    fv = extract_features(sub)
    assert 0.0 <= fv.signal_quality <= 1.0

def test_signal_quality_high_for_clean_pwm():
    dense = [1,0,1,1,0,1,0,1,0,0,1,0,1,1,0,0] * 10
    sub_dense = _make_sub([dense])
    fv_dense = extract_features(sub_dense)
    sub_zero = _make_sub([[0]*160])
    fv_zero = extract_features(sub_zero)
    assert fv_dense.signal_quality > fv_zero.signal_quality
    assert fv_dense.signal_quality >= 0.5
