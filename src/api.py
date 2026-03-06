from traceback import print_exc

import pendulum as pdlm
from constants import O_CNFG, O_FUTL, S_DATA


def get_bypass():
    from stock_brokers.bypass.bypass import Bypass

    try:
        if isinstance(O_CNFG, dict):
            dct = O_CNFG["bypass"]

            tokpath = S_DATA + dct["userid"] + ".txt"
            enctoken = None
            if not O_FUTL.is_file_not_2day(tokpath):
                print(f"{tokpath} modified today ... reading {enctoken}")
                with open(tokpath, "r") as tf:
                    enctoken = tf.read()
                    if len(enctoken) < 5:
                        enctoken = None
            print(f"enctoken to broker {enctoken}")
            bypass = Bypass(
                dct["userid"], dct["password"], dct["totp"], tokpath, enctoken
            )
            if bypass.authenticate():
                if not enctoken:
                    enctoken = bypass.kite.enctoken
                    with open(tokpath, "w") as tw:
                        tw.write(enctoken)
            else:
                raise Exception("unable to authenticate")
    except Exception as e:
        print(f"unable to create bypass object {e}")
        remove_token(tokpath)
        # get_bypass()
        print_exc()
    else:
        return bypass


def get_zerodha():
    try:
        from stock_brokers.zerodha.zerodha import Zerodha

        zera = None
        if isinstance(O_CNFG, dict):
            dct = O_CNFG["zerodha"]
            # tokpath = S_DATA + dct["userid"] + ".txt"
            zera = Zerodha(
                userid=dct["userid"],
                password=dct["password"],
                totp=dct["totp"],
                api_key=dct["api_key"],
                secret=dct["secret"],
            )
            if not zera.authenticate():
                raise Exception("unable to authenticate")

    except Exception as e:
        print(f"exception while creating zerodha object {e}")
        # remove_token(tokpath)
        get_zerodha()
    else:
        return zera


def remove_token(tokpath):
    __import__("os").remove(tokpath)


def login():
    if isinstance(O_CNFG, dict):
        if O_CNFG["broker"] == "bypass":
            return get_bypass()
        else:
            return get_zerodha()
    else:
        print("please configure the settings properly")


class Helper:
    api_object = None
    baseline = {}

    @classmethod
    def api(cls):
        if cls.api_object is None:
            cls.api_object = login()
        return cls.api_object

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
            if isinstance(lst, list) and len(lst) > 0:
                if close:= lst[-1].get("close"):
                    cls.baseline[instrument_token] = close
                return cls.baseline[instrument_token]
            return 0
        except Exception as e:
            print(f"{e} exception while getting history")

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
        from_date=pdlm.now("Asia/Kolkata").subtract(days=6).to_date_string(),
        to_date=pdlm.now("Asia/Kolkata").to_date_string(),
        interval="day",
    )
    lst = broker_object.historical(kwargs)
    pprint(lst)
    print(f'verify that {yesterday_close=} and recent historical close {lst[-1]["close"]} are same')
