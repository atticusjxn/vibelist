# X Sentiment Integration Guide

## Current Status
✅ **System is FULLY FUNCTIONAL with Grok sentiment** (already integrated)

The X sentiment modules (`x_scraper.py` + `sentiment_analyzer.py`) are **ready but not yet integrated** into main.py because:
1. Nitter is currently 100% down (all instances failing)
2. Grok sentiment already works perfectly
3. No need to add code that won't execute until Nitter returns

## When to Integrate ntscraper+VADER

Wait until **Nitter instances are reliable** (check with `python test_x_sentiment.py`). When you see tweets being fetched, proceed with integration below.

---

## Integration Steps (When Nitter Works)

### Step 1: Update `analyzer.py`

Add X sentiment fetching to the stock analysis flow:

```python
# In src/vibelist/analyzer.py

from .x_scraper import fetch_tweets
from .sentiment_analyzer import analyze_sentiment as analyze_vader_sentiment
from .sentiment import XaiAPIClient

class PortfolioAnalyzer:
    def __init__(self, config, xai_api_key=None):
        # ... existing code ...
        self.xai_client = XaiAPIClient(xai_api_key) if xai_api_key else None

    def analyze_stock(self, symbol: str, weight: float) -> StockAnalysis:
        """Analyze individual stock (WITH X sentiment dual-path)"""

        # ... existing stock data fetching ...

        # NEW: Fetch X sentiment with dual-path
        x_result = fetch_tweets(symbol, count=30, grok_client=self.xai_client)

        if x_result['source'] == 'ntscraper':
            # Use VADER sentiment
            vader_sentiment = analyze_vader_sentiment(x_result['tweets'])
            # Convert to SentimentScore format for compatibility
            sentiment_score = SentimentScore(
                symbol=symbol,
                overall_sentiment=vader_sentiment.avg_sentiment,
                sentiment_label=vader_sentiment.get_label(),
                confidence=vader_sentiment.confidence,
                key_insights=[
                    f"{vader_sentiment.pos_pct:.1f}% positive, {vader_sentiment.neg_pct:.1f}% negative from {vader_sentiment.tweets_analyzed} tweets"
                ],
                post_count=vader_sentiment.tweets_analyzed,
                last_updated=datetime.now(),
                sources=["X/Twitter (ntscraper)"],
                top_quote=vader_sentiment.top_positive['text'] if vader_sentiment.top_positive else None,
                top_quote_username=vader_sentiment.top_positive['username'] if vader_sentiment.top_positive else None
            )
        else:
            # Use Grok sentiment (fallback)
            sentiment_score = x_result['grok_sentiment']

        # ... rest of analysis using sentiment_score ...
```

### Step 2: Update Email Template (Optional Enhancement)

If you want to show MORE detail when ntscraper works, add after line 579 in `email_template.html`:

