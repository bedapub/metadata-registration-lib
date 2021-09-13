from math import floor, log10


def str_to_bool(s):
    return s.lower() in ["true", "1", "y", "yes", "on", "t"]


def fix_float_issue(x):
    """
    Round to 15 significant numbers
    See related tests for expected behaviour
    Trick to round floating points of style 0.009600000000000001 or 0.5599999999999999
    """
    # dec = Decimal(str(x)).quantize(Decimal("1.000000000000"))
    dec = round(x, 15 - int(floor(log10(abs(x)))) - 1)

    return dec
