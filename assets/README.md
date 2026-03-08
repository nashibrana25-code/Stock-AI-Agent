# Assets — README Screenshots

This folder contains screenshot images referenced in the root `README.md`.

## Required Screenshots

Replace the placeholder files below with real screenshots of the running application.

| Filename | Description | Where to capture |
|----------|-------------|-----------------|
| `dashboard.png` | Main dashboard showing the list of 50 ASX stocks with live prices, percentage changes, and sparklines | Navigate to the app root `/` |
| `stock-detail.png` | Individual stock detail view showing the AI analysis panel (sentiment, target price, confidence score, recommendation, written summary, and key factor tags) | Click any stock ticker to open the detail view |
| `ai-analysis.png` | AI Market Summary and Investment Recommendations panel showing the market mood, sectors to watch, short-term outlook, and a sample portfolio built for a given capital amount | Click "AI Market Summary" or enter a capital amount in the recommendations form |

## Recommended Screenshot Settings

- **Resolution:** 1280 × 800 px minimum (Retina/2x preferred: 2560 × 1600 px)
- **Format:** PNG (lossless)
- **Browser:** Chrome or Edge, dark mode, default zoom (100 %)
- **State:** Populate the UI with live data before capturing — avoid empty/loading states

## Replacing Placeholders

```bash
# Overwrite each placeholder with your real screenshot:
cp path/to/your/dashboard-screenshot.png   assets/dashboard.png
cp path/to/your/stock-detail-screenshot.png assets/stock-detail.png
cp path/to/your/ai-analysis-screenshot.png  assets/ai-analysis.png

git add assets/
git commit -m "docs: add real screenshots to assets folder"
```