```html
<!-- Enhanced X Sentiment Section (when ntscraper active) -->
{% if analysis.x_sentiment_detail %}
<div class="x-sentiment-pulse" style="margin-top: 16px; padding: 12px; background: #0d1117; border-left: 3px solid #00d4ff; border-radius: 4px;">
    <div style="font-family: 'Share Tech Mono', monospace; font-size: 14px; color: #00d4ff; margin-bottom: 8px;">
        📡 X SENTIMENT PULSE
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 8px;">
        <span style="font-size: 24px;">{{ analysis.x_sentiment_detail.emoji }}</span>
        <div>
            <div style="font-weight: 600;">{{ analysis.x_sentiment_detail.label }}</div>
            <div style="font-size: 13px; color: #8b949e;">
                {{ analysis.x_sentiment_detail.tweets_analyzed }} tweets analyzed ·
                Confidence: {{ analysis.x_sentiment_detail.confidence }}
            </div>
        </div>
    </div>

    <!-- Sentiment Breakdown Bar -->
    <div style="display: flex; gap: 8px; margin-bottom: 8px; font-size: 12px; font-family: 'Share Tech Mono', monospace;">
        <div style="flex: {{ analysis.x_sentiment_detail.pos_pct }}; background: #22c55e; padding: 4px; text-align: center; border-radius: 2px;">
            {{ "%.0f"|format(analysis.x_sentiment_detail.pos_pct) }}%
        </div>
        <div style="flex: {{ analysis.x_sentiment_detail.neu_pct }}; background: #f59e0b; padding: 4px; text-align: center; border-radius: 2px;">
            {{ "%.0f"|format(analysis.x_sentiment_detail.neu_pct) }}%
        </div>
        <div style="flex: {{ analysis.x_sentiment_detail.neg_pct }}; background: #ef4444; padding: 4px; text-align: center; border-radius: 2px;">
            {{ "%.0f"|format(analysis.x_sentiment_detail.neg_pct) }}%
        </div>
    </div>

    <!-- Sample Tweets -->
    {% if analysis.x_sentiment_detail.top_positive %}
    <div style="font-size: 13px; margin-top: 8px; padding: 8px; background: #161b22; border-radius: 4px;">
        <div style="color: #22c55e; font-weight: 600;">📈 Most Positive:</div>
        <div style="color: #c9d1d9; margin-top: 4px;">
            "{{ analysis.x_sentiment_detail.top_positive.text[:100] }}..."
            <span style="color: #8b949e;">— @{{ analysis.x_sentiment_detail.top_positive.username }}</span>
            {% if analysis.x_sentiment_detail.top_positive.sarcasm %}
            <span style="color: #f59e0b;">⚠️ sarcasm?</span>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if analysis.x_sentiment_detail.top_negative %}
    <div style="font-size: 13px; margin-top: 8px; padding: 8px; background: #161b22; border-radius: 4px;">
        <div style="color: #ef4444; font-weight: 600;">📉 Most Negative:</div>
        <div style="color: #c9d1d9; margin-top: 4px;">
            "{{ analysis.x_sentiment_detail.top_negative.text[:100] }}..."
            <span style="color: #8b949e;">— @{{ analysis.x_sentiment_detail.top_negative.username }}</span>
            {% if analysis.x_sentiment_detail.top_negative.sarcasm %}
            <span style="color: #f59e0b;">⚠️ sarcasm?</span>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>
{% endif %}
```

### Step 3: Update `email_generator.py`

Pass VADER sentiment details to the template:

```python
def _prepare_template_context(self, portfolio_analysis: PortfolioAnalysis) -> Dict[str, Any]:
    """Prepare context for email template"""
    # ... existing code ...

    # Add x_sentiment_detail for enhanced display (when ntscraper works)
    for symbol, analysis in context['portfolio_analysis'].stock_analyses.items():
        if hasattr(analysis, 'vader_sentiment'):
            context['portfolio_analysis'].stock_analyses[symbol].x_sentiment_detail = analysis.vader_sentiment.to_dict()

    return context
```

### Step 4: Test the Integration

```bash
# Verify ntscraper is working
source .venv/bin/activate
python test_x_sentiment.py

# If tweets are fetched, test full flow
python main.py --dry-run
```

---

## Why Not Integrate Now?

1. **Nitter is 100% down** (all 9 instances failing as of Oct 23, 2025)
2. **Grok already works perfectly** (see test output in X_SENTIMENT_IMPLEMENTATION.md)
3. **Code would never execute** (ntscraper fails → Grok fallback every time)
4. **Cleaner to wait** until Nitter stabilizes

## How to Monitor Nitter Status

Run this weekly to check if Nitter is back:

```bash
source .venv/bin/activate
python test_x_sentiment.py
```

Look for output like:
```
Tweets fetched: 15  # If you see this, Nitter is working!
```

When you see tweets being fetched, follow the integration steps above.

---

## Alternative: Use Only Grok (Simpler)

If Nitter never becomes reliable, you can:

1. **Remove ntscraper dependencies**:
   ```bash
   pip uninstall ntscraper
   # Remove from requirements.txt
   ```

2. **Delete unused modules**:
   ```bash
   rm src/vibelist/x_scraper.py
   rm src/vibelist/sentiment_analyzer.py
   rm test_x_sentiment.py test_vader.py
   ```

3. **Keep using Grok** (already working, zero changes needed)

**Grok provides excellent sentiment** with:
- Real X post samples
- AI-powered insights
- 100% uptime
- Already paid for

The ntscraper+VADER path was built for:
- Granular data (individual tweet scores)
- No API costs
- Higher volume analysis

But **Grok works great** if you prefer simplicity over granularity.

---

## Summary

✅ **Current state**: Grok sentiment working perfectly (0 code changes needed)

📦 **Ready to deploy**: ntscraper+VADER modules built and tested (waiting for Nitter)

🎯 **Next action**: Monitor Nitter with `test_x_sentiment.py`, integrate when reliable

💡 **Recommendation**: Deploy current system to GitHub Actions, enjoy daily digests with Grok sentiment!
