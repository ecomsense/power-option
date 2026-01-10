from traceback import print_exc

from constants import O_CNFG, O_FUTL, S_DATA


def get_bypass():
    from stock_brokers.bypass.bypass import Bypass

    try:
        print("O_CNFG", O_CNFG)
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
        bypass = Bypass(dct["userid"], dct["password"], dct["totp"], tokpath, enctoken)
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
        get_bypass()
        print_exc()
    else:
        return bypass


def get_zerodha():
    try:
        from stock_brokers.zerodha.zerodha import Zerodha

        dct = O_CNFG["zerodha"]
        tokpath = S_DATA + dct["userid"] + ".txt"
        zera = Zerodha(
            user_id=dct["userid"],
            password=dct["password"],
            totp=dct["totp"],
            api_key=dct["api_key"],
            secret=dct["secret"],
            tokpath=tokpath,
        )
        if not zera.authenticate():
            raise Exception("unable to authenticate")

    except Exception as e:
        print(f"exception while creating zerodha object {e}")
        remove_token(tokpath)
        get_zerodha()
    else:
        return zera


def remove_token(tokpath):
    __import__("os").remove(tokpath)


def login():
    if O_CNFG["broker"] == "bypass":
        return get_bypass()
    else:
        return get_zerodha()


class Helper:
    api_object = None

    @classmethod
    def api(cls):
        if cls.api_object is None:
            cls.api_object = login()
        return cls.api_object
