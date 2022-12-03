import krakenex
from test_data.mock_data import DATA_SET_A, DATA_SET_B, DATA_SET_C
import pandas as pd
from pandas.testing import assert_frame_equal


kraken = krakenex.API()
asset_selected = 'XETH'
quote_selected = 'ZUSD'

def test_succcessfuL_get_pair():
    new_data = kraken.query_public(
    "Trades",
    {"pair": asset_selected + quote_selected},
    )

    assert new_data['result'][asset_selected + quote_selected]

def test_unsuccessful_get_pair():
    asset_selected = 'wrong_asset'
    quote_selected = 'wrong_quot'

    new_data = kraken.query_public(
    "Trades",
    {"pair": asset_selected + quote_selected},
    )

    assert new_data['error']

def test_old_data():
    if DATA_SET_A is None:
        pass
    else:
        new_data = pd.concat([DATA_SET_A, DATA_SET_B], axis=0)
    assert_frame_equal(new_data, DATA_SET_C)