from traceback import print_exc
from typing import Any, Literal, Tuple  # Use list[dict] for the return type

import pandas as pd
from constants import D_SYMBOL, O_FUTL, S_DATA, logging

OptionType = Literal["CE", "PE"]


def read_symbol_info_from_url(exchange: str) -> list[dict[str, Any]]:
    """
    1. write symbol info to json first
    helper function to download csv from broker

    parameters:
        accepts exchange "NFO"

    returns:
        a list of dicts: [{"tradingsymbol": "NIFTY...", ...}, ...]
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

        return df.to_dict(orient="records")

    except Exception as e:
        logging.error(f"Error fetching {exchange}: {e}")
        print_exc()
        return []  # Return empty list on failure to keep the type consistent


def dump(exchange: str) -> None:
    """Helper function to get symbol info by exchange
    and write it to json in data dir

    Args:
        exchange: NFO for example.
    """
    try:
        # what exchange and its symbols should be dumped
        exchange_file = S_DATA + exchange + ".json"

        if O_FUTL.is_file_not_2day(exchange_file):
            sym_from_json = read_symbol_info_from_url(exchange)
            O_FUTL.write_file(exchange_file, sym_from_json)
    except Exception as e:
        logging.error(f"dump error: {e}")
        print_exc()


def dump_basename_from_exchange(basename: str, exchange: str) -> None:
    """
    2. convert the exchange json into basename wise csv
    Args:
       basename : NIFTY for example
    """
    try:
        dump(exchange)

        # what exchange and its symbols should be dumped
        exchange_file = S_DATA + exchange + ".json"

        symbols_from_json = O_FUTL.read_file(exchange_file)

        # Convert the raw JSON list to a DataFrame immediately
        df = pd.DataFrame(symbols_from_json)

        #  Filter by basename and instrument type
        df = df[df["name"] == basename]
        df = df[df["instrument_type"].isin(["CE", "PE"])]

        #  Select only the necessary columns and fix types
        cols = [
            "expiry",
            "tradingsymbol",
            "instrument_token",
            "strike",
            "instrument_type",
        ]
        df = df[cols]
        df["strike"] = pd.to_numeric(df["strike"]).astype(int)

        #  Process CE and PE separately
        for option_type in ["CE", "PE"]:
            subset = df[df["instrument_type"] == option_type].copy()

            # Sort: CE Ascending, PE Descending
            ascending = True if option_type == "CE" else False
            subset = subset.sort_values(by="strike", ascending=ascending)

            # Define path: data/ce/nifty.csv
            file_path = f"{S_DATA}/{option_type}/{basename}.csv"
            while not O_FUTL.is_file_exists(file_path):
                logging.info(f"waiting for the {file_path} to write")
                __import__("time").sleep(1)
            else:
                # Drop the instrument_type column before saving since it's redundant in the folder
                subset.drop(columns=["instrument_type"]).to_csv(file_path, index=False)
    except Exception as e:
        logging.error(f"{e} while dumping basename from exchange")
        print_exc()


def find_base() -> list:
    """3. populate unique basename (expiries) for the UI from csv

    returns:
        list of unique basename expiries BANKNIFTY (2030-11-01)
    """
    try:
        return list(D_SYMBOL.keys())
    except Exception as e:
        logging.error(f"{e} while")
        print_exc()


def find_expiry_from_base(basename):
    try:
        file_path = f"{S_DATA}/CE/{basename}.csv"
        df = pd.read_csv(file_path)
        formatted = df["expiry"].astype(str)
        expiries = formatted.unique().tolist()
        # Convert to date, sort oldest first (nearest expiry first)
        expiries = sorted(expiries, key=lambda x: __import__("datetime").datetime.strptime(x, "%Y-%m-%d"))
        return expiries
    except Exception as e:
        logging.error(f"{e} when finding expiry from base")
        print_exc()


def find_strike_from_base_expiry(basename, expiry) -> dict:
    """4. get data dependant drop downs

    returns:
        dict containing keys "CE" and "PE"
        with values as strike prices
    """
    try:
        dct = {}
        for option_type in ["CE", "PE"]:
            file_path = f"{S_DATA}/{option_type}/{basename}.csv"
            df = pd.read_csv(file_path)
            df = df[df["expiry"] == expiry]
            dct[option_type] = df["strike"].to_list()
        return dct
    except Exception as e:
        logging.error(f"{e} while")
        print_exc()


def find_symbolinfo(
    ce_or_pe: OptionType, basename: str, expiry: str, start: int, num_of_strikes: int
) -> pd.DataFrame:
    """5. helper function to find symbol infos based on the request from UI

    params:
        option_type: "CE" or "PE"
        base_expiry: str in date format
        start: the starting strike price
        num_of_strikes: count from the num of strikes from the start

    return:
        dataframe containing symbol info namely expiry, tradingsymbol, instrument_token, strike
    """
    try:
        # Parsing the input
        # Load the CSV
        csv_file = f"{S_DATA}{ce_or_pe}/{basename}.csv"
        df = pd.read_csv(csv_file)
        # 1. Filter by expiry first
        df = df[df["expiry"] == str(expiry)].reset_index(drop=True)

        # 2. Find the index of the row where 'strike' equals 'start'
        # We use .index[0] to get the first occurrence
        matching_indices = df.index[df["strike"] == start].tolist()

        if not matching_indices:
            logging.warning(f"Strike {start} not found for {expiry}")
            return pd.DataFrame()

        start_idx = matching_indices[0]

        # 3. Slice the dataframe starting from start_idx for the length of num_of_strikes
        # iloc[start:stop] handles out-of-bounds automatically by returning available rows
        df_sliced = df.iloc[start_idx : start_idx + num_of_strikes]

        return df_sliced
    except Exception as e:
        logging.error(f"{e} error in find trading symbol")
        print_exc()
        return pd.DataFrame()


def find_call_and_put_from_dropdown(
    basename: str, expiry: str, ce_start: int, pe_start: int, num_of_strikes: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """6. wrapper to get symbol info dataframes

    Args:
        base_expiry: combination of base and expiry
        ce_start: starting stike of ce
        pe_start: starting strike of pe
        num_of_strikes: number of strikes to retrieve

    returns:
        call and put dataframes
    """
    try:
        df_ce = find_symbolinfo(
            ce_or_pe="CE",
            start=ce_start,
            basename=basename,
            expiry=expiry,
            num_of_strikes=num_of_strikes,
        )
        df_pe = find_symbolinfo(
            ce_or_pe="PE",
            start=pe_start,
            basename=basename,
            expiry=expiry,
            num_of_strikes=num_of_strikes,
        )
        return df_ce, df_pe
    except Exception as e:
        logging.error(f"{e} while")
        print_exc()


if __name__ == "__main__":
    from pprint import pprint

    from api import Helper
    from constants import D_SYMBOL
    from wsocket import Wsocket

    """
    # we need to accepts arguments from the dependant dropdown
    df_ce, df_pe = find_call_and_put_from_dropdown(
        base_expiry="BANKNIFTY (2026-02-24)",
        ce_start=60600,
        pe_start=60600,
        num_of_strikes=15,
    )
    api = Helper.api()
    ws = Wsocket(api, SUBSCRIBED["left"])
    ticks = {}
    while not any(ticks):
        ticks = ws.ltp()
        __import__("time").sleep(5)
    else:
        logging.debug(ticks)

    """

    base_expiry = "BANKNIFTY (2026-02-24)"
    resp = find_strike_from_base_expiry(base_expiry)
    logging.debug(resp)
