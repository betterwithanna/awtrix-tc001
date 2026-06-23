"""Tests fuer das Krypto-Portfolio (CoinGecko gemockt)."""
import crypto


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def _patch_prices(monkeypatch, payload):
    monkeypatch.setattr(crypto.requests, "get", lambda *a, **k: _Resp(payload))


def test_portfolio_value_and_change(monkeypatch):
    # BTC 0.04932662 @ 50000 (+0% heute), SOL 45.46 @ 100 (+0%)
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 50000, "eur_24h_change": 0.0},
        "solana": {"eur": 100, "eur_24h_change": 0.0},
    })
    total, pct, eur = crypto.get_portfolio()
    assert round(total, 2) == round(0.04932662 * 50000 + 45.46 * 100, 2)
    assert round(pct, 4) == 0.0 and round(eur, 4) == 0.0


def test_portfolio_positive_change(monkeypatch):
    # beide +10% heute -> Tagesgewinn = total * (1 - 1/1.1)
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 55000, "eur_24h_change": 10.0},
        "solana": {"eur": 110, "eur_24h_change": 10.0},
    })
    total, pct, eur = crypto.get_portfolio()
    assert round(pct, 2) == 10.0
    assert eur > 0 and round(eur, 2) == round(total - total / 1.1, 2)


def test_portfolio_none_on_missing_price(monkeypatch):
    _patch_prices(monkeypatch, {"bitcoin": {"eur": 50000}, "solana": {}})
    assert crypto.get_portfolio() is None


def test_portfolio_none_on_request_error(monkeypatch):
    def boom(*a, **k):
        raise crypto.requests.RequestException("net down")
    monkeypatch.setattr(crypto.requests, "get", boom)
    assert crypto.get_portfolio() is None
