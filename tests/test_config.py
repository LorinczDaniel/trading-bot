from config.settings import Settings


def test_defaults(monkeypatch, tmp_path):
    # Run in an empty dir so no real .env is read.
    monkeypatch.chdir(tmp_path)
    for var in ("EXCHANGE_ID", "EXCHANGE_API_KEY", "EXCHANGE_API_SECRET", "USE_TESTNET"):
        monkeypatch.delenv(var, raising=False)
    s = Settings()
    assert s.exchange_id == "binance"
    assert s.use_testnet is True
    assert s.exchange_api_key == ""


def test_from_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXCHANGE_ID", "kraken")
    monkeypatch.setenv("USE_TESTNET", "false")
    s = Settings()
    assert s.exchange_id == "kraken"
    assert s.use_testnet is False
