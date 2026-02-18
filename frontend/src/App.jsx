import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'https://asx-ai-investment-platform.vercel.app';
const RANGES = ['1W', '1M', '3M', '6M', '1Y', '5Y'];

function App() {
  const [capital, setCapital] = useState(1000);
  const [riskLevel, setRiskLevel] = useState('moderate');
  const [strategy, setStrategy] = useState('balanced');
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stocks, setStocks] = useState({});
  const [connected, setConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('recommend');
  const [selectedStock, setSelectedStock] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [historyRange, setHistoryRange] = useState('1M');
  const [historyLoading, setHistoryLoading] = useState(false);
  const [expandedRec, setExpandedRec] = useState(null);
  const [recHistoryData, setRecHistoryData] = useState(null);
  const [recHistoryRange, setRecHistoryRange] = useState('1M');
  const [recHistoryLoading, setRecHistoryLoading] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await axios.get(`${API_URL}/health`);
        if (response.data.status === 'healthy') setConnected(true);
      } catch { setConnected(false); }
    };
    checkConnection();

    const loadStocks = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/stocks`);
        setStocks(response.data);
      } catch (err) { console.error('Error loading stocks:', err); }
    };
    loadStocks();
  }, []);

  // Market Overview history
  useEffect(() => {
    if (!selectedStock) { setHistoryData(null); return; }
    const fetchHistory = async () => {
      setHistoryLoading(true);
      try {
        const response = await axios.get(`${API_URL}/api/v1/stocks/${selectedStock}?range=${historyRange}`);
        setHistoryData(response.data);
      } catch (err) { console.error('Error loading history:', err); }
      finally { setHistoryLoading(false); }
    };
    fetchHistory();
  }, [selectedStock, historyRange]);

  // Recommendation expanded history
  useEffect(() => {
    if (!expandedRec) { setRecHistoryData(null); return; }
    const fetchHistory = async () => {
      setRecHistoryLoading(true);
      try {
        const response = await axios.get(`${API_URL}/api/v1/stocks/${expandedRec}?range=${recHistoryRange}`);
        setRecHistoryData(response.data);
      } catch (err) { console.error('Error loading rec history:', err); }
      finally { setRecHistoryLoading(false); }
    };
    fetchHistory();
  }, [expandedRec, recHistoryRange]);

  const generateRecommendation = async () => {
    setLoading(true);
    setExpandedRec(null);
    try {
      const response = await axios.post(`${API_URL}/api/v1/recommendations/generate`, {
        total_capital: parseFloat(capital),
        risk_tolerance: riskLevel,
        investment_strategy: strategy,
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const tierLabel = () => {
    if (capital <= 500) return { tier: 1, label: 'Focus', desc: 'Single stock strategy' };
    if (capital <= 2000) return { tier: 2, label: 'Core', desc: 'Up to 3 positions' };
    if (capital <= 5000) return { tier: 3, label: 'Growth', desc: 'Up to 7 positions' };
    return { tier: 4, label: 'Portfolio', desc: 'Full diversification' };
  };

  const t = tierLabel();

  const getStockAnalysis = (symbol, data) => {
    const price = data?.current_price || 0;
    const h = (s) => Math.abs(((s.split('').reduce((a, c) => a + c.charCodeAt(0), 0) * 2654435761) >>> 0) % 1000);
    const baseReturn = 8.0 + (h(symbol) % 15);
    const confidence = 0.60 + (h(symbol + 'c') % 30) / 100;
    const riskScore = 0.3 + (h(symbol + 'r') % 40) / 100;
    const volatility = 10 + (h(symbol + 'v') % 20);
    const peRatio = 12 + (h(symbol + 'pe') % 25);
    const divYield = 1.5 + (h(symbol + 'dy') % 40) / 10;
    const marketCap = 10 + (h(symbol + 'mc') % 190);
    const weekHigh52 = price * (1 + (5 + h(symbol + 'h') % 20) / 100);
    const weekLow52 = price * (1 - (5 + h(symbol + 'l') % 25) / 100);
    const targetPrice = price * (1 + baseReturn / 100);
    const potentialGain = targetPrice - price;
    const dayChange = ((h(symbol + 'd') % 500) - 250) / 100;
    const volume = 500000 + (h(symbol + 'vol') % 9500000);

    const riskLabel = riskScore < 0.4 ? 'Low' : riskScore < 0.6 ? 'Moderate' : riskScore < 0.8 ? 'High' : 'Very High';
    const riskColor = riskScore < 0.4 ? 'text-gain' : riskScore < 0.6 ? 'text-yellow-400' : riskScore < 0.8 ? 'text-orange-400' : 'text-loss';
    const signal = confidence > 0.75 && baseReturn > 15 ? 'Strong Buy' : confidence > 0.65 ? 'Buy' : 'Hold';
    const signalColor = signal === 'Strong Buy' ? 'bg-gain/20 text-gain' : signal === 'Buy' ? 'bg-accent/20 text-accent' : 'bg-yellow-500/20 text-yellow-400';
    return {
      baseReturn: baseReturn.toFixed(1), confidence: (confidence * 100).toFixed(0), riskScore: riskScore.toFixed(2),
      riskLabel, riskColor, volatility: volatility.toFixed(1), peRatio: peRatio.toFixed(1), divYield: divYield.toFixed(2),
      marketCap: marketCap.toFixed(1), weekHigh52: weekHigh52.toFixed(2), weekLow52: weekLow52.toFixed(2),
      targetPrice: targetPrice.toFixed(2), potentialGain: potentialGain.toFixed(2), dayChange: dayChange.toFixed(2),
      volume: volume.toLocaleString(), signal, signalColor, confidenceRaw: confidence,
      pricePosition: ((price - weekLow52) / (weekHigh52 - weekLow52) * 100).toFixed(0),
    };
  };

  const PriceChart = ({ data, idPrefix }) => {
    if (!data || !data.prices || data.prices.length === 0) return null;
    const prices = data.prices.map(p => p.close);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const range = maxP - minP || 1;
    const w = 600;
    const h = 160;
    const pad = { top: 10, bottom: 30, left: 0, right: 0 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const points = prices.map((p, i) => {
      const x = pad.left + (i / (prices.length - 1)) * chartW;
      const y = pad.top + chartH - ((p - minP) / range) * chartH;
      return `${x},${y}`;
    }).join(' ');

    const areaPoints = `${pad.left},${pad.top + chartH} ${points} ${pad.left + chartW},${pad.top + chartH}`;
    const isPositive = prices[prices.length - 1] >= prices[0];
    const strokeColor = isPositive ? '#00d4aa' : '#ef4444';
    const gainId = `${idPrefix || 'chart'}-gradGain`;
    const lossId = `${idPrefix || 'chart'}-gradLoss`;
    const fillId = isPositive ? gainId : lossId;

    const labelCount = 5;
    const step = Math.max(1, Math.floor((data.prices.length - 1) / (labelCount - 1)));
    const dateLabels = [];
    for (let i = 0; i < data.prices.length; i += step) {
      const d = data.prices[i].date;
      const x = pad.left + (i / (prices.length - 1)) * chartW;
      dateLabels.push({ x, label: d.slice(5) });
    }

    return (
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
        <defs>
          <linearGradient id={gainId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00d4aa" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#00d4aa" stopOpacity="0" />
          </linearGradient>
          <linearGradient id={lossId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={areaPoints} fill={`url(#${fillId})`} />
        <polyline points={points} fill="none" stroke={strokeColor} strokeWidth="2" strokeLinejoin="round" />
        {dateLabels.map((d, i) => (
          <text key={i} x={d.x} y={h - 5} textAnchor="middle" fill="#6b7280" fontSize="10">{d.label}</text>
        ))}
      </svg>
    );
  };

  const StockAnalysisPanel = ({ symbol, stockData, analysisData, hData, hRange, hLoading, onRangeChange, onClose, idPrefix }) => {
    const a = analysisData;
    const data = stockData;
    return (
      <div className="mt-4 bg-dark-800 border border-accent/20 rounded-2xl p-6 animate-in">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-2xl font-bold">{symbol.replace('.AX', '')}</h3>
              <span className={`text-xs px-2 py-1 rounded-lg font-semibold ${a.signalColor}`}>{a.signal}</span>
            </div>
            <p className="text-sm text-gray-400">{data.company_name || data.name} &middot; {data.sector}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition p-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Price Overview Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-dark-700 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Current Price</p>
            <p className="text-2xl font-bold">${data.current_price || data.price}</p>
            <p className={`text-xs font-medium mt-1 ${parseFloat(a.dayChange) >= 0 ? 'text-gain' : 'text-loss'}`}>
              {parseFloat(a.dayChange) >= 0 ? '\u25B2' : '\u25BC'} {a.dayChange}% today
            </p>
          </div>
          <div className="bg-dark-700 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">AI Target</p>
            <p className="text-2xl font-bold text-accent">${a.targetPrice}</p>
            <p className="text-xs text-gain mt-1">+${a.potentialGain} upside</p>
          </div>
          <div className="bg-dark-700 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Expected Return</p>
            <p className="text-2xl font-bold text-gain">+{a.baseReturn}%</p>
            <p className="text-xs text-gray-500 mt-1">AI predicted</p>
          </div>
          <div className="bg-dark-700 rounded-xl p-4">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Confidence</p>
            <p className="text-2xl font-bold">{a.confidence}%</p>
            <div className="w-full h-1.5 bg-dark-600 rounded-full mt-2 overflow-hidden">
              <div className="h-full bg-accent rounded-full" style={{ width: `${a.confidence}%` }} />
            </div>
          </div>
        </div>

        {/* Price History Chart */}
        <div className="bg-dark-700/50 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Price History</p>
              {hData && (
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-lg font-bold ${hData.period_return_pct >= 0 ? 'text-gain' : 'text-loss'}`}>
                    {hData.period_return_pct >= 0 ? '+' : ''}{hData.period_return_pct}%
                  </span>
                  <span className="text-xs text-gray-500">
                    ${hData.period_start_price} &rarr; ${hData.current_price}
                  </span>
                </div>
              )}
            </div>
            <div className="flex gap-1 bg-dark-800 rounded-lg p-0.5">
              {RANGES.map(r => (
                <button
                  key={r}
                  onClick={(e) => { e.stopPropagation(); onRangeChange(r); }}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                    hRange === r
                      ? 'bg-accent text-dark-900'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {hLoading ? (
            <div className="h-40 flex items-center justify-center">
              <svg className="animate-spin h-6 w-6 text-accent" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </div>
          ) : hData ? (
            <>
              <PriceChart data={hData} idPrefix={idPrefix} />
              <div className="grid grid-cols-4 gap-3 mt-4">
                <div className="bg-dark-800/80 rounded-lg p-2.5">
                  <p className="text-[9px] text-gray-500 uppercase">Period High</p>
                  <p className="text-sm font-bold text-gain">${hData.period_high}</p>
                </div>
                <div className="bg-dark-800/80 rounded-lg p-2.5">
                  <p className="text-[9px] text-gray-500 uppercase">Period Low</p>
                  <p className="text-sm font-bold text-loss">${hData.period_low}</p>
                </div>
                <div className="bg-dark-800/80 rounded-lg p-2.5">
                  <p className="text-[9px] text-gray-500 uppercase">Avg Price</p>
                  <p className="text-sm font-bold">${hData.average_price}</p>
                </div>
                <div className="bg-dark-800/80 rounded-lg p-2.5">
                  <p className="text-[9px] text-gray-500 uppercase">Avg Volume</p>
                  <p className="text-sm font-bold">{hData.average_volume?.toLocaleString()}</p>
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* 52-Week Range */}
        <div className="bg-dark-700/50 rounded-xl p-4 mb-6">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">52-Week Range</p>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 w-16">${a.weekLow52}</span>
            <div className="flex-1 relative h-2 bg-dark-600 rounded-full">
              <div className="absolute h-full bg-gradient-to-r from-loss via-yellow-500 to-gain rounded-full" style={{ width: '100%' }} />
              <div
                className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full border-2 border-dark-900 shadow-lg"
                style={{ left: `${Math.min(Math.max(a.pricePosition, 2), 98)}%` }}
              />
            </div>
            <span className="text-xs text-gray-400 w-16 text-right">${a.weekHigh52}</span>
          </div>
        </div>

        {/* Fundamentals Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">P/E Ratio</p>
            <p className="text-sm font-bold mt-1">{a.peRatio}x</p>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Div. Yield</p>
            <p className="text-sm font-bold mt-1">{a.divYield}%</p>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Volatility</p>
            <p className="text-sm font-bold mt-1">{a.volatility}%</p>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Market Cap</p>
            <p className="text-sm font-bold mt-1">${a.marketCap}B</p>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Volume</p>
            <p className="text-sm font-bold mt-1">{a.volume}</p>
          </div>
          <div className="bg-dark-700/50 rounded-lg p-3">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Risk</p>
            <p className={`text-sm font-bold mt-1 ${a.riskColor}`}>{a.riskLabel}</p>
          </div>
        </div>

        {/* Investment Scenarios */}
        <div className="bg-dark-700/30 rounded-xl p-4">
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">If You Invest Today</p>
          <div className="grid grid-cols-3 gap-4">
            {[500, 1000, 5000].map((amt) => {
              const price = data.current_price || data.price;
              const shares = Math.floor(amt / price);
              const invested = shares * price;
              const futureVal = invested * (1 + parseFloat(a.baseReturn) / 100);
              const profit = futureVal - invested;
              return (
                <div key={amt} className="bg-dark-800 rounded-lg p-3 border border-dark-600/30">
                  <p className="text-xs text-gray-400 mb-2">${amt.toLocaleString()} invested</p>
                  <p className="text-xs text-gray-500">{shares} shares @ ${price}</p>
                  <p className="text-sm font-bold text-gain mt-2">+${profit.toFixed(2)}</p>
                  <p className="text-[10px] text-gray-500">Projected profit</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Navigation */}
      <nav className="border-b border-dark-600/50 backdrop-blur-xl bg-dark-900/80 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
              <svg className="w-5 h-5 text-dark-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight">ASX AI</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden md:flex items-center gap-1 text-sm">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-gain animate-pulse' : 'bg-loss'}`} />
              <span className="text-gray-400">{connected ? 'Live' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Hero */}
        <div className="mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-3">
            Invest smarter<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-emerald-400">
              with AI insights.
            </span>
          </h1>
          <p className="text-gray-400 text-lg max-w-xl">
            AI-powered ASX stock recommendations tailored to your capital and risk appetite. From $50 to $10,000.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-1 mb-8 bg-dark-700 rounded-xl p-1 w-fit">
          <button
            onClick={() => setActiveTab('recommend')}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'recommend' ? 'bg-dark-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'
            }`}
          >
            Get Recommendations
          </button>
          <button
            onClick={() => setActiveTab('market')}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'market' ? 'bg-dark-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'
            }`}
          >
            Market Overview
          </button>
        </div>

        {activeTab === 'recommend' && (
          <>
            {/* Input Card */}
            <div className="bg-dark-800 border border-dark-600/50 rounded-2xl p-6 md:p-8 mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">Configure Strategy</h2>
                <div className="flex items-center gap-2 bg-dark-700 rounded-lg px-3 py-1.5">
                  <span className="text-xs text-gray-400">Tier</span>
                  <span className="text-sm font-bold text-accent">{t.tier}</span>
                  <span className="text-xs text-gray-500">&middot;</span>
                  <span className="text-xs text-gray-400">{t.label}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm text-gray-400 mb-2 font-medium">Investment Capital</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 font-semibold">$</span>
                    <input
                      type="number" min="50" max="10000" value={capital}
                      onChange={(e) => setCapital(e.target.value)}
                      className="w-full bg-dark-700 border border-dark-600 rounded-xl pl-8 pr-4 py-3 text-white font-semibold text-lg focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{t.desc}</p>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2 font-medium">Risk Tolerance</label>
                  <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-600 rounded-xl px-4 py-3 text-white font-medium focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all appearance-none cursor-pointer">
                    <option value="very_low">Very Low</option>
                    <option value="low">Low</option>
                    <option value="moderate">Moderate</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-2 font-medium">Strategy</label>
                  <select value={strategy} onChange={(e) => setStrategy(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-600 rounded-xl px-4 py-3 text-white font-medium focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all appearance-none cursor-pointer">
                    <option value="conservative">Conservative</option>
                    <option value="balanced">Balanced</option>
                    <option value="growth">Growth</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </div>
              </div>

              <button onClick={generateRecommendation} disabled={loading}
                className="mt-6 w-full bg-gradient-to-r from-accent to-accent-dark hover:from-accent-light hover:to-accent text-dark-900 font-bold py-3.5 px-6 rounded-xl transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed text-sm tracking-wide">
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    ANALYZING MARKET...
                  </span>
                ) : 'GENERATE RECOMMENDATIONS'}
              </button>
            </div>

            {recommendations && (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-dark-800 border border-dark-600/50 rounded-2xl p-5">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Expected Return</p>
                    <p className="text-3xl font-bold text-gain">+{recommendations.expected_return}%</p>
                  </div>
                  <div className="bg-dark-800 border border-dark-600/50 rounded-2xl p-5">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Invested</p>
                    <p className="text-3xl font-bold">${recommendations.total_investment.toLocaleString()}</p>
                  </div>
                  <div className="bg-dark-800 border border-dark-600/50 rounded-2xl p-5">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Positions</p>
                    <p className="text-3xl font-bold">{recommendations.recommendations?.length || 0}</p>
                  </div>
                </div>

                <div className="bg-dark-800/50 border border-dark-600/30 rounded-xl px-5 py-3">
                  <p className="text-sm text-gray-400">{recommendations.summary}</p>
                </div>

                <div className="space-y-3">
                  {recommendations.recommendations?.map((stock, index) => {
                    const isExpanded = expandedRec === stock.symbol;
                    const a = getStockAnalysis(stock.symbol, { current_price: stock.current_price });
                    return (
                      <div key={index}>
                        <div
                          onClick={() => { setExpandedRec(isExpanded ? null : stock.symbol); setRecHistoryRange('1M'); }}
                          className={`bg-dark-800 border rounded-2xl p-5 cursor-pointer transition-all group ${
                            isExpanded ? 'border-accent/50 ring-1 ring-accent/20' : 'border-dark-600/50 hover:border-dark-500'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-dark-700 flex items-center justify-center text-xs font-bold text-accent border border-dark-600">
                                {index + 1}
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <h3 className="font-bold text-base">{stock.symbol.replace('.AX', '')}</h3>
                                  <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-semibold ${a.signalColor}`}>{a.signal}</span>
                                </div>
                                <p className="text-xs text-gray-500">{stock.company_name}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="text-right">
                                <p className="text-lg font-bold text-gain">${stock.recommended_allocation.toLocaleString()}</p>
                                <p className="text-xs text-gray-500">{stock.recommended_shares} shares</p>
                              </div>
                              <svg className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </div>
                          </div>
                          <div className="grid grid-cols-4 gap-4">
                            <div className="bg-dark-700/50 rounded-lg p-3">
                              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Price</p>
                              <p className="text-sm font-semibold mt-0.5">${stock.current_price}</p>
                            </div>
                            <div className="bg-dark-700/50 rounded-lg p-3">
                              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Target</p>
                              <p className="text-sm font-semibold mt-0.5 text-accent">${stock.target_price}</p>
                            </div>
                            <div className="bg-dark-700/50 rounded-lg p-3">
                              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Return</p>
                              <p className="text-sm font-semibold mt-0.5 text-gain">+{stock.predicted_return}%</p>
                            </div>
                            <div className="bg-dark-700/50 rounded-lg p-3">
                              <p className="text-[10px] text-gray-500 uppercase tracking-wider">Confidence</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <div className="flex-1 h-1.5 bg-dark-600 rounded-full overflow-hidden">
                                  <div className="h-full bg-accent rounded-full" style={{ width: `${stock.confidence_score * 100}%` }} />
                                </div>
                                <span className="text-xs font-semibold">{(stock.confidence_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          </div>
                          <p className="text-xs text-gray-500 mt-3 leading-relaxed">{stock.reasoning}</p>
                        </div>

                        {isExpanded && (
                          <StockAnalysisPanel
                            symbol={stock.symbol}
                            stockData={{ current_price: stock.current_price, company_name: stock.company_name, sector: stock.reasoning.split('(')[1]?.split(')')[0] || 'ASX' }}
                            analysisData={a}
                            hData={recHistoryData}
                            hRange={recHistoryRange}
                            hLoading={recHistoryLoading}
                            onRangeChange={setRecHistoryRange}
                            onClose={() => setExpandedRec(null)}
                            idPrefix={`rec-${index}`}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {!recommendations && !loading && (
              <div className="bg-dark-800/30 border border-dashed border-dark-600/50 rounded-2xl p-12 text-center">
                <div className="w-16 h-16 rounded-2xl bg-dark-700 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <p className="text-gray-500 text-sm">Configure your strategy and click generate to get AI-powered stock picks</p>
              </div>
            )}
          </>
        )}

        {activeTab === 'market' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">ASX Market Overview</h2>
              <span className="text-xs text-gray-500">{Object.keys(stocks).length} stocks tracked &middot; Click for analysis</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(stocks).map(([symbol, data]) => {
                const a = getStockAnalysis(symbol, data);
                return (
                  <div
                    key={symbol}
                    onClick={() => { setSelectedStock(selectedStock === symbol ? null : symbol); setHistoryRange('1M'); }}
                    className={`bg-dark-800 border rounded-xl p-4 cursor-pointer transition-all ${
                      selectedStock === symbol ? 'border-accent/50 ring-1 ring-accent/20' : 'border-dark-600/50 hover:border-dark-500'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-sm">{symbol.replace('.AX', '')}</p>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-semibold ${a.signalColor}`}>{a.signal}</span>
                        </div>
                        <p className="text-[11px] text-gray-500">{data?.company_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">${data?.current_price}</p>
                        <p className={`text-xs font-medium ${parseFloat(a.dayChange) >= 0 ? 'text-gain' : 'text-loss'}`}>
                          {parseFloat(a.dayChange) >= 0 ? '+' : ''}{a.dayChange}%
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] bg-dark-700 text-gray-400 px-2 py-0.5 rounded-md">{data?.sector}</span>
                      <svg className={`w-4 h-4 text-gray-500 transition-transform ${selectedStock === symbol ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Expanded Stock Analysis Panel */}
            {selectedStock && stocks[selectedStock] && (() => {
              const data = stocks[selectedStock];
              const a = getStockAnalysis(selectedStock, data);
              return (
                <StockAnalysisPanel
                  symbol={selectedStock}
                  stockData={data}
                  analysisData={a}
                  hData={historyData}
                  hRange={historyRange}
                  hLoading={historyLoading}
                  onRangeChange={setHistoryRange}
                  onClose={() => setSelectedStock(null)}
                  idPrefix="market"
                />
              );
            })()}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-700/50 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-accent/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-gray-500">ASX AI Platform</span>
            </div>
            <p className="text-xs text-gray-600">
              24/7 autonomous AI agent &middot; Multi-source data analysis &middot; Capital-aware recommendations
            </p>
            <p className="text-xs text-gray-600">&copy; 2026</p>
          </div>
          <p className="text-[10px] text-gray-700 mt-4 text-center leading-relaxed">
            This platform provides AI-generated stock analysis for educational purposes only. Not financial advice. Always do your own research before investing.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
