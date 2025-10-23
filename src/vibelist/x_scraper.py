"""
X (Twitter) tweet scraping using ntscraper with Grok fallback
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ntscraper import Nitter

logger = logging.getLogger(__name__)

# Spam detection keywords
SPAM_KEYWORDS = [
    'dm for', 'dm me', 'crypto airdrop', 'pump', 'signals', 'click here',
    'free stock', 'guaranteed profit', 'join our', 'telegram',
    'make money fast', 'secret strategy'
]


class TweetData:
    """Structured tweet data"""
    def __init__(self, text: str, username: str, date: str, link: Optional[str] = None,
                 likes: int = 0, retweets: int = 0):
        self.text = text
        self.username = username
        self.date = date
        self.link = link
        self.likes = likes
        self.retweets = retweets
        self.parsed_date: Optional[datetime] = None
        self._parse_date()

    def _parse_date(self):
        """Parse ntscraper date format to datetime"""
        try:
            # ntscraper date format: "Jan 23, 2025 · 2:30 PM UTC"
            self.parsed_date = datetime.strptime(self.date, '%b %d, %Y · %I:%M %p %Z')
        except Exception as e:
            logger.debug(f"Date parse failed for '{self.date}': {e}")
            # Fallback: assume recent if parsing fails
            self.parsed_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'username': self.username,
            'date': self.date,
            'link': self.link,
            'likes': self.likes,
            'retweets': self.retweets
        }


def is_spam(tweet_text: str) -> bool:
    """
    Detect spam tweets using keyword blacklist and heuristics

    Args:
        tweet_text: The tweet content to check

    Returns:
        True if tweet is likely spam
    """
    text_lower = tweet_text.lower()

    # Check spam keywords
    if any(keyword in text_lower for keyword in SPAM_KEYWORDS):
        return True

    # Excessive hashtags (>3)
    if tweet_text.count('#') > 3:
        return True

    # Too short (likely bot)
    if len(tweet_text.strip()) < 20:
        return True

    # Multiple URLs (likely spam/scam)
    urls = re.findall(r'http\S+', tweet_text)
    if len(urls) > 2:
        return True

    return False


def is_recent(tweet: TweetData, max_age_hours: int = 72) -> bool:
    """
    Check if tweet is recent enough

    Args:
        tweet: TweetData object
        max_age_hours: Maximum age in hours (default 72 = 3 days)

    Returns:
        True if tweet is within the age threshold
    """
    if not tweet.parsed_date:
        return True  # If we can't parse, assume it's recent (benefit of doubt)

    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    return tweet.parsed_date > cutoff


def fetch_tweets_ntscraper(ticker: str, count: int = 30, max_retries: int = 3) -> List[TweetData]:
    """
    Fetch tweets about a stock ticker using ntscraper

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        count: Number of tweets to fetch
        max_retries: Number of retry attempts for failed requests

    Returns:
        List of TweetData objects (may be empty if all instances fail)
    """
    try:
        logger.info(f"Fetching {count} tweets for ${ticker} via ntscraper")

        # Create multi-query to catch different tweet formats
        queries = [
            f"${ticker}",           # $AAPL
            f"#{ticker}",           # #AAPL
            f"{ticker} stock"       # "AAPL stock"
        ]

        all_tweets = []
        scraper = Nitter(log_level=1)  # Reduce ntscraper logging noise

        for query in queries:
            try:
                logger.debug(f"Searching for: {query}")
                result = scraper.get_tweets(query, mode='term', number=count // 3, max_retries=max_retries)

                if result and 'tweets' in result:
                    raw_tweets = result['tweets']
                    logger.info(f"Retrieved {len(raw_tweets)} raw tweets for query: {query}")

                    for tw in raw_tweets:
                        # Extract tweet data
                        tweet = TweetData(
                            text=tw.get('text', ''),
                            username=tw.get('user', {}).get('username', 'unknown'),
                            date=tw.get('date', ''),
                            link=tw.get('link'),
                            likes=tw.get('stats', {}).get('likes', 0),
                            retweets=tw.get('stats', {}).get('retweets', 0)
                        )

                        # Filter spam FIRST
                        if is_spam(tweet.text):
                            logger.debug(f"Filtering spam tweet: {tweet.text[:50]}...")
                            continue

                        # Filter by recency
                        if not is_recent(tweet, max_age_hours=72):
                            logger.debug(f"Filtering old tweet from {tweet.date}")
                            continue

                        # Filter retweets (RT @user)
                        if tweet.text.startswith('RT @'):
                            logger.debug(f"Filtering retweet: {tweet.text[:50]}...")
                            continue

                        all_tweets.append(tweet)

            except Exception as e:
                logger.warning(f"Query '{query}' failed: {e}")
                continue

        # Deduplicate tweets by text (avoid counting same tweet twice)
        unique_tweets = []
        seen_texts = set()
        for tweet in all_tweets:
            text_normalized = tweet.text.lower().strip()
            if text_normalized not in seen_texts:
                seen_texts.add(text_normalized)
                unique_tweets.append(tweet)

        logger.info(f"Fetched {len(unique_tweets)} unique, recent tweets for ${ticker} (filtered from {len(all_tweets)})")

        if len(unique_tweets) < 5:
            logger.warning(f"Only {len(unique_tweets)} tweets found for ${ticker} after filtering (spam + recency)")

        return unique_tweets

    except Exception as e:
        logger.error(f"ntscraper failed for ${ticker}: {e}")
        return []


def fetch_tweets(ticker: str, count: int = 30, grok_client=None) -> Dict[str, Any]:
    """
    Fetch tweets with dual-path: ntscraper primary, Grok fallback

    Args:
        ticker: Stock ticker symbol
        count: Desired number of tweets
        grok_client: Optional XaiAPIClient for fallback sentiment

    Returns:
        Dictionary with:
        - source: "ntscraper" or "grok"
        - tweets: List of TweetData objects (empty for grok)
        - grok_sentiment: SentimentScore object (only for grok)
        - error: Error message if any
    """
    # Try ntscraper first
    tweets = fetch_tweets_ntscraper(ticker, count)

    if len(tweets) >= 5:
        # Success! We have enough tweets
        return {
            'source': 'ntscraper',
            'tweets': tweets,
            'grok_sentiment': None,
            'error': None
        }

    # Fallback to Grok if:
    # 1. ntscraper returned <5 tweets (all instances down or low-volume stock)
    # 2. grok_client is provided
    if grok_client:
        logger.warning(f"ntscraper returned only {len(tweets)} tweets for ${ticker}, falling back to Grok")
        try:
            grok_sentiment = grok_client.analyze_stock_sentiment(ticker, hours_back=48)
            return {
                'source': 'grok',
                'tweets': [],
                'grok_sentiment': grok_sentiment,
                'error': None
            }
        except Exception as e:
            logger.error(f"Grok fallback also failed for ${ticker}: {e}")
            return {
                'source': 'failed',
                'tweets': tweets,  # Return what we have, even if <5
                'grok_sentiment': None,
                'error': str(e)
            }
    else:
        # No Grok client provided, return what we have
        return {
            'source': 'ntscraper',
            'tweets': tweets,
            'grok_sentiment': None,
            'error': f"Only {len(tweets)} tweets found (no Grok fallback available)"
        }
