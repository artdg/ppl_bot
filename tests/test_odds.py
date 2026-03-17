from app.services.odds import OddsConfig, compute_odds


def test_compute_odds_default_when_no_bets() -> None:
    c1, c2 = compute_odds(0, 0)
    assert c1 == 2.0
    assert c2 == 2.0


def test_compute_odds_is_bounded() -> None:
    cfg = OddsConfig(min_coef=1.2, max_coef=5.0, margin=0.05, base=0)
    c1, c2 = compute_odds(1_000_000, 1, cfg=cfg)
    assert 1.2 <= c1 <= 5.0
    assert 1.2 <= c2 <= 5.0

