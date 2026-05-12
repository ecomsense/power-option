import os
import pendulum as pdlm

from stock_brokers.zerodha.zerodha import Zerodha
from constants import logging
from kiteconnect import KiteTicker
from constants import S_DATA, yml_to_obj


def login():
    try:
        tokpath = S_DATA + "token.txt"
        O_CNFG = yml_to_obj()

        zera = None
        if isinstance(O_CNFG, dict) and "zerodha" in O_CNFG:
            dct = O_CNFG["zerodha"]
            zera = Zerodha(
                userid=dct["userid"],
                password=dct["password"],
                totp=dct["totp"],
                api_key=dct["api_key"],
                secret=dct["secret"],
            )
            try:
                if not zera.authenticate():
                    raise Exception("unable to authenticate")
                else:
                    zera.kws = KiteTicker(zera.api_key, zera.enctoken)
                    logging.info(f"Zerodha authentication successful, token: {zera.enctoken[:20]}...")
            except SystemExit:
                logging.warning("Zerodha authentication failed - will retry later")
                return None
        else:
            logging.error("Zerodha credentials not found in settings.yml")
            return None

    except SystemExit:
        logging.warning("Zerodha authentication failed - will retry later")
        return None
    except Exception as e:
        logging.error(f"exception while creating zerodha object {e}")
        try:
            remove_token(tokpath)
            login()
        except SystemExit:
            logging.warning("Zerodha authentication failed - will retry later")
            return None
    else:
        return zera


def remove_token(tokpath):
    __import__("os").remove(tokpath)


def is_broker_authenticated():
    """Check if broker is authenticated and available."""
    try:
        return Helper.api() is not None
    except:
        return False


class Helper:
    api_object = None
    baseline = {}

    @classmethod
    def api(cls):
        if cls.api_object is None:
            cls.api_object = login()
        return cls.api_object

    @classmethod
    def reset(cls):
        cls.api_object = None
        cls.baseline = {}
        tokpath = S_DATA + "token.txt"
        if os.path.exists(tokpath):
            try:
                os.remove(tokpath)
                logging.info("Token file deleted - forcing new login")
            except Exception as e:
                logging.error(f"Error deleting token: {e}")
        logging.info("Helper session reset complete - new token will be generated on next login")

    @classmethod
    def _get_history(cls, instrument_token):
        try:
            broker_object = cls.api()
            kwargs = dict(
                instrument_token=instrument_token,
                from_date=pdlm.now("Asia/Kolkata").subtract(days=6).to_date_string(),
                to_date=pdlm.now("Asia/Kolkata").to_date_string(),
                interval="day",
            )
            lst = broker_object.historical(kwargs)
            if isinstance(lst, list) and len(lst) > 1:
                if close := lst[-2].get("close"):
                    cls.baseline[instrument_token] = close
                return cls.baseline[instrument_token]
            return 0
        except Exception as e:
            logging.error(f"{e} exception while getting history")

    @classmethod
    def history(cls, instrument_token):
        return cls.baseline.get(instrument_token, cls._get_history(instrument_token))


if __name__ == "__main__":
    from pprint import pprint

    instrument_token = 256265
    yesterday_close = Helper._get_history(instrument_token)

    broker_object = Helper.api()
    kwargs = dict(
        instrument_token=instrument_token,
        from_date=pdlm.now("Asia/Kolkata").subtract(days=7).to_date_string(),
        to_date=pdlm.now("Asia/Kolkata").to_date_string(),
        interval="day",
    )
    lst = broker_object.historical(kwargs)
    pprint(lst)
    print(
        f"verify that {yesterday_close=} and recent historical close {lst[-2]['close']} are same"
    )
