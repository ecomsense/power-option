class Symbols:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.diff = kwargs["diff"]
        self.depth = kwargs["depth"]
        self.exchange = kwargs["exchange"]

        self.instrument_token = kwargs["instrument_token"]
        self.trading_symbol = kwargs["tradingsymbol"]

        self.symbols_from_json = O_FUTL.read_file(S_DATA + self.exchange + ".json")
        self.expiry_date = self._get_expiry()

    def _get_expiry(self, expiry_offset=0):
        """
        Get the expiry date for the specified base instrument with an optional expiry offset.

        Parameters:
        expiry_offset (int, optional): The offset from the current date to the desired expiry date. Defaults to 0.

        Returns:
        pd.Timestamp or None: The expiry date if found, otherwise None.
        """
        try:
            # Create DataFrame and filter by name
            df = pd.DataFrame(self.symbols_from_json)
            filtered_df = df[df["name"] == self.name]

            # Drop duplicates, convert expiry to datetime, and filter future expiries
            filtered_df = filtered_df.drop_duplicates(subset=["expiry"])
            filtered_df["expiry"] = pd.to_datetime(filtered_df["expiry"])
            today = pd.Timestamp.now().normalize()
            future_expiries = filtered_df[filtered_df["expiry"] >= today]

            # Sort and check offset
            future_expiries = future_expiries.sort_values(by="expiry")
            if 0 <= expiry_offset < len(future_expiries):
                expiry_datetime = future_expiries.iloc[expiry_offset]["expiry"]
                # convert date time to date string
                # TODO
                expiry_date = pdlm.instance(expiry_datetime).to_date_string()
                logging.info(
                    f"Expiry date with offset {expiry_offset} for {self.name}: {expiry_date}"
                )
                return expiry_date
            raise Exception(f"no expiry found for {self.name}")
        except Exception as e:
            logging.error(f"get expiry error: {e}")
            print_exc()
            raise

    def tokens_from_symbols(self, symbols: list[str]):
        try:
            filtered = []
            if isinstance(symbols, str):
                symbols = [symbols]
            for symtoken in self.symbols_from_json:
                if symtoken["tradingsymbol"] in symbols:
                    filtered.append(symtoken)
            return filtered
        except Exception as e:
            print(f"tokens from symbols error: {e}")
            print_exc()

    def calc_atm_from_ltp(self, ltp):
        return round(ltp / self.diff) * self.diff

    def _generate_symbols(self, atm, depth):
        """
        Generate a list of option symbols based on the given ATM (At the Money) price and depth.

        Parameters:
        atm (int): The At the Money price for the base instrument.
        depth (int): The number of strikes above and below the ATM price to include in the build chain.

        Returns:
        list: A list of option symbols (tradingsymbols) for the specified ATM and depth.
        """
        # Filter by the base, expiry
        df = pd.DataFrame(self.symbols_from_json)
        # df["expiry"] = pd.to_datetime(df["expiry"])
        filtered_df = df[(df["name"] == self.name) & (df["expiry"] == self.expiry_date)]

        merged_list = []
        for ce_or_pe in ["CE", "PE"]:
            option_df = filtered_df[filtered_df["instrument_type"] == ce_or_pe]

            # Sort DataFrame by strike
            option_df = option_df.sort_values(by="strike")

            # Find the index of the closest strike to the base strike
            closest_index = option_df.index[
                (option_df["strike"] - atm).abs().argsort()[:1]
            ].tolist()

            if not closest_index:
                continue  # Skip if no closest strike found

            closest_index = closest_index[0]

            # Get the sorted strikes
            strikes = option_df["strike"].tolist()

            # Find the position of the base strike in the sorted list
            base_position = strikes.index(option_df.loc[closest_index, "strike"])

            # Calculate the range for the depth
            start_index = max(base_position - depth, 0)
            end_index = min(base_position + depth + 1, len(strikes))

            # Filter rows within the depth range
            depth_filtered_df = option_df.iloc[start_index:end_index]
            merged_list.append(depth_filtered_df.iloc[0]["tradingsymbol"])
            print(f"Merged Build chain {merged_list}")
        return merged_list

    def new_chain(self, ltp, full_chain=0):
        try:
            atm = self.calc_atm_from_ltp(ltp)
            depth = full_chain
            symbols = self._generate_symbols(atm, depth)
            filter = self.tokens_from_symbols(symbols)
            return filter
        except Exception as e:
            print(f"generate_symbols error: {e}")
            print_exc()

    """
    def build_chain(self, ltp, full_chain=False):
        txt = "Build chain" if full_chain else "Straddle"
        atm = self.calc_atm_from_ltp(ltp)
        print(f"{atm=}")
        lst = []
        lst.append(self.name + self.expiry + str(atm) + "CE")
        lst.append(self.name + self.expiry + str(atm) + "PE")
        if full_chain:
            for v in range(1, self.depth):
                txt = self.name + self.expiry + str(atm + (v * self.diff)) + "CE"
                print(txt)
                lst.append(txt)
                lst.append(self.name + self.expiry + str(atm + (v * self.diff)) + "PE")
                lst.append(self.name + self.expiry + str(atm - (v * self.diff)) + "CE")
                lst.append(self.name + self.expiry + str(atm - (v * self.diff)) + "PE")
        filtered = self.tokens_from_symbols(lst)
        if not any(filtered):
            raise Exception("tokens not found")
        elif full_chain:
            self.symbols_from_json = filtered
        return filtered

    def get_option_symbols(self, ltp):
        straddle = self.build_chain(ltp, full_chain=False)
        # Use dictionary comprehension to map instrument types to their symbols
        symbols = {item["instrument_type"]: item["tradingsymbol"] for item in straddle}
        print(f"{symbols=}")

        # Extract the symbols for CE and PE
        ce_symbol = symbols.get("CE")
        pe_symbol = symbols.get("PE")

        logging.debug(f"CE symbol: {ce_symbol}, PE symbol: {pe_symbol}")
        return ce_symbol, pe_symbol
    """
