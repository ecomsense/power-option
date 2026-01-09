from traceback import print_exc


from constants import O_SETG, logging
from symbols import dump
from utils import dict_from_yml
from api import Helper


def root():
    try:
        logging.info("HAPPY TRADING")
        # download necessary masters
        dump()
        entry_time: str = O_SETG["program"]["start"]
        strategy_settings = O_SETG["strategy"]
        # Unpack settings into instance attributes
        symbol_settings = dict_from_yml("base", strategy_settings["base"])
        print(symbol_settings, entry_time)
        api = Helper.api()
    except Exception as e:
        print(f"root error: {e}")
        print_exc()


root()
