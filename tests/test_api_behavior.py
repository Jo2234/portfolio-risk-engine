from __future__ import annotations

import pytest


def create_portfolio(client, payload: dict[str, object]) -> str:
    response = client.post("/portfolios", json=payload)
    assert response.status_code == 201
    return response.json()["portfolio_id"]


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_portfolio_normalizes_symbols_and_exposes_metadata(client, two_asset_portfolio_payload):
    payload = {
        **two_asset_portfolio_payload,
        "positions": [
            {"symbol": "aapl", "weight": 0.6},
            {"symbol": "msft", "weight": 0.4},
        ],
    }

    response = client.post("/portfolios", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["validation"] == {"weight_total": 1.0, "supported": True}
    assert [position["symbol"] for position in body["positions"]] == ["AAPL", "MSFT"]
    assert [position["sector"] for position in body["positions"]] == ["Technology", "Technology"]
    assert all(position["asset_class"] == "market" for position in body["positions"])


@pytest.mark.parametrize(
    ("positions", "expected_detail"),
    [
        ([{"symbol": "AAPL", "weight": 0.7}], "Weights must sum to 1.0"),
        (
            [{"symbol": "AAPL", "weight": 0.6}, {"symbol": "DOGE", "weight": 0.4}],
            "Unsupported symbols",
        ),
    ],
)
def test_create_portfolio_rejects_invalid_payloads(client, two_asset_portfolio_payload, positions, expected_detail):
    response = client.post("/portfolios", json={**two_asset_portfolio_payload, "positions": positions})

    assert response.status_code == 422
    assert expected_detail in str(response.json()["detail"])


def test_analyze_rejects_missing_portfolio_and_invalid_var_confidence(client):
    missing = client.post(
        "/portfolios/not-a-real-id/analyze",
        json={"start_date": "2024-01-01", "end_date": "2024-01-09", "var_confidence": 0.95},
    )
    invalid_confidence = client.post(
        "/portfolios/not-a-real-id/analyze",
        json={"start_date": "2024-01-01", "end_date": "2024-01-09", "var_confidence": 0.5},
    )

    assert missing.status_code == 404
    assert invalid_confidence.status_code == 422


def test_analyze_returns_metrics_scenarios_summary_and_persisted_report(
    client,
    deterministic_prices,
    two_asset_portfolio_payload,
):
    portfolio_id = create_portfolio(client, two_asset_portfolio_payload)

    no_report = client.get(f"/portfolios/{portfolio_id}/report")
    analyze = client.post(
        f"/portfolios/{portfolio_id}/analyze",
        json={"start_date": "2024-01-01", "end_date": "2024-01-09", "var_confidence": 0.95},
    )
    report = client.get(f"/portfolios/{portfolio_id}/report")

    assert no_report.status_code == 404
    assert analyze.status_code == 200
    assert report.status_code == 200
    assert report.json() == analyze.json()

    body = analyze.json()
    assert body["portfolio_id"] == portfolio_id
    assert {"metrics", "scenarios", "summary"} <= body.keys()
    assert body["summary"].endswith("are not forecasts.")
    assert {scenario["scenario"] for scenario in body["scenarios"]} == {
        "COVID crash",
        "2022 rates shock",
        "2018 Q4 selloff",
        "Regional banking stress",
    }


def test_hypothetical_stress_applies_direct_and_broad_market_shocks(
    client,
    two_asset_portfolio_payload,
):
    portfolio_id = create_portfolio(client, two_asset_portfolio_payload)

    response = client.post(
        f"/portfolios/{portfolio_id}/stress",
        json={
            "shocks": [
                {"target": "SPY", "shock_pct": -0.10},
                {"target": "AAPL", "shock_pct": -0.20},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["estimated_portfolio_return"] == pytest.approx(-0.185)
    assert body["estimated_dollar_impact"] == pytest.approx(-18500.0)
    assert body["contributors"][0] == {
        "symbol": "AAPL",
        "applied_shock": -0.20,
        "portfolio_impact": -0.12,
    }
    assert "Broad equity shocks use a simple 0.65 beta proxy for equity-like holdings." in body["assumptions"]
    assert body["limitations"] == ["Hypothetical shocks are approximations, not forecasts."]


def test_stress_rejects_missing_portfolio(client):
    response = client.post(
        "/portfolios/not-a-real-id/stress",
        json={"shocks": [{"target": "SPY", "shock_pct": -0.10}]},
    )

    assert response.status_code == 404
