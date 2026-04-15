from constants import logging


class Wsocket:
    _ltp = {}

    def __init__(self, api, tokens):
        self._subscribe = None
        self._unsubscribe = None

        self.tokens = tokens
        # self.kws = api.kite.kws()
        self.kws = api.kws

        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error
        self.kws.on_reconnect = self.on_reconnect
        self.kws.on_noreconnect = self.on_noreconnect

        # Infinite loop on the main thread. Nothing after this will run.
        # You have to use the pre-defined callbacks to manage subscriptions.
        self.kws.connect(threaded=True)

    def ltp(self):
        return self._ltp

    def unsubscribe(self, tokens):
        self._unsubscribe = tokens

    def subscribe(self, tokens):
        self._subscribe = tokens

    def on_ticks(self, ws, ticks):
        try:
            # Log ALL incoming ticks to see what's coming
            logging.info(f"ALL TICKS: {ticks}")
            
            new_data = {}
            for tick in ticks:
                token = tick["instrument_token"]

                # 1. Try to get Market Depth Price (for Options)
                if "depth" in tick and tick["depth"]["buy"]:
                    new_data[token] = tick["depth"]["buy"][-1]["price"]

                # 2. Fallback to Last Traded Price (for Indices or non-full mode)
                elif "last_price" in tick:
                    new_data[token] = tick["last_price"]

            # Print received quotes for debugging
            if new_data:
                logging.info(f"TICKS RECEIVED: {new_data}")

            # Update persistent cache if we found any valid price data
            if new_data:
                self._ltp = self._ltp | new_data

        except Exception as e:
            print(f"Error processing ticks: {e}")

        # Handle subscription changes
        if self._unsubscribe:
            ws.unsubscribe(self._unsubscribe)
            self._unsubscribe = None
        elif self._subscribe:
            ws.subscribe(self._subscribe)
            ws.set_mode(ws.MODE_FULL, self._subscribe)
            self._subscribe = None

    def on_connect(self, ws, response):
        if response:
            print(f"on connect: {response}")

        ws.subscribe(self.tokens)
        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_FULL, self.tokens)

    def on_close(self, ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        ws.stop()
        logging.error(
            "Wsocket close: {code} - {reason}".format(code=code, reason=reason)
        )
        print("wsocket closed")

    def on_error(self, ws, code, reason):
        # Callback when connection closed with error.
        logging.error(
            "Connection error: {code} - {reason}".format(code=code, reason=reason)
        )
        print("error in websocket")

    def on_reconnect(self, ws, attempts_count):
        # Callback when reconnect is on progress
        logging.warning("Reconnecting: {}".format(attempts_count))

    # Callback when all reconnect failed (exhausted max retries)

    def on_noreconnect(self, ws):
        logging.error("Reconnect failed.")


if __name__ == "__main__":
    from api import Helper
    from constants import O_SETG
    from symbols import dump
    from utils import dict_from_yml

    dump()

    symbol_settings = dict_from_yml("name", O_SETG["base"])
    api = Helper.api()
    ws = Wsocket(api, [25625, 11000, 16])
    ticks = {}
    while not any(ticks):
        ticks = ws.ltp()
        __import__("time").sleep(5)
    else:
        print(ticks)
