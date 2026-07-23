from runner.ochiai import ochiai_score
from runner.tarantula import tarantula_score
import math

def test_ochiai_basic():
    # ef=1, ep=0, nf=0, np=1
    # total_f=1, total_p=1
    # ochiai = ef / sqrt(total_f * (ef + ep)) = 1 / sqrt(1 * 1) = 1.0
    assert ochiai_score(1, 0, 0, 1) == 1.0

def test_ochiai_partial():
    # ef=1, ep=1, nf=1, np=1
    # total_f=2, total_p=2
    # ochiai = 1 / sqrt(2 * 2) = 0.5
    assert math.isclose(ochiai_score(1, 1, 1, 1), 0.5)

def test_tarantula_basic():
    # ef=1, ep=0, nf=0, np=1
    # susp_f = 1/1 = 1.0
    # susp_p = 0/1 = 0.0
    # tarantula = 1.0 / (1.0 + 0.0) = 1.0
    assert tarantula_score(1, 0, 0, 1) == 1.0

def test_tarantula_partial():
    # ef=1, ep=1, nf=1, np=1
    # susp_f = 1/2 = 0.5
    # susp_p = 1/2 = 0.5
    # tarantula = 0.5 / (0.5 + 0.5) = 0.5
    assert math.isclose(tarantula_score(1, 1, 1, 1), 0.5)
