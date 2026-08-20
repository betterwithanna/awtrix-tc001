"""Tests fuer das SmallCap-Portfolio (CoinGecko gemockt)."""
import smallcap


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def _patch_prices(monkeypatch, payload):
    monkeypatch.setattr(smallcap.requests, "get", lambda *a, **k: _Resp(payload))


def _patch_holdings(monkeypatch, holdings):
    monkeypatch.setattr(smallcap, "HOLDINGS", holdings)


def test_portfolio_value_and_pl(monkeypatch):
    _patch_holdings(monkeypatch, {
        "troll-2": {"amount": 100.0, "cost_eur": 40.0},
        "buttcoin-7": {"amount": 200.0, "cost_eur": 60.0},
    })
    _patch_prices(monkeypatch, {
        "troll-2": {"eur": 0.5, "eur_24h_change": 0.0},
        "buttcoin-7": {"eur": 0.3, "eur_24h_change": 0.0},
    })
    p = smallcap.get_portfolio()
    assert round(p.total, 2) == round(100 * 0.5 + 200 * 0.3, 2)
    assert round(p.cost, 2) == 100.0
    assert round(p.pl_eur, 2) == round(p.total - 100.0, 2)


def test_portfolio_positive_day_change(monkeypatch):
    _patch_holdings(monkeypatch, {"troll-2": {"amount": 10.0, "cost_eur": 5.0}})
    _patch_prices(monkeypatch, {"troll-2": {"eur": 1.1, "eur_24h_change": 10.0}})
    p = smallcap.get_portfolio()
    assert round(p.day_pct, 2) == 10.0
    assert p.day_eur > 0


def test_portfolio_none_on_missing_price(monkeypatch):
    _patch_holdings(monkeypatch, {"troll-2": {"amount": 1.0, "cost_eur": 1.0}})
    _patch_prices(monkeypatch, {"troll-2": {}})
    assert smallcap.get_portfolio() is None


def test_portfolio_none_on_request_error(monkeypatch):
    def boom(*a, **k):
        raise smallcap.requests.RequestException("net down")
    monkeypatch.setattr(smallcap.requests, "get", boom)
    assert smallcap.get_portfolio() is None


def test_real_holdings_have_cost_basis():
    for coin_id, h in smallcap.HOLDINGS.items():
        assert h["cost_eur"] is not None and h["cost_eur"] > 0, coin_id
        assert h["amount"] > 0, coin_id
