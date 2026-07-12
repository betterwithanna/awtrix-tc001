"""Tests fuer das Krypto-Portfolio (CoinGecko gemockt).

Die Tests setzen HOLDINGS explizit (monkeypatch), damit sie unabhaengig von den
realen Bestaenden bleiben -- diese aendern sich bei jedem Kauf/Staking-Update.
"""
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


def _patch_holdings(monkeypatch, holdings):
    monkeypatch.setattr(crypto, "HOLDINGS", holdings)


def test_portfolio_value_and_change(monkeypatch):
    # BTC 0.04932662 @ 50000 (+0% heute), SOL 45.46 @ 100 (+0%)
    _patch_holdings(monkeypatch, {
        "bitcoin": {"amount": 0.04932662, "cost_eur": None},
        "solana": {"amount": 45.46, "cost_eur": None},
    })
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 50000, "eur_24h_change": 0.0},
        "solana": {"eur": 100, "eur_24h_change": 0.0},
    })
    p = crypto.get_portfolio()
    assert round(p.total, 2) == round(0.04932662 * 50000 + 45.46 * 100, 2)
    assert round(p.day_pct, 4) == 0.0 and round(p.day_eur, 4) == 0.0


def test_portfolio_positive_change(monkeypatch):
    # beide +10% heute -> Tagesgewinn = total * (1 - 1/1.1)
    _patch_holdings(monkeypatch, {
        "bitcoin": {"amount": 0.04932662, "cost_eur": None},
        "solana": {"amount": 45.46, "cost_eur": None},
    })
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 55000, "eur_24h_change": 10.0},
        "solana": {"eur": 110, "eur_24h_change": 10.0},
    })
    p = crypto.get_portfolio()
    assert round(p.day_pct, 2) == 10.0
    assert p.day_eur > 0 and round(p.day_eur, 2) == round(p.total - p.total / 1.1, 2)


def test_since_buy_pl_none_without_cost(monkeypatch):
    # Fehlt bei EINEM Coin cost_eur -> keine Seit-Kauf-Rendite.
    _patch_holdings(monkeypatch, {
        "bitcoin": {"amount": 1.0, "cost_eur": None},
    })
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 50000, "eur_24h_change": 0.0},
    })
    p = crypto.get_portfolio()
    assert p.cost is None and p.pl_eur is None and p.pl_pct is None


def test_since_buy_pl_computed_with_cost(monkeypatch):
    # 1 BTC fuer 40.000 EUR gekauft, jetzt 50.000 EUR wert -> +10.000 EUR / +25%.
    _patch_holdings(monkeypatch, {
        "bitcoin": {"amount": 1.0, "cost_eur": 40000.0},
    })
    _patch_prices(monkeypatch, {
        "bitcoin": {"eur": 50000, "eur_24h_change": 0.0},
    })
    p = crypto.get_portfolio()
    assert round(p.cost, 2) == 40000.0
    assert round(p.pl_eur, 2) == 10000.0
    assert round(p.pl_pct, 2) == 25.0


def test_real_holdings_have_cost_basis():
    # Regressionsschutz: reale Bestaende tragen eine Kostenbasis (Seit-Kauf aktiv).
    for coin, h in crypto.HOLDINGS.items():
        assert h["cost_eur"] is not None and h["cost_eur"] > 0, coin


def test_portfolio_none_on_missing_price(monkeypatch):
    _patch_holdings(monkeypatch, {
        "bitcoin": {"amount": 0.04932662, "cost_eur": None},
        "solana": {"amount": 45.46, "cost_eur": None},
    })
    _patch_prices(monkeypatch, {"bitcoin": {"eur": 50000}, "solana": {}})
    assert crypto.get_portfolio() is None


def test_portfolio_none_on_request_error(monkeypatch):
    def boom(*a, **k):
        raise crypto.requests.RequestException("net down")
    monkeypatch.setattr(crypto.requests, "get", boom)
    assert crypto.get_portfolio() is None
