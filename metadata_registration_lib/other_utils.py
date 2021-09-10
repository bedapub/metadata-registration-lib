from decimal import Decimal


def str_to_bool(s):
    return s.lower() in ["true", "1", "y", "yes", "on", "t"]


def fix_float_issue(f):
    """
    Trick to round floating points of style 0.009600000000000001 or 0.5599999999999999
    """
    # f_str = str(f)
    # for char in ["0", "9"]:
    #     if char * 8 in f_str:
    #         index = f_str.find(char * 8)
    #         return round(f, index + 7)
    dec = Decimal(str(f)).quantize(Decimal("1.000000000000"))
    return float(dec)
