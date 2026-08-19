"""Tests fuer das Aktien-Portfolio (Yahoo Finance gemockt)."""
import stocks


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def _meta(price, prev_close):
    return {"chart": {"result": [{"meta": {
        "regularMarketPrice": price, "previousClose": prev_close,
    }}]}}


def _patch_holdings(monkeypatch, holdings):
    monkeypatch.setattr(stocks, "HOLDINGS", holdings)


def test_portfolio_value_and_pl(monkeypatch):
    # 19.69439728 MRNA @ 117.80 gekauft, jetzt 128.88, gestern 125.00.
    _patch_holdings(monkeypatch, {"MRNA": {"amount": 19.69439728, "cost_usd": 2320.00}})
    monkeypatch.setattr(stocks.requests, "get",
                        lambda *a, **k: _Resp(_meta(128.88, 125.00)))
    p = stocks.get_portfolio()
    amount = 19.69439728
    assert round(p.total, 2) == round(amount * 128.88, 2)
    assert round(p.day_usd, 2) == round(amount * (128.88 - 125.00), 2)
    assert round(p.cost, 2) == 2320.00
    assert round(p.pl_usd, 2) == round(amount * 128.88 - 2320.00, 2)


def test_portfolio_none_on_missing_price(monkeypatch):
    _patch_holdings(monkeypatch, {"MRNA": {"amount": 1.0, "cost_usd": 100.0}})
    monkeypatch.setattr(stocks.requests, "get",
                        lambda *a, **k: _Resp({"chart": {"result": [{"meta": {}}]}}))
    assert stocks.get_portfolio() is None


def test_portfolio_none_on_request_error(monkeypatch):
    def boom(*a, **k):
        raise stocks.requests.RequestException("net down")
    monkeypatch.setattr(stocks.requests, "get", boom)
    assert stocks.get_portfolio() is None


def test_portfolio_none_on_malformed_response(monkeypatch):
    monkeypatch.setattr(stocks.requests, "get", lambda *a, **k: _Resp({}))
    assert stocks.get_portfolio() is None


def test_real_holdings_have_cost_basis():
    for symbol, h in stocks.HOLDINGS.items():
        assert h["cost_usd"] is not None and h["cost_usd"] > 0, symbol
        assert h["amount"] > 0, symbol
