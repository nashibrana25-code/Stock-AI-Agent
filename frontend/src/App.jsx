import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'https://asx-ai-investment-platform.vercel.app';

function App() {
  const [capital, setCapital] = useState(1000);
  const [riskLevel, setRiskLevel] = useState('moderate');
  const [strategy, setStrategy] = useState('balanced');
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stocks, setStocks] = useState({});
  const [connected, setConnected] = useState(false);

  // Check API connection on load
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await axios.get(`${API_URL}/health`);
        if (response.data.status === 'healthy') {
          setConnected(true);
        }
      } catch (err) {
        setConnected(false);
      }
    };
    checkConnection();

    // Load stock data
    const loadStocks = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/stocks`);
        setStocks(response.data);
      } catch (err) {
        console.error('Error loading stocks:', err);
      }
    };
    loadStocks();
  }, []);

  const generateRecommendation = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/v1/recommendations/generate`, {
        total_capital: parseFloat(capital),
        risk_tolerance: riskLevel,
        investment_strategy: strategy,
        min_diversification: 3,
        max_single_stock_percentage: 0.30
      });
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error generating recommendations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                ASX AI Investment Platform
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                24/7 AI-Powered Stock Recommendations
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`h-3 w-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-sm text-gray-600">
                {connected ? 'AI Agent Online' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Input Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-6">Get Personalized Recommendations</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Investment Capital ($50 - $10,000)
              </label>
              <input
                type="number"
                min="50"
                max="10000"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                {capital <= 500 && "Tier 1: Focus strategy"}
                {capital > 500 && capital <= 2000 && "Tier 2: Basic diversification"}
                {capital > 2000 && capital <= 5000 && "Tier 3: Moderate diversification"}
                {capital > 5000 && "Tier 4: Full diversification"}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Risk Tolerance
              </label>
              <select
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="very_low">Very Low</option>
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
                <option value="very_high">Very High</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Investment Strategy
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="conservative">Conservative</option>
                <option value="balanced">Balanced</option>
                <option value="growth">Growth</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>
          </div>

          <button
            onClick={generateRecommendation}
            disabled={loading}
            className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Generate AI Recommendations'}
          </button>
        </div>

        {/* Recommendations Display */}
        {recommendations && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold mb-4">Your Personalized Portfolio</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Expected Return</p>
                <p className="text-2xl font-bold text-blue-600">
                  {recommendations.expected_return}%
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Investment</p>
                <p className="text-2xl font-bold text-green-600">
                  ${recommendations.total_investment}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Stocks Recommended</p>
                <p className="text-2xl font-bold text-purple-600">
                  {recommendations.recommendations?.length || 0}
                </p>
              </div>
            </div>

            <p className="text-gray-700 mb-6">{recommendations.summary}</p>

            {/* Stock Recommendations */}
            <div className="space-y-4">
              {recommendations.recommendations?.map((stock, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold">{stock.symbol}</h3>
                      <p className="text-sm text-gray-600">{stock.company_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-green-600">
                        ${stock.recommended_allocation}
                      </p>
                      <p className="text-sm text-gray-600">
                        {stock.recommended_shares} shares
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                    <div>
                      <p className="text-gray-600">Current Price</p>
                      <p className="font-semibold">${stock.current_price}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Target Price</p>
                      <p className="font-semibold">${stock.target_price}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Expected Return</p>
                      <p className="font-semibold text-green-600">+{stock.predicted_return}%</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Confidence</p>
                      <p className="font-semibold">{(stock.confidence_score * 100).toFixed(0)}%</p>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 mt-4">
                    <strong>Reasoning:</strong> {stock.reasoning}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Live Market Data */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-4">ASX Market Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stocks).slice(0, 8).map(([symbol, data]) => (
              <div key={symbol} className="border border-gray-200 rounded-lg p-3">
                <p className="font-semibold text-sm">{symbol}</p>
                <p className="text-xs text-gray-500">{data?.company_name || ''}</p>
                <p className="text-xl font-bold mt-1">${data?.current_price || '---'}</p>
                <p className="text-xs text-gray-500">{data?.sector || ''}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white mt-12 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 text-center text-gray-600">
          <p>© 2026 ASX AI Investment Platform | 24/7 Autonomous AI Agent</p>
          <p className="text-sm mt-1">Real-time analysis • Multi-source data • Capital-aware recommendations</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
