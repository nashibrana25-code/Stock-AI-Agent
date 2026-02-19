from http.server import BaseHTTPRequestHandler
import json
import urllib.request
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import ssl
import time
import os
from concurrent.futures import ThreadPoolExecutor

# ============================================================
# AI MODEL CONFIG (Groq - Llama 3.3 70B, free tier)
# ============================================================
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '').strip()
GROQ_MODEL = 'llama-3.3-70b-versatile'
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
AI_CACHE_TTL = 900  # 15 min cache for AI analysis (save rate limits)
_ai_cache = {}


def _call_ai(prompt, max_tokens=300):
    """Call Groq AI API and return the response text."""
    if not GROQ_API_KEY:
        return None
    body = json.dumps({
        'model': GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': 'You are an expert ASX stock market analyst. Always respond with valid JSON only, no markdown, no code fences.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3,
        'max_tokens': max_tokens,
    }).encode()
    req = urllib.request.Request(GROQ_URL, data=body, headers={
        'Authorization': 'Bearer ' + GROQ_API_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    try:
        resp = urllib.request.urlopen(req, timeout=8, context=_ssl_ctx)
        data = json.loads(resp.read())
        text = data['choices'][0]['message']['content'].strip()
        # Strip markdown code fences if present
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
        text = text.strip()
        return text
    except urllib.error.HTTPError as e:
        _ai_cache['_last_error'] = (time.time(), 'HTTP ' + str(e.code) + ': ' + str(e.read()[:200]))
        return None
    except Exception as e:
        _ai_cache['_last_error'] = (time.time(), str(type(e).__name__) + ': ' + str(e))
        return None


def _get_ai_cached(key, fetcher):
    """Cache AI responses for 15 minutes."""
    now = time.time()
    if key in _ai_cache:
        ts, data = _ai_cache[key]
        if now - ts < AI_CACHE_TTL:
            return data
    data = fetcher()
    if data is not None:
        _ai_cache[key] = (now, data)
    return data


def ai_analyze_stock(symbol, quote_data):
    """Get AI-powered analysis for a single stock using real market data."""
    if not GROQ_API_KEY or not quote_data or not quote_data.get('price'):
        return None

    def _fetch():
        info = ASX_STOCKS.get(symbol, {})
        price = quote_data['price']
        prev = quote_data.get('previous_close', price)
        w52h = quote_data.get('fifty_two_week_high', price)
        w52l = quote_data.get('fifty_two_week_low', price)
        vol = quote_data.get('volume', 0)
        change = round((price - prev) / prev * 100, 2) if prev else 0

        prompt = (
            'Analyze ' + symbol + ' (' + (info.get('name', symbol)) + ', ' + info.get('sector', 'Unknown') + ' sector) for ASX investment.\n'
            'LIVE DATA: Price=$' + str(round(price, 2)) + ', Previous Close=$' + str(round(prev, 2)) +
            ', Daily Change=' + str(change) + '%, Volume=' + str(vol) +
            ', 52-Week High=$' + str(round(w52h, 2)) + ', 52-Week Low=$' + str(round(w52l, 2)) + '.\n'
            'Reply with ONLY this JSON (no other text):\n'
            '{"sentiment":"bullish/neutral/bearish",'
            '"confidence":0.0-1.0,'
            '"target_price":number,'
            '"risk_level":"low/medium/high",'
            '"key_factors":["factor1","factor2","factor3"],'
            '"summary":"2-3 sentence analysis",'
            '"recommendation":"strong_buy/buy/hold/sell/strong_sell"}'
        )
        text = _call_ai(prompt, max_tokens=250)
        if not text:
            return None
        try:
            result = json.loads(text)
            result['ai_model'] = GROQ_MODEL
            result['analyzed_at'] = str(datetime.utcnow())
            return result
        except Exception:
            return None

    return _get_ai_cached('ai_' + symbol, _fetch)


def ai_market_summary(stocks_data):
    """Get AI-powered market summary for all stocks."""
    if not GROQ_API_KEY:
        return None

    def _fetch():
        # Build compact market snapshot for the prompt
        gainers = []
        losers = []
        for sym, entry in stocks_data.items():
            if not entry or entry.get('current_price', 0) == 0:
                continue
            chg = entry.get('change_pct', 0)
            name = sym.replace('.AX', '')
            if chg > 0:
                gainers.append((name, chg))
            elif chg < 0:
                losers.append((name, chg))
        gainers.sort(key=lambda x: x[1], reverse=True)
        losers.sort(key=lambda x: x[1])

        top5_gain = ', '.join([g[0] + ' +' + str(g[1]) + '%' for g in gainers[:5]])
        top5_loss = ', '.join([l[0] + ' ' + str(l[1]) + '%' for l in losers[:5]])
        total = len(stocks_data)
        green = len(gainers)
        red = len(losers)

        prompt = (
            'Provide ASX market summary. ' + str(total) + ' stocks tracked: ' +
            str(green) + ' up, ' + str(red) + ' down.\n'
            'Top gainers: ' + top5_gain + '\n'
            'Top losers: ' + top5_loss + '\n'
            'Reply with ONLY this JSON:\n'
            '{"market_mood":"bullish/neutral/bearish",'
            '"mood_score":0.0-1.0,'
            '"headline":"one catchy headline",'
            '"summary":"3-4 sentence market analysis",'
            '"sectors_to_watch":["sector1","sector2"],'
            '"outlook":"positive/mixed/negative"}'
        )
        text = _call_ai(prompt, max_tokens=250)
        if not text:
            return None
        try:
            result = json.loads(text)
            result['ai_model'] = GROQ_MODEL
            result['analyzed_at'] = str(datetime.utcnow())
            result['stocks_analyzed'] = total
            return result
        except Exception:
            return None

    return _get_ai_cached('ai_market_summary', _fetch)


# ============================================================
# ASX STOCK UNIVERSE - tickers and sectors (prices fetched LIVE)
# ============================================================
ASX_STOCKS = {
    'CBA.AX': {'name': 'Commonwealth Bank', 'sector': 'Financials'},
    'BHP.AX': {'name': 'BHP Group', 'sector': 'Materials'},
    'CSL.AX': {'name': 'CSL Limited', 'sector': 'Healthcare'},
    'NAB.AX': {'name': 'National Australia Bank', 'sector': 'Financials'},
    'WBC.AX': {'name': 'Westpac Banking', 'sector': 'Financials'},
    'ANZ.AX': {'name': 'ANZ Group', 'sector': 'Financials'},
    'FMG.AX': {'name': 'Fortescue Metals', 'sector': 'Materials'},
    'WES.AX': {'name': 'Wesfarmers', 'sector': 'Consumer'},
    'TLS.AX': {'name': 'Telstra Group', 'sector': 'Telecom'},
    'RIO.AX': {'name': 'Rio Tinto', 'sector': 'Materials'},
    'MQG.AX': {'name': 'Macquarie Group', 'sector': 'Financials'},
    'WOW.AX': {'name': 'Woolworths', 'sector': 'Consumer'},
    'ALL.AX': {'name': 'Aristocrat Leisure', 'sector': 'Technology'},
    'STO.AX': {'name': 'Santos', 'sector': 'Energy'},
    'WDS.AX': {'name': 'Woodside Energy', 'sector': 'Energy'},
    'REA.AX': {'name': 'REA Group', 'sector': 'Technology'},
    'TCL.AX': {'name': 'Transurban Group', 'sector': 'Infrastructure'},
    'GMG.AX': {'name': 'Goodman Group', 'sector': 'Real Estate'},
    'COL.AX': {'name': 'Coles Group', 'sector': 'Consumer'},
    'QBE.AX': {'name': 'QBE Insurance', 'sector': 'Financials'},
    'SHL.AX': {'name': 'Sonic Healthcare', 'sector': 'Healthcare'},
    'AMC.AX': {'name': 'Amcor', 'sector': 'Materials'},
    'ORG.AX': {'name': 'Origin Energy', 'sector': 'Energy'},
    'MIN.AX': {'name': 'Mineral Resources', 'sector': 'Materials'},
    'JHX.AX': {'name': 'James Hardie', 'sector': 'Materials'},
    'SEK.AX': {'name': 'Seek Limited', 'sector': 'Technology'},
    'CPU.AX': {'name': 'Computershare', 'sector': 'Technology'},
    'IAG.AX': {'name': 'Insurance Australia', 'sector': 'Financials'},
    'ASX.AX': {'name': 'ASX Limited', 'sector': 'Financials'},
    'NCM.AX': {'name': 'Newcrest Mining', 'sector': 'Materials'},
    'AGL.AX': {'name': 'AGL Energy', 'sector': 'Energy'},
    'S32.AX': {'name': 'South32', 'sector': 'Materials'},
    'XRO.AX': {'name': 'Xero Limited', 'sector': 'Technology'},
    'WTC.AX': {'name': 'WiseTech Global', 'sector': 'Technology'},
    'APX.AX': {'name': 'Appen Limited', 'sector': 'Technology'},
    'ZIP.AX': {'name': 'Zip Co', 'sector': 'Financials'},
    'LYC.AX': {'name': 'Lynas Rare Earths', 'sector': 'Materials'},
    'PLS.AX': {'name': 'Pilbara Minerals', 'sector': 'Materials'},
    'AZJ.AX': {'name': 'Aurizon Holdings', 'sector': 'Infrastructure'},
    'TWE.AX': {'name': 'Treasury Wine Estates', 'sector': 'Consumer'},
    'IEL.AX': {'name': 'IDP Education', 'sector': 'Education'},
    'RMD.AX': {'name': 'ResMed', 'sector': 'Healthcare'},
    'MPL.AX': {'name': 'Medibank Private', 'sector': 'Healthcare'},
    'ORI.AX': {'name': 'Orica Limited', 'sector': 'Materials'},
    'BXB.AX': {'name': 'Brambles', 'sector': 'Logistics'},
    'SCG.AX': {'name': 'Scentre Group', 'sector': 'Real Estate'},
    'DXS.AX': {'name': 'Dexus', 'sector': 'Real Estate'},
    'SGP.AX': {'name': 'Stockland', 'sector': 'Real Estate'},
    'EVN.AX': {'name': 'Evolution Mining', 'sector': 'Materials'},
    'NST.AX': {'name': 'Northern Star', 'sector': 'Materials'},
}

# Yahoo Finance range mapping: our_key -> (yf_range, yf_interval)
RANGE_MAP = {
    '1W': ('5d', '1d'),
    '1M': ('1mo', '1d'),
    '3M': ('3mo', '1d'),
    '6M': ('6mo', '1d'),
    '1Y': ('1y', '1d'),
    '5Y': ('5y', '1wk'),
}

# In-memory cache: {cache_key: (timestamp, data)}
_cache = {}
CACHE_TTL = 300  # 5 minutes

# SSL context for urllib
_ssl_ctx = ssl.create_default_context()


def _yahoo_fetch(url):
    """Fetch JSON from Yahoo Finance API."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    try:
        resp = urllib.request.urlopen(req, timeout=8, context=_ssl_ctx)
        return json.loads(resp.read())
    except Exception:
        return None


def _get_cached(key, fetcher):
    """Simple TTL cache."""
    now = time.time()
    if key in _cache:
        ts, data = _cache[key]
        if now - ts < CACHE_TTL:
            return data
    data = fetcher()
    if data is not None:
        _cache[key] = (now, data)
    return data


def _parse_chart_meta(raw):
    """Parse Yahoo Finance chart API response into a clean quote dict."""
    if not raw or 'chart' not in raw:
        return None
    results = raw['chart'].get('result')
    if not results:
        return None
    meta = results[0]['meta']
    return {
        'price': meta.get('regularMarketPrice'),
        'previous_close': meta.get('chartPreviousClose'),
        'day_high': meta.get('regularMarketDayHigh'),
        'day_low': meta.get('regularMarketDayLow'),
        'volume': meta.get('regularMarketVolume'),
        'fifty_two_week_high': meta.get('fiftyTwoWeekHigh'),
        'fifty_two_week_low': meta.get('fiftyTwoWeekLow'),
        'long_name': meta.get('longName') or meta.get('shortName', ''),
        'currency': meta.get('currency', 'AUD'),
    }


def fetch_live_quote(symbol):
    """Fetch real-time quote for a single ASX stock."""
    def _fetch():
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?range=5d&interval=1d'
        return _parse_chart_meta(_yahoo_fetch(url))
    return _get_cached('quote_' + symbol, _fetch)


def _fetch_quote_for_batch(symbol):
    """Fetch a single quote (used in parallel batch fetching)."""
    cache_key = 'quote_' + symbol
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL:
            return symbol, data
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?range=5d&interval=1d'
    raw = _yahoo_fetch(url)
    quote = _parse_chart_meta(raw)
    if quote is not None:
        _cache[cache_key] = (now, quote)
    return symbol, quote


def fetch_all_quotes():
    """Fetch live quotes for ALL stocks in parallel."""
    symbols = list(ASX_STOCKS.keys())
    results = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = list(executor.map(_fetch_quote_for_batch, symbols))
    for sym, quote in futures:
        results[sym] = quote
    return results


def fetch_live_history(symbol, range_key):
    """Fetch real OHLCV history from Yahoo Finance."""
    yf_range, yf_interval = RANGE_MAP.get(range_key, ('1mo', '1d'))

    def _fetch():
        url = ('https://query1.finance.yahoo.com/v8/finance/chart/' + symbol +
               '?range=' + yf_range + '&interval=' + yf_interval)
        raw = _yahoo_fetch(url)
        if not raw or 'chart' not in raw:
            return None
        results = raw['chart'].get('result')
        if not results:
            return None
        result = results[0]
        meta = result['meta']
        timestamps = result.get('timestamp', [])
        quotes = result.get('indicators', {}).get('quote', [{}])[0]
        if not timestamps:
            return None

        prices = []
        for i, ts in enumerate(timestamps):
            o = quotes.get('open', [None] * len(timestamps))[i]
            h = quotes.get('high', [None] * len(timestamps))[i]
            low_val = quotes.get('low', [None] * len(timestamps))[i]
            c = quotes.get('close', [None] * len(timestamps))[i]
            v = quotes.get('volume', [None] * len(timestamps))[i]
            if c is None:
                continue
            dt = datetime.utcfromtimestamp(ts)
            prices.append({
                'date': dt.strftime('%Y-%m-%d'),
                'open': round(o, 2) if o else round(c, 2),
                'high': round(h, 2) if h else round(c, 2),
                'low': round(low_val, 2) if low_val else round(c, 2),
                'close': round(c, 2),
                'volume': int(v) if v else 0,
            })

        if not prices:
            return None

        current = meta.get('regularMarketPrice', prices[-1]['close'])
        closes = [p['close'] for p in prices]
        period_return = round((current - closes[0]) / closes[0] * 100, 2) if closes[0] else 0
        high_price = max(p['high'] for p in prices)
        low_price = min(p['low'] for p in prices)
        avg_price = round(sum(closes) / len(closes), 2)
        avg_vol = int(sum(p['volume'] for p in prices) / len(prices)) if prices else 0

        return {
            'symbol': symbol,
            'company_name': meta.get('longName') or meta.get('shortName', symbol),
            'sector': ASX_STOCKS.get(symbol, {}).get('sector', 'Unknown'),
            'range': range_key,
            'current_price': round(current, 2),
            'period_start_price': round(closes[0], 2),
            'period_return_pct': period_return,
            'period_high': round(high_price, 2),
            'period_low': round(low_price, 2),
            'average_price': avg_price,
            'average_volume': avg_vol,
            'data_points': len(prices),
            'prices': prices,
            'data_source': 'yahoo_finance',
            'last_updated': str(datetime.utcnow()),
        }

    return _get_cached('hist_' + symbol + '_' + range_key, _fetch)


def _build_stock_entry(sym, info, quote):
    """Build a stock entry dict from symbol info and live quote data."""
    if quote and quote.get('price'):
        price = quote['price']
        prev = quote.get('previous_close', price)
        change_pct = round((price - prev) / prev * 100, 2) if prev else 0
        return {
            'symbol': sym,
            'company_name': quote.get('long_name') or info['name'],
            'sector': info['sector'],
            'current_price': round(price, 2),
            'previous_close': round(prev, 2),
            'day_high': round(quote.get('day_high', 0), 2),
            'day_low': round(quote.get('day_low', 0), 2),
            'volume': quote.get('volume', 0),
            'fifty_two_week_high': round(quote.get('fifty_two_week_high', 0), 2),
            'fifty_two_week_low': round(quote.get('fifty_two_week_low', 0), 2),
            'change_pct': change_pct,
            'data_source': 'yahoo_finance',
        }
    else:
        return {
            'symbol': sym,
            'company_name': info['name'],
            'sector': info['sector'],
            'current_price': 0,
            'data_source': 'unavailable',
        }


def get_stocks():
    """Get all stocks with live prices (fetched in parallel)."""
    all_quotes = fetch_all_quotes()
    result = {}
    for sym, info in ASX_STOCKS.items():
        quote = all_quotes.get(sym)
        result[sym] = _build_stock_entry(sym, info, quote)
    return result


def search_stocks(query):
    """Search stocks with live price data."""
    query = query.strip().upper()
    if not query:
        return []

    matching = []
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
            matching.append((sym, info, score))

    if not matching:
        return []

    match_syms = [m[0] for m in matching]
    quotes = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = list(executor.map(_fetch_quote_for_batch, match_syms))
    for sym, quote in futures:
        quotes[sym] = quote

    results = []
    for sym, info, score in matching:
        quote = quotes.get(sym)
        price = round(quote['price'], 2) if quote and quote.get('price') else 0
        prev_close = quote.get('previous_close', 0) if quote else 0
        change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0

        results.append({
            'symbol': sym,
            'company_name': quote.get('long_name', info['name']) if quote else info['name'],
            'sector': info['sector'],
            'current_price': price,
            'previous_close': round(prev_close, 2) if prev_close else 0,
            'change_pct': change_pct,
            'volume': quote.get('volume', 0) if quote else 0,
            'fifty_two_week_high': round(quote.get('fifty_two_week_high', 0), 2) if quote else 0,
            'fifty_two_week_low': round(quote.get('fifty_two_week_low', 0), 2) if quote else 0,
            'match_score': score,
            'data_source': 'yahoo_finance' if quote else 'unavailable',
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


def generate_recommendations(body):
    """Generate recommendations using LIVE Yahoo Finance data."""
    capital = float(body.get('total_capital', 1000))
    risk_tolerance = body.get('risk_tolerance', 'moderate')
    investment_strategy = body.get('investment_strategy', 'balanced')

    if capital < 50 or capital > 10000:
        return {'error': 'Capital must be between $50 and $10,000'}, 400

    tier, max_pos, max_risk = get_tier(capital)

    strat_mult = {'conservative': 0.7, 'balanced': 1.0, 'growth': 1.3, 'aggressive': 1.5}
    risk_mult_map = {'very_low': 0.5, 'low': 0.7, 'moderate': 1.0, 'high': 1.3, 'very_high': 1.5}
    sm = strat_mult.get(investment_strategy, 1.0)
    rm = risk_mult_map.get(risk_tolerance, 1.0)

    all_quotes = fetch_all_quotes()

    scored = []
    for sym, info in ASX_STOCKS.items():
        quote = all_quotes.get(sym)
        if not quote or not quote.get('price'):
            continue

        price = quote['price']
        prev = quote.get('previous_close', price)
        w52_high = quote.get('fifty_two_week_high', price)
        w52_low = quote.get('fifty_two_week_low', price)

        daily_change = (price - prev) / prev * 100 if prev else 0
        from_52w_high = (w52_high - price) / w52_high * 100 if w52_high else 0

        base_return = 5.0 + from_52w_high * 0.3 + daily_change * 0.5
        base_return = max(2.0, min(base_return, 25.0))

        range_width = w52_high - w52_low if w52_high > w52_low else 1
        position_in_range = (price - w52_low) / range_width if range_width else 0.5
        confidence = 0.55 + (1 - position_in_range) * 0.35

        risk_score = 0.2 + position_in_range * 0.5 + abs(daily_change) * 0.02
        risk_score = min(risk_score, 0.95)

        if risk_score > max_risk:
            continue

        adj_return = round(base_return * sm * rm, 1)
        scored.append({
            'symbol': sym,
            'name': quote.get('long_name') or info['name'],
            'sector': info['sector'],
            'price': round(price, 2),
            'predicted_return': adj_return,
            'confidence': round(confidence, 2),
            'risk_score': round(risk_score, 2),
            'score': adj_return * confidence,
            'daily_change': round(daily_change, 2),
            'volume': quote.get('volume', 0),
            'fifty_two_week_high': round(w52_high, 2),
            'fifty_two_week_low': round(w52_low, 2),
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
            'daily_change_pct': p['daily_change'],
            'volume': p['volume'],
            'fifty_two_week_high': p['fifty_two_week_high'],
            'fifty_two_week_low': p['fifty_two_week_low'],
            'reasoning': p['name'] + ' (' + p['sector'] + ') - Live $' + str(p['price']) + ', confidence ' + str(conf_pct) + '%, risk ' + str(p['risk_score']) + ', return ' + str(p['predicted_return']) + '%',
            'data_source': 'yahoo_finance',
        })

    avg_return = round(sum(r['predicted_return'] for r in recs) / len(recs), 1) if recs else 0

    # Generate AI portfolio summary if available
    ai_summary = None
    if GROQ_API_KEY and recs:
        picks_text = ', '.join([r['symbol'].replace('.AX', '') + ' $' + str(r['current_price']) for r in recs])
        prompt = (
            'Portfolio recommendation for $' + str(int(capital)) + ' capital, ' + risk_tolerance + ' risk, ' + investment_strategy + ' strategy.\n'
            'Picks: ' + picks_text + '. Expected return: ' + str(avg_return) + '%.\n'
            'Reply ONLY valid JSON:\n'
            '{"portfolio_rating":"excellent/good/fair/poor",'
            '"reasoning":"2-3 sentences explaining why these picks work together",'
            '"risk_assessment":"1 sentence on portfolio risk",'
            '"tip":"1 actionable tip for this investor"}'
        )
        ai_text = _call_ai(prompt, max_tokens=200)
        if ai_text:
            try:
                ai_summary = json.loads(ai_text)
                ai_summary['ai_model'] = GROQ_MODEL
            except Exception:
                pass

    return {
        'total_investment': round(total_invested, 2),
        'expected_return': avg_return,
        'risk_level': risk_tolerance,
        'summary': 'Tier ' + str(tier) + ': ' + str(len(recs)) + ' ASX stocks for $' + str(int(capital)) + ' (' + risk_tolerance + ' risk, ' + investment_strategy + '). Expected return: ' + str(avg_return) + '%. Prices are LIVE from Yahoo Finance.',
        'ai_portfolio_analysis': ai_summary,
        'recommendations': recs,
        'data_source': 'yahoo_finance',
        'ai_enabled': bool(GROQ_API_KEY),
        'generated_at': str(datetime.utcnow()),
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
                'version': '3.0.0',
                'data_source': 'yahoo_finance (real-time)',
                'ai_model': GROQ_MODEL if GROQ_API_KEY else 'none',
                'ai_enabled': bool(GROQ_API_KEY),
                'timestamp': str(datetime.utcnow()),
            })
        elif path == '/health':
            self._send_json({
                'status': 'healthy',
                'data_source': 'yahoo_finance',
                'ai_enabled': bool(GROQ_API_KEY),
                'ai_model': GROQ_MODEL if GROQ_API_KEY else 'none',
                'timestamp': str(datetime.utcnow()),
            })
        elif path == '/api/v1/stocks':
            self._send_json(get_stocks())
        elif path == '/api/v1/stocks/search':
            q = params.get('q', [''])[0]
            results = search_stocks(q)
            self._send_json({
                'query': q,
                'count': len(results),
                'results': results,
                'data_source': 'yahoo_finance',
            })
        elif path.startswith('/api/v1/stocks/') and path.count('/') == 4:
            symbol = path.split('/')[-1]
            if not symbol.endswith('.AX'):
                symbol = symbol + '.AX'
            range_key = params.get('range', ['1M'])[0]
            if range_key not in RANGE_MAP:
                range_key = '1M'
            data = fetch_live_history(symbol, range_key)
            if data:
                self._send_json(data)
            else:
                self._send_json({'error': 'Stock not found or Yahoo Finance unavailable'}, 404)
        elif path == '/api/v1/ai/analyze' and params.get('symbol'):
            symbol = params.get('symbol', [''])[0]
            if not symbol.endswith('.AX'):
                symbol = symbol + '.AX'
            quote = fetch_live_quote(symbol)
            if not quote:
                self._send_json({'error': 'Could not fetch stock data'}, 404)
            else:
                ai_result = ai_analyze_stock(symbol, quote)
                info = ASX_STOCKS.get(symbol, {})
                price = quote.get('price', 0)
                prev = quote.get('previous_close', price)
                last_err = _ai_cache.get('_last_error')
                self._send_json({
                    'symbol': symbol,
                    'company_name': quote.get('long_name') or info.get('name', symbol),
                    'current_price': round(price, 2),
                    'change_pct': round((price - prev) / prev * 100, 2) if prev else 0,
                    'ai_analysis': ai_result,
                    'ai_enabled': bool(GROQ_API_KEY),
                    'ai_error': last_err[1] if last_err and not ai_result else None,
                    'data_source': 'yahoo_finance',
                })
        elif path == '/api/v1/ai/market-summary':
            stocks_data = get_stocks()
            summary = ai_market_summary(stocks_data)
            self._send_json({
                'market_summary': summary,
                'ai_enabled': bool(GROQ_API_KEY),
                'stocks_count': len(stocks_data),
                'data_source': 'yahoo_finance',
            })
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
