from constants import logging
from pprint import pprint


class Wsocket:
    _ltp = {}

    def __init__(self, api, tokens):
        self._subscribe = None
        self._unsubscribe = None

        self.tokens = tokens
        self.kws = api.kite.kws()

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
            # Use a generator expression with a conditional check to avoid KeyErrors
            new_data = {
                tick["instrument_token"]: tick["depth"]["buy"][-1]["price"] 
                for tick in ticks 
                if "depth" in tick and tick["depth"]["buy"]
            }
            
            # Update your persistent cache
            if new_data:
                self._ltp = self._ltp | new_data
            else:
                pprint(ticks)
                
        except Exception as e:
            # Catching general exceptions prevents the thread from dying
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
