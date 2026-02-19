from http.server import BaseHTTPRequestHandler
import json
import math
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs


ASX_STOCKS = {
    'CBA.AX': {'name': 'Commonwealth Bank', 'sector': 'Financials', 'price': 118.5},
    'BHP.AX': {'name': 'BHP Group', 'sector': 'Materials', 'price': 44.2},
    'CSL.AX': {'name': 'CSL Limited', 'sector': 'Healthcare', 'price': 285.0},
    'NAB.AX': {'name': 'National Australia Bank', 'sector': 'Financials', 'price': 37.8},
    'WBC.AX': {'name': 'Westpac Banking', 'sector': 'Financials', 'price': 28.5},
    'ANZ.AX': {'name': 'ANZ Group', 'sector': 'Financials', 'price': 29.2},
    'FMG.AX': {'name': 'Fortescue Metals', 'sector': 'Materials', 'price': 19.8},
    'WES.AX': {'name': 'Wesfarmers', 'sector': 'Consumer', 'price': 73.5},
    'TLS.AX': {'name': 'Telstra Group', 'sector': 'Telecom', 'price': 3.95},
    'RIO.AX': {'name': 'Rio Tinto', 'sector': 'Materials', 'price': 118.0},
    'MQG.AX': {'name': 'Macquarie Group', 'sector': 'Financials', 'price': 210.0},
    'WOW.AX': {'name': 'Woolworths', 'sector': 'Consumer', 'price': 31.2},
    'ALL.AX': {'name': 'Aristocrat Leisure', 'sector': 'Technology', 'price': 48.5},
    'STO.AX': {'name': 'Santos', 'sector': 'Energy', 'price': 7.2},
    'WDS.AX': {'name': 'Woodside Energy', 'sector': 'Energy', 'price': 25.8},
    'REA.AX': {'name': 'REA Group', 'sector': 'Technology', 'price': 195.0},
    'TCL.AX': {'name': 'Transurban Group', 'sector': 'Infrastructure', 'price': 13.2},
    'GMG.AX': {'name': 'Goodman Group', 'sector': 'Real Estate', 'price': 33.8},
    'COL.AX': {'name': 'Coles Group', 'sector': 'Consumer', 'price': 18.5},
    'QBE.AX': {'name': 'QBE Insurance', 'sector': 'Financials', 'price': 18.0},
    'SHL.AX': {'name': 'Sonic Healthcare', 'sector': 'Healthcare', 'price': 25.5},
    'AMC.AX': {'name': 'Amcor', 'sector': 'Materials', 'price': 14.8},
    'ORG.AX': {'name': 'Origin Energy', 'sector': 'Energy', 'price': 11.2},
    'MIN.AX': {'name': 'Mineral Resources', 'sector': 'Materials', 'price': 38.0},
    'JHX.AX': {'name': 'James Hardie', 'sector': 'Materials', 'price': 52.0},
    'SEK.AX': {'name': 'Seek Limited', 'sector': 'Technology', 'price': 22.5},
    'CPU.AX': {'name': 'Computershare', 'sector': 'Technology', 'price': 28.0},
    'IAG.AX': {'name': 'Insurance Australia', 'sector': 'Financials', 'price': 7.8},
    'ASX.AX': {'name': 'ASX Limited', 'sector': 'Financials', 'price': 65.0},
    'NCM.AX': {'name': 'Newcrest Mining', 'sector': 'Materials', 'price': 26.5},
    'AGL.AX': {'name': 'AGL Energy', 'sector': 'Energy', 'price': 11.8},
    'S32.AX': {'name': 'South32', 'sector': 'Materials', 'price': 3.45},
    'XRO.AX': {'name': 'Xero Limited', 'sector': 'Technology', 'price': 128.0},
    'WTC.AX': {'name': 'WiseTech Global', 'sector': 'Technology', 'price': 85.0},
    'APX.AX': {'name': 'Appen Limited', 'sector': 'Technology', 'price': 1.85},
    'ZIP.AX': {'name': 'Zip Co', 'sector': 'Financials', 'price': 1.25},
    'LYC.AX': {'name': 'Lynas Rare Earths', 'sector': 'Materials', 'price': 6.8},
    'PLS.AX': {'name': 'Pilbara Minerals', 'sector': 'Materials', 'price': 3.2},
    'AZJ.AX': {'name': 'Aurizon Holdings', 'sector': 'Infrastructure', 'price': 3.75},
    'TWE.AX': {'name': 'Treasury Wine Estates', 'sector': 'Consumer', 'price': 11.5},
    'IEL.AX': {'name': 'IDP Education', 'sector': 'Education', 'price': 17.0},
    'RMD.AX': {'name': 'ResMed', 'sector': 'Healthcare', 'price': 35.5},
    'MPL.AX': {'name': 'Medibank Private', 'sector': 'Healthcare', 'price': 3.9},
    'ORI.AX': {'name': 'Orica Limited', 'sector': 'Materials', 'price': 17.5},
    'BXB.AX': {'name': 'Brambles', 'sector': 'Logistics', 'price': 14.2},
    'SCG.AX': {'name': 'Scentre Group', 'sector': 'Real Estate', 'price': 3.15},
    'DXS.AX': {'name': 'Dexus', 'sector': 'Real Estate', 'price': 7.5},
    'SGP.AX': {'name': 'Stockland', 'sector': 'Real Estate', 'price': 4.8},
    'EVN.AX': {'name': 'Evolution Mining', 'sector': 'Materials', 'price': 3.9},
    'NST.AX': {'name': 'Northern Star', 'sector': 'Materials', 'price': 12.5},
}


