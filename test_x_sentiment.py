"""
Test X sentiment integration (ntscraper + VADER + Grok fallback)
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vibelist.x_scraper import fetch_tweets
from vibelist.sentiment_analyzer import analyze_sentiment
from vibelist.sentiment import XaiAPIClient

# Load environment variables
load_dotenv()

def test_ntscraper_with_fallback():
    """Test the dual-path system"""
    print("=" * 60)
    print("Testing X Sentiment Integration")
    print("=" * 60)

    # Setup Grok client for fallback
    xai_api_key = os.getenv("XAI_API_KEY")
    grok_client = None

    if xai_api_key:
        grok_client = XaiAPIClient(xai_api_key)
        print("✅ Grok client initialized (fallback available)")
    else:
        print("⚠️  No XAI_API_KEY found - Grok fallback disabled")

    # Test with AAPL and TSLA
    test_tickers = ['AAPL', 'TSLA']

    for ticker in test_tickers:
        print(f"\n{'=' * 60}")
        print(f"Testing: ${ticker}")
        print(f"{'=' * 60}\n")

        # Fetch tweets (will use Grok fallback if ntscraper fails)
        result = fetch_tweets(ticker, count=20, grok_client=grok_client)

        print(f"Source: {result['source']}")

        if result['source'] == 'ntscraper':
            tweets = result['tweets']
            print(f"Tweets fetched: {len(tweets)}")

            if tweets:
                # Show sample tweets
                print("\nSample tweets:")
                for i, tweet in enumerate(tweets[:3], 1):
                    print(f"\n{i}. @{tweet.username} ({tweet.date})")
                    print(f"   {tweet.text[:100]}...")
                    print(f"   ❤️  {tweet.likes} | 🔁 {tweet.retweets}")

                # Analyze sentiment with VADER
                print("\n" + "-" * 60)
                print("VADER Sentiment Analysis")
                print("-" * 60)

                sentiment = analyze_sentiment(tweets)
                print(f"\n{sentiment.get_emoji()} Overall Sentiment: {sentiment.get_label()}")
                print(f"   Average compound: {sentiment.avg_sentiment:+.3f}")
                print(f"   Positive: {sentiment.pos_pct:.1f}%")
                print(f"   Negative: {sentiment.neg_pct:.1f}%")
                print(f"   Neutral: {sentiment.neu_pct:.1f}%")
                print(f"   Confidence: {sentiment.confidence}")

                if sentiment.top_positive:
                    print(f"\n📈 Most Positive Tweet:")
                    print(f"   @{sentiment.top_positive['username']}: {sentiment.top_positive['text'][:80]}...")
                    print(f"   Score: {sentiment.top_positive['score']:+.3f} {'⚠️ (sarcasm?)' if sentiment.top_positive['sarcasm'] else ''}")

                if sentiment.top_negative:
                    print(f"\n📉 Most Negative Tweet:")
                    print(f"   @{sentiment.top_negative['username']}: {sentiment.top_negative['text'][:80]}...")
                    print(f"   Score: {sentiment.top_negative['score']:+.3f} {'⚠️ (sarcasm?)' if sentiment.top_negative['sarcasm'] else ''}")

            else:
                print("⚠️  No tweets found after filtering")

        elif result['source'] == 'grok':
            print("Using Grok fallback sentiment")
            grok_sentiment = result['grok_sentiment']
            print(f"\nSentiment: {grok_sentiment.sentiment_label}")
            print(f"Score: {grok_sentiment.overall_sentiment:+.2f}")
            print(f"Confidence: {grok_sentiment.confidence:.2f}")
            print(f"Posts analyzed: {grok_sentiment.post_count}")

            if grok_sentiment.key_insights:
                print("\nKey insights:")
                for insight in grok_sentiment.key_insights[:3]:
                    print(f"  • {insight}")

            if grok_sentiment.top_quote:
                print(f"\nTop quote: \"{grok_sentiment.top_quote}\"")
                if grok_sentiment.top_quote_username:
                    print(f"  — @{grok_sentiment.top_quote_username}")

        else:
            print(f"❌ Both ntscraper and Grok failed")
            if result['error']:
                print(f"   Error: {result['error']}")

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_ntscraper_with_fallback()
