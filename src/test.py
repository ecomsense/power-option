from symbols import Symbols
from pprint import pprint
from utils import dict_from_yml
from api import Helper
from wsocket import Wsocket

# base symbol changed
kwargs = dict_from_yml("name", "BANKNIFTY")
s = Symbols(**kwargs)


filtered = s.new_chain(59251, full_chain=True)
pprint(filtered)
filtered = [item["instrument_token"] for item in filtered]
api = Helper.api()

wst = Wsocket(api, filtered)
ticks = {}
while not any(ticks):
    ticks = wst.ltp()
    __import__("time").sleep(5)
else:
    pprint(ticks)
