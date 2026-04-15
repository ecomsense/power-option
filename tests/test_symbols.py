import pytest
import sys
sys.path.insert(0, "src")

from symbols import (
    find_expiry_from_base,
    find_strike_from_base_expiry,
    find_symbolinfo,
    find_call_and_put_from_dropdown,
)


class TestSymbols:
    def test_find_expiry_returns_list(self):
        result = find_expiry_from_base("NIFTY")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_find_expiry_returns_valid_dates(self):
        result = find_expiry_from_base("BANKNIFTY")
        for exp in result:
            assert isinstance(exp, str)
            assert len(exp) == 10

    def test_find_expiry_sorted_latest_first(self):
        result = find_expiry_from_base("NIFTY")
        dates = result
        sorted_dates = sorted(dates, reverse=True)
        assert dates == sorted_dates, "Expiries should be sorted latest first"

    def test_find_expiry_invalid_base(self):
        result = find_expiry_from_base("INVALID")
        assert result in ([], None)  # returns [] or None on error

    def test_find_strike_returns_dict(self):
        result = find_strike_from_base_expiry("NIFTY", "2026-04-21")
        assert isinstance(result, dict)
        assert "CE" in result
        assert "PE" in result

    def test_find_strike_returns_strike_lists(self):
        result = find_strike_from_base_expiry("BANKNIFTY", "2026-05-26")
        assert isinstance(result["CE"], list)
        assert isinstance(result["PE"], list)
        assert len(result["CE"]) > 0
        assert len(result["PE"]) > 0

    def test_find_strike_sorted(self):
        result = find_strike_from_base_expiry("NIFTY", "2026-04-21")
        ce_strikes = result["CE"]
        pe_strikes = result["PE"]
        assert ce_strikes == sorted(ce_strikes), "CE should be sorted ascending"
        assert pe_strikes == sorted(pe_strikes, reverse=True), "PE should be sorted descending"

    def test_find_strike_invalid_expiry(self):
        result = find_strike_from_base_expiry("NIFTY", "2099-99-99")
        assert result["CE"] == []
        assert result["PE"] == []

    def test_find_symbolinfo_ce(self):
        result = find_symbolinfo("CE", "NIFTY", "2026-04-21", 22000, 5)
        assert len(result) == 5
        assert result.iloc[0]["strike"] == 22000

    def test_find_symbolinfo_pe(self):
        result = find_symbolinfo("PE", "NIFTY", "2026-04-21", 22000, 5)
        assert len(result) == 5
        assert result.iloc[0]["strike"] == 22000

    def test_find_symbolinfo_strike_not_found(self):
        result = find_symbolinfo("CE", "NIFTY", "2026-04-21", 999999, 5)
        assert len(result) == 0

    def test_find_call_and_put_returns_dataframes(self):
        df_ce, df_pe = find_call_and_put_from_dropdown(
            "NIFTY", "2026-04-21", 22000, 22000, 5
        )
        assert len(df_ce) == 5
        assert len(df_pe) == 5

    def test_find_call_and_put_no_matching_strike(self):
        df_ce, df_pe = find_call_and_put_from_dropdown(
            "NIFTY", "2026-04-21", 999999, 999999, 5
        )
        assert len(df_ce) == 0
        assert len(df_pe) == 0

    def test_all_symbols_accessible(self):
        for basename in ["NIFTY", "BANKNIFTY", "SENSEX"]:
            expiries = find_expiry_from_base(basename)
            assert len(expiries) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])