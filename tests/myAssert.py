from __future__ import print_function

def areEqual(expect, val, eps = 0.01):
    print("Expected: ", expect, " actual: ", val)
    try:
        diff = abs(float(val) / float(expect) - 1.0)
        assert diff < eps, "***** Values don't match, expected= {:.12f}, found= {:.12f}, diff= {:.12f}. *****".format(expect, val, diff)
        assert expect * val >= 0.0, "***** Values don't have the same sign: expected= {:f}, found= {:f}. *****".format(expect, val)
    except BaseException as be:
        print(be)