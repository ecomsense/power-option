from traceback import print_exc
from constants import D_SYMBOL, logging


def dict_from_yml(key_to_search, value_to_match):
    try:
        dct = {}
        sym_from_yml = D_SYMBOL
        for _, dct in sym_from_yml.items():
            if isinstance(dct, dict) and dct[key_to_search] == value_to_match:
                return dct
        logging.debug(f"{dct=}")
        return dct
    except Exception as e:
        logging.error(f"dict from yml error: {e}")
        print_exc()
