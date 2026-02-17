# ASX AI Investment Platform

Enterprise-grade AI-powered investment advisor for Australian Stock Exchange (ASX) with capital-aware recommendations.

## Features

- **Multi-Source Data Aggregation**: Real-time data from ASX, Yahoo Finance, Alpha Vantage, and more
- **AI-Powered Analysis**: Machine learning models for price prediction and trend analysis
- **Sentiment Analysis**: News and social media sentiment processing
- **Capital-Aware Recommendations**: Tailored strategies for portfolios from $50 to $10,000+
- **Risk Management**: Portfolio optimization with diversification rules
- **Real-time Updates**: WebSocket streaming for live market data
- **Scalable Architecture**: Microservices with Kubernetes deployment

## Architecture

```
├── services/
│   ├── data-ingestion/      # Multi-source data collection
│   ├── data-processor/       # ETL and normalization
│   ├── ml-engine/           # AI models and predictions
│   ├── recommendation/      # Investment advisor engine
│   ├── api-gateway/         # Main API endpoint
│   └── notification/        # Alerts and notifications
├── shared/
│   ├── models/              # Data models
│   ├── utils/               # Shared utilities
│   └── config/              # Configuration
├── infrastructure/
│   ├── docker/              # Docker configurations
│   ├── k8s/                 # Kubernetes manifests
│   └── terraform/           # Infrastructure as Code
├── ml-models/               # Trained models and notebooks
├── tests/                   # Test suites
└── docs/                    # Documentation

```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Celery
- **AI/ML**: PyTorch, TensorFlow, scikit-learn, XGBoost
- **Data**: PostgreSQL, TimescaleDB, Redis, Apache Kafka
- **Search**: Elasticsearch
- **Monitoring**: Prometheus, Grafana, ELK Stack
- **Cloud**: AWS/Azure (containerized for multi-cloud)
- **Frontend**: React, TypeScript, Next.js

## Getting Started

See [docs/setup.md](docs/setup.md) for detailed setup instructions.

## Development Phases

- [x] Phase 1: Project Setup & Infrastructure
- [ ] Phase 2: Data Ingestion Layer
- [ ] Phase 3: ML Engine Development
- [ ] Phase 4: Recommendation Engine
- [ ] Phase 5: API & Frontend
- [ ] Phase 6: Testing & Optimization
- [ ] Phase 7: Production Deployment

## License

Proprietary - All Rights Reserved
