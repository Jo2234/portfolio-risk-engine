from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

PORTFOLIO = {
    "name": "AI Barbell Portfolio",
    "portfolio_value": 100000,
    "benchmark_symbol": "SPY",
    "positions": [
        {"symbol": "NVDA", "weight": 0.2},
        {"symbol": "MSFT", "weight": 0.2},
        {"symbol": "JPM", "weight": 0.15},
        {"symbol": "XOM", "weight": 0.1},
        {"symbol": "GLD", "weight": 0.1},
        {"symbol": "TLT", "weight": 0.1},
        {"symbol": "CASH", "weight": 0.15},
    ],
}


def create():
    return client.post("/portfolios", json=PORTFOLIO).json()["portfolio_id"]


def test_weight_validation():
    bad = {**PORTFOLIO, "positions": [{"symbol": "SPY", "weight": 0.5}]}
    assert client.post("/portfolios", json=bad).status_code == 422


def test_analyze_returns_risk_metrics():
    pid = create()
    response = client.post(f"/portfolios/{pid}/analyze", json={"start_date": "2021-01-01", "var_confidence": 0.95})
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert "expected_shortfall" in metrics
    assert "correlation_matrix" in metrics


def test_stress_has_contributors():
    pid = create()
    response = client.post(f"/portfolios/{pid}/stress", json={"shocks": [{"target": "QQQ", "shock_pct": -0.15}]})
    assert response.status_code == 200
    assert response.json()["contributors"]
