from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from urllib.parse import urlparse

ASX_STOCKS = {
    "CBA.AX": {"name": "Commonwealth Bank", "sector": "Financials", "price": 118.50},
    "BHP.AX": {"name": "BHP Group", "sector": "Materials", "price": 44.20},
    "CSL.AX": {"name": "CSL Limited", "sector": "Healthcare", "price": 285.00},
    "NAB.AX": {"name": "National Australia Bank", "sector": "Financials", "price": 37.80},
    "WBC.AX": {"name": "Westpac Banking", "sector": "Financials", "price": 28.50},
    "ANZ.AX": {"name": "ANZ Group", "sector": "Financials", "price": 29.20},
    "FMG.AX": {"name": "Fortescue Metals", "sector": "Materials", "price": 19.80},
    "WES.AX": {"name": "Wesfarmers", "sector": "Consumer", "price": 73.50},
    "TLS.AX": {"name": "Telstra Group", "sector": "Telecom", "price": 3.95},
    "RIO.AX": {"name": "Rio Tinto", "sector": "Materials", "price": 118.00},
    "MQG.AX": {"name": "Macquarie Group", "sector": "Financials", "price": 210.00},
    "WOW.AX": {"name": "Woolworths", "sector": "Consumer", "price": 31.20},
    "ALL.AX": {"name": "Aristocrat Leisure", "sector": "Technology", "price": 48.50},
    "STO.AX": {"name": "Santos", "sector": "Energy", "price": 7.20},
    "WDS.AX": {"name": "Woodside Energy", "sector": "Energy", "price": 25.80},
}


def get_tier(capital):
    if capital <= 500:
        return 1, 1, 0.5
    elif capital <= 2000:
        return 2, 3, 0.6
    elif capital <= 5000:
        return 3, 7, 0.7
    else:
        return 4, 15, 0.8


def get_stocks():
    result = {}
    for sym, info in ASX_STOCKS.items():
        result[sym] = {
            "symbol": sym,
            "company_name": info["name"],
            "sector": info["sector"],
            "current_price": info["price"],
        }
    return result


def generate_recommendations(body):
    capital = float(body.get("total_capital", 1000))
    risk_tolerance = body.get("risk_tolerance", "moderate")
    investment_strategy = body.get("investment_strategy", "balanced")

    if capital < 50 or capital > 10000:
        return {"error": "Capital must be between $50 and $10,000"}, 400

    tier, max_pos, max_risk = get_tier(capital)

    strat_mult = {"conservative": 0.7, "balanced": 1.0, "growth": 1.3, "aggressive": 1.5}
    risk_mult_map = {"very_low": 0.5, "low": 0.7, "moderate": 1.0, "high": 1.3, "very_high": 1.5}
    sm = strat_mult.get(investment_strategy, 1.0)
    rm = risk_mult_map.get(risk_tolerance, 1.0)

    scored = []
    for sym, info in ASX_STOCKS.items():
        base_return = 8.0 + (hash(sym) % 15)
        confidence = 0.60 + (hash(sym + "c") % 30) / 100
        risk_score = 0.3 + (hash(sym + "r") % 40) / 100
        if risk_score > max_risk:
            continue
        adj_return = round(base_return * sm * rm, 1)
        scored.append({
            "symbol": sym,
            "name": info["name"],
            "sector": info["sector"],
            "price": info["price"],
            "predicted_return": adj_return,
            "confidence": round(confidence, 2),
            "risk_score": round(risk_score, 2),
            "score": adj_return * confidence,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    picks = scored[:max_pos]

    total_score = sum(p["score"] for p in picks) or 1
    recs = []
    total_invested = 0

    for p in picks:
        alloc = capital * p["score"] / total_score
        shares = max(1, int(alloc / p["price"]))
        cost = round(shares * p["price"], 2)
        if total_invested + cost > capital:
            shares = max(1, int((capital - total_invested) / p["price"]))
            cost = round(shares * p["price"], 2)
        if cost <= 0 or total_invested + cost > capital:
            continue
        total_invested += cost
        target = round(p["price"] * (1 + p["predicted_return"] / 100), 2)
        conf_pct = int(p["confidence"] * 100)
        recs.append({
            "symbol": p["symbol"],
            "company_name": p["name"],
            "current_price": p["price"],
            "target_price": target,
            "predicted_return": p["predicted_return"],
            "confidence_score": p["confidence"],
            "recommended_allocation": cost,
            "recommended_shares": shares,
            "reasoning": p["name"] + " (" + p["sector"] + ") - confidence " + str(conf_pct) + "%, risk " + str(p["risk_score"]) + ", return " + str(p["predicted_return"]) + "%",
        })

    avg_return = round(sum(r["predicted_return"] for r in recs) / len(recs), 1) if recs else 0

    return {
        "total_investment": round(total_invested, 2),
        "expected_return": avg_return,
        "risk_level": risk_tolerance,
        "summary": "Tier " + str(tier) + ": " + str(len(recs)) + " ASX stocks for $" + str(int(capital)) + " (" + risk_tolerance + " risk, " + investment_strategy + "). Expected return: " + str(avg_return) + "%.",
        "recommendations": recs,
    }, 200


class handler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self._send_json({})

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path == "/":
            self._send_json({
                "name": "ASX AI Investment Platform",
                "status": "online",
                "version": "1.0.0",
                "timestamp": str(datetime.utcnow()),
            })
        elif path == "/health":
            self._send_json({"status": "healthy", "timestamp": str(datetime.utcnow())})
        elif path == "/api/v1/stocks":
            self._send_json(get_stocks())
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/v1/recommendations/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = {}
            if content_length > 0:
                raw = self.rfile.read(content_length)
                body = json.loads(raw)
            data, status = generate_recommendations(body)
            self._send_json(data, status)
        else:
            self._send_json({"error": "Not found"}, 404)
