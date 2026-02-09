from traceback import print_exc
from typing import Any, Literal  # Use list[dict] for the return type

import pandas as pd
import pendulum as pdlm
from constants import D_SYMBOL, O_FUTL, S_DATA, logging

OptionType = Literal["CE", "PE"]


def get_symbols(exchange: str) -> list[dict[str, Any]]:
    """
    download csv from broker and return as list of dicts
    parameters:
        accepts exchange "NFO"
    returns:
        list of dictionaries containing symbol info
    """
    try:
        url = f"https://api.kite.trade/instruments/{exchange}"
        df = pd.read_csv(url)

        # 1. Select relevant columns
        cols = [
            "tradingsymbol",
            "instrument_token",
            "name",
            "strike",
            "instrument_type",
            "expiry",
            "lot_size",
        ]
        # Use .copy() to avoid SettingWithCopy warnings later
        df = df[cols].copy()

        # 2. Fix Types
        # Convert strike to numeric, then int (fills NaNs with 0 or drops them)
        df["strike"] = (
            pd.to_numeric(df["strike"], errors="coerce").fillna(0).astype(int)
        )
        df["instrument_token"] = (
            pd.to_numeric(df["instrument_token"], errors="coerce").fillna(0).astype(int)
        )

        # 3. Drop rows where essential data might be missing
        df = df.dropna(subset=["tradingsymbol", "name"])

        # Returns a list of dicts: [{"tradingsymbol": "NIFTY...", ...}, ...]
        return df.to_dict(orient="records")

    except Exception as e:
        print(f"Error fetching {exchange}: {e}")
        print_exc()
        return []  # Return empty list on failure to keep the type consistent


def dump(exchange: str) -> None:
    """get symbol info by exchange and write it to json in data dir

    Args:
        arg_name (type): Description.

    Returns:
        return_type: Description.
    """

    try:
        # what exchange and its symbols should be dumped
        exchange_file = S_DATA + exchange + ".json"
        if O_FUTL.is_file_not_2day(exchange_file):
            sym_from_json = get_symbols(exchange)
            O_FUTL.write_file(exchange_file, sym_from_json)
    except Exception as e:
        print(f"dump error: {e}")
        print_exc()


def dump_basename_from_exchange(basename: str, exchange: str):
    """
    description: convert the exchange json into basename wise csv
    """
    path_and_file = f"{S_DATA}{exchange}.json"

    symbols_from_json = O_FUTL.read_file(path_and_file)

    # Convert the raw JSON list to a DataFrame immediately
    df = pd.DataFrame(symbols_from_json)

    # 1. Filter by basename and instrument type
    df = df[df["name"] == basename]
    df = df[df["instrument_type"].isin(["CE", "PE"])]

    # 2. Select only the necessary columns and fix types
    cols = [
        "expiry",
        "tradingsymbol",
        "instrument_token",
        "strike",
        "instrument_type",
    ]
    df = df[cols]
    df["strike"] = pd.to_numeric(df["strike"]).astype(int)

    # 3. Process CE and PE separately
    for option_type in ["CE", "PE"]:
        subset = df[df["instrument_type"] == option_type].copy()

        # Sort: CE Ascending, PE Descending
        ascending = True if option_type == "CE" else False
        subset = subset.sort_values(by="strike", ascending=ascending)
        # Define path: data/ce/nifty.csv
        file_path = f"{S_DATA}/{option_type}/{basename}.csv"
        if O_FUTL.is_file_exists(file_path):
            # Drop the instrument_type column before saving since it's redundant in the folder
            subset.drop(columns=["instrument_type"]).to_csv(file_path, index=False)


def find_symbolinfo(
    ce_or_pe: OptionType, base_expiry: str, start: int, num_of_strikes: int
):
    """
    prepare the symbol data to csv, so sorting can be done easily

    params:
    option_type: "CE" or "PE"
    base_expiry: str in date format

    return:
    list of dictionaries containing symbol info namely expiry, tradingsymbol, instrument_token, strike
    """

    try:
        # Parsing the input
        lst = base_expiry.split(" ")
        basename, expiry = lst[0], lst[1].replace("(", "").replace(")", "")

        # Load the CSV
        csv_file = f"{S_DATA}{ce_or_pe}/{basename}.csv"
        df = pd.read_csv(csv_file)
        logging.debug(df.expiry)

        # 1. Filter by expiry first
        df = df[df["expiry"] == expiry].reset_index(drop=True)

        # 2. Find the index of the row where 'strike' equals 'start'
        # We use .index[0] to get the first occurrence
        matching_indices = df.index[df["strike"] == start].tolist()

        if not matching_indices:
            print(f"Strike {start} not found for {expiry}")
            return df.dataframe()

        start_idx = matching_indices[0]

        # 3. Slice the dataframe starting from start_idx for the length of num_of_strikes
        # iloc[start:stop] handles out-of-bounds automatically by returning available rows
        df_sliced = df.iloc[start_idx : start_idx + num_of_strikes]

        return df_sliced
    except Exception as e:
        print(f"Error in find trading symbol: {e}")
        return df.dataframe()


def find_call_and_put_from_dropdown(
    side: str, base_expiry: str, ce_start: int, pe_start: int, num_of_strikes: int
):
    df_ce = find_symbolinfo(
        ce_or_pe="CE",
        start=ce_start,
        base_expiry=base_expiry,
        num_of_strikes=num_of_strikes,
    )

    df_pe = find_symbolinfo(
        ce_or_pe="PE",
        start=pe_start,
        base_expiry=base_expiry,
        num_of_strikes=num_of_strikes,
    )

    return df_ce, df_pe


if __name__ == "__main__":
    from pprint import pprint

    from api import Helper
    from constants import D_SYMBOL
    from wsocket import Wsocket

    SUBSCRIBED = {"left": [], "right": []}

    for kwargs in D_SYMBOL.values():
        # first download the csv to json
        dump(kwargs["exchange"])

        # filter the json further by base name
        dump_basename_from_exchange(kwargs["name"], kwargs["exchange"])

    # we need to accepts arguments from the dependant dropdown
    df_ce, df_pe = find_call_and_put_from_dropdown(
        side="left",
        base_expiry="BANKNIFTY (2026-02-24)",
        ce_start=60600,
        pe_start=60600,
        num_of_strikes=15,
    )

    SUBSCRIBED["left"] = df_ce["instrument_token"].to_list()
    SUBSCRIBED["left"].append(df_pe["instrument_token"].to_list())

    api = Helper.api()
    ws = Wsocket(api, [SUBSCRIBED["left"]])
    ticks = {}
    while not any(ticks):
        ticks = ws.ltp()
        __import__("time").sleep(5)
    else:
        print(ticks)