RANGE_DAYS = {'1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '5Y': 1825}


def _seed(s):
    return abs(hash(s)) % 2147483647


def _pseudo_random(seed, i):
    v = ((seed + i * 2654435761) ^ (seed >> 16)) & 0xFFFFFFFF
    return (v % 10000) / 10000.0


def generate_history(symbol, range_key):
    if symbol not in ASX_STOCKS:
        return None
    info = ASX_STOCKS[symbol]
    current = info['price']
    days = RANGE_DAYS.get(range_key, 30)
    seed = _seed(symbol + range_key)

    drift_pct = {'1W': -2, '1M': -5, '3M': -8, '6M': -12, '1Y': -18, '5Y': -40}
    drift = drift_pct.get(range_key, -5)
    start_price = current * (1 + drift / 100)

    vol = 0.015 if days <= 30 else 0.012 if days <= 180 else 0.01
    points = min(days, 250) if days > 60 else days
    step = max(1, days // points)

    prices = []
    today = datetime.utcnow().date()
    p = start_price

    for i in range(points):
        d = today - timedelta(days=days - i * step)
        r = _pseudo_random(seed, i)
        trend = (current - start_price) / points
        noise = (r - 0.48) * current * vol
        cycle = math.sin(i * 0.15 + seed % 7) * current * vol * 0.5
        p = p + trend + noise + cycle
        p = max(p, current * 0.3)

        high = p * (1 + _pseudo_random(seed + 1000, i) * 0.02)
        low = p * (1 - _pseudo_random(seed + 2000, i) * 0.02)
        vol_day = int(500000 + _pseudo_random(seed + 3000, i) * 9500000)

        prices.append({
            'date': d.strftime('%Y-%m-%d'),
            'open': round(p * (1 + (_pseudo_random(seed + 4000, i) - 0.5) * 0.005), 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(p, 2),
            'volume': vol_day,
        })

    prices[-1]['close'] = current

    closes = [pt['close'] for pt in prices]
    period_return = round((current - closes[0]) / closes[0] * 100, 2)
    high_price = max(pt['high'] for pt in prices)
    low_price = min(pt['low'] for pt in prices)
    avg_price = round(sum(closes) / len(closes), 2)
    avg_vol = int(sum(pt['volume'] for pt in prices) / len(prices))

    return {
        'symbol': symbol,
        'company_name': info['name'],
        'sector': info['sector'],
        'range': range_key,
        'current_price': current,
        'period_start_price': round(closes[0], 2),
        'period_return_pct': period_return,
        'period_high': round(high_price, 2),
        'period_low': round(low_price, 2),
        'average_price': avg_price,
        'average_volume': avg_vol,
        'data_points': len(prices),
        'prices': prices,
    }


def search_stocks(query):
    query = query.strip().upper()
    if not query:
        return []
    results = []
    for sym, info in ASX_STOCKS.items():
        ticker = sym.replace('.AX', '')
        name_upper = info['name'].upper()
        sector_upper = info['sector'].upper()
        if query in ticker or query in name_upper or query in sector_upper:
            score = 0
            if ticker == query:
                score = 100
            elif ticker.startswith(query):
                score = 80
            elif query in ticker:
                score = 60
            elif name_upper.startswith(query):
                score = 50
            elif query in name_upper:
                score = 40
            elif query in sector_upper:
                score = 20
            results.append({
                'symbol': sym,
                'company_name': info['name'],
                'sector': info['sector'],
                'current_price': info['price'],
                'match_score': score,
            })
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return results


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
            'symbol': sym,
            'company_name': info['name'],
            'sector': info['sector'],
            'current_price': info['price'],
        }
    return result


def generate_recommendations(body):
    capital = float(body.get('total_capital', 1000))
    risk_tolerance = body.get('risk_tolerance', 'moderate')
    investment_strategy = body.get('investment_strategy', 'balanced')

    if capital < 50 or capital > 10000:
        return {'error': 'Capital must be between  and ,000'}, 400

    tier, max_pos, max_risk = get_tier(capital)

    strat_mult = {'conservative': 0.7, 'balanced': 1.0, 'growth': 1.3, 'aggressive': 1.5}
    risk_mult_map = {'very_low': 0.5, 'low': 0.7, 'moderate': 1.0, 'high': 1.3, 'very_high': 1.5}
    sm = strat_mult.get(investment_strategy, 1.0)
    rm = risk_mult_map.get(risk_tolerance, 1.0)

    scored = []
    for sym, info in ASX_STOCKS.items():
        base_return = 8.0 + (hash(sym) % 15)
        confidence = 0.60 + (hash(sym + 'c') % 30) / 100
        risk_score = 0.3 + (hash(sym + 'r') % 40) / 100
        if risk_score > max_risk:
            continue
        adj_return = round(base_return * sm * rm, 1)
        scored.append({
            'symbol': sym,
            'name': info['name'],
            'sector': info['sector'],
            'price': info['price'],
            'predicted_return': adj_return,
            'confidence': round(confidence, 2),
            'risk_score': round(risk_score, 2),
            'score': adj_return * confidence,
        })

    scored.sort(key=lambda x: x['score'], reverse=True)
    picks = scored[:max_pos]

    total_score = sum(p['score'] for p in picks) or 1
    recs = []
    total_invested = 0

    for p in picks:
        alloc = capital * p['score'] / total_score
        shares = max(1, int(alloc / p['price']))
        cost = round(shares * p['price'], 2)
        if total_invested + cost > capital:
            shares = max(1, int((capital - total_invested) / p['price']))
            cost = round(shares * p['price'], 2)
        if cost <= 0 or total_invested + cost > capital:
            continue
        total_invested += cost
        target = round(p['price'] * (1 + p['predicted_return'] / 100), 2)
        conf_pct = int(p['confidence'] * 100)
        recs.append({
            'symbol': p['symbol'],
            'company_name': p['name'],
            'current_price': p['price'],
            'target_price': target,
            'predicted_return': p['predicted_return'],
            'confidence_score': p['confidence'],
            'recommended_allocation': cost,
            'recommended_shares': shares,
            'reasoning': p['name'] + ' (' + p['sector'] + ') - confidence ' + str(conf_pct) + '%, risk ' + str(p['risk_score']) + ', return ' + str(p['predicted_return']) + '%',
        })

    avg_return = round(sum(r['predicted_return'] for r in recs) / len(recs), 1) if recs else 0

    return {
        'total_investment': round(total_invested, 2),
        'expected_return': avg_return,
        'risk_level': risk_tolerance,
        'summary': 'Tier ' + str(tier) + ': ' + str(len(recs)) + ' ASX stocks for $' + str(int(capital)) + ' (' + risk_tolerance + ' risk, ' + investment_strategy + '). Expected return: ' + str(avg_return) + '%.',
        'recommendations': recs,
    }, 200


class handler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self._send_json({})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'
        params = parse_qs(parsed.query)

        if path == '/':
            self._send_json({
                'name': 'ASX AI Investment Platform',
                'status': 'online',
                'version': '1.2.0',
                'timestamp': str(datetime.utcnow()),
            })
        elif path == '/health':
            self._send_json({'status': 'healthy', 'timestamp': str(datetime.utcnow())})
        elif path == '/api/v1/stocks':
            self._send_json(get_stocks())
        elif path == '/api/v1/stocks/search':
            q = params.get('q', [''])[0]
            results = search_stocks(q)
            self._send_json({'query': q, 'count': len(results), 'results': results})
        elif path.startswith('/api/v1/stocks/') and path.count('/') == 4:
            symbol = path.split('/')[-1]
            if not symbol.endswith('.AX'):
                symbol = symbol + '.AX'
            range_key = params.get('range', ['1M'])[0]
            if range_key not in RANGE_DAYS:
                range_key = '1M'
            data = generate_history(symbol, range_key)
            if data:
                self._send_json(data)
            else:
                self._send_json({'error': 'Stock not found'}, 404)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/')

        if path == '/api/v1/recommendations/generate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = {}
            if content_length > 0:
                raw = self.rfile.read(content_length)
                body = json.loads(raw)
            data, status = generate_recommendations(body)
            self._send_json(data, status)
        else:
            self._send_json({'error': 'Not found'}, 404)
