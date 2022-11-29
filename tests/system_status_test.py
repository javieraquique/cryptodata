import krakenex
import json
kraken = krakenex.API()


def test_successful_systemStatus():
    server_time = kraken.query_public("Time")
    if server_time["error"]:
        assert server_time["error"]
    else:
        assert server_time["result"]