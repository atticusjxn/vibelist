"""
VADER sentiment analysis with sarcasm detection for X tweets
"""

import logging
from typing import Dict, List, Any, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Sarcasm indicators
SARCASM_EMOJIS = ['😂', '🤣', '💀', '😭', '🙄', '😏']


class SentimentResult:
    """Structured sentiment analysis result"""
    def __init__(self, avg_sentiment: float, pos_pct: float, neg_pct: float, neu_pct: float,
                 confidence: str, tweets_analyzed: int, top_positive: Optional[Dict] = None,
                 top_negative: Optional[Dict] = None):
        self.avg_sentiment = avg_sentiment
        self.pos_pct = pos_pct
        self.neg_pct = neg_pct
        self.neu_pct = neu_pct
        self.confidence = confidence  # "high", "medium", "low"
        self.tweets_analyzed = tweets_analyzed
        self.top_positive = top_positive
        self.top_negative = top_negative

    def get_label(self) -> str:
        """Get sentiment label (POSITIVE/NEGATIVE/NEUTRAL)"""
        if self.avg_sentiment > 0.25:
            return "POSITIVE"
        elif self.avg_sentiment < -0.25:
            return "NEGATIVE"
        else:
            return "NEUTRAL"

    def get_emoji(self) -> str:
        """Get emoji indicator for sentiment"""
        if self.avg_sentiment > 0.25:
            return "🟢"  # Green for positive
        elif self.avg_sentiment < -0.25:
            return "🔴"  # Red for negative
        else:
            return "🟡"  # Yellow for neutral

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'avg_sentiment': self.avg_sentiment,
            'pos_pct': self.pos_pct,
            'neg_pct': self.neg_pct,
            'neu_pct': self.neu_pct,
            'confidence': self.confidence,
            'tweets_analyzed': self.tweets_analyzed,
            'label': self.get_label(),
            'emoji': self.get_emoji(),
            'top_positive': self.top_positive,
            'top_negative': self.top_negative
        }


def detect_sarcasm(text: str) -> bool:
    """
    Detect likely sarcasm in tweet text

    Args:
        text: Tweet content

    Returns:
        True if sarcasm indicators detected
    """
    # Check for sarcasm emojis
    if any(emoji in text for emoji in SARCASM_EMOJIS):
        return True

    # Check for sarcastic patterns
    sarcasm_patterns = [
        'oh great',
        'just great',
        'perfect timing',
        'love it when',
        'totally fine',
        'this is fine'
    ]

    text_lower = text.lower()
    if any(pattern in text_lower for pattern in sarcasm_patterns):
        return True

    # Excessive punctuation (!!!, ???)
    if text.count('!') > 2 or text.count('?') > 2:
        return True

    return False


def adjust_for_sarcasm(vader_score: Dict[str, float], text: str) -> Dict[str, float]:
    """
    Adjust VADER score if sarcasm detected

    Args:
        vader_score: Original VADER polarity scores
        text: Tweet text

    Returns:
        Adjusted vader_score dict with added 'sarcasm_detected' flag
    """
    if detect_sarcasm(text):
        # Reduce compound score magnitude by 50%
        adjusted = vader_score.copy()
        adjusted['compound'] *= 0.5
        adjusted['sarcasm_detected'] = True
        logger.debug(f"Sarcasm detected in: '{text[:50]}...' - adjusted compound from {vader_score['compound']:.3f} to {adjusted['compound']:.3f}")
        return adjusted
    else:
        score = vader_score.copy()
        score['sarcasm_detected'] = False
        return score


def analyze_sentiment(tweets: List[Any]) -> SentimentResult:
    """
    Analyze sentiment of tweets using VADER

    Args:
        tweets: List of TweetData objects from x_scraper

    Returns:
        SentimentResult with aggregated sentiment analysis
    """
    if not tweets or len(tweets) == 0:
        logger.warning("No tweets to analyze, returning neutral sentiment")
        return SentimentResult(
            avg_sentiment=0.0,
            pos_pct=0.0,
            neg_pct=0.0,
            neu_pct=100.0,
            confidence="low",
            tweets_analyzed=0
        )

    analyzer = SentimentIntensityAnalyzer()
    scores = []
    sarcasm_count = 0

    tweet_scores = []  # Track individual scores for finding top tweets

    for tweet in tweets:
        # Get VADER score
        vader_score = analyzer.polarity_scores(tweet.text)

        # Adjust for sarcasm
        adjusted_score = adjust_for_sarcasm(vader_score, tweet.text)

        if adjusted_score['sarcasm_detected']:
            sarcasm_count += 1

        scores.append(adjusted_score['compound'])
        tweet_scores.append({
            'tweet': tweet,
            'compound': adjusted_score['compound'],
            'sarcasm': adjusted_score['sarcasm_detected']
        })

    # Calculate aggregates
    avg_sentiment = sum(scores) / len(scores) if scores else 0.0

    # Count positive/negative/neutral (using thresholds)
    pos_count = sum(1 for s in scores if s > 0.05)
    neg_count = sum(1 for s in scores if s < -0.05)
    neu_count = len(scores) - pos_count - neg_count

    pos_pct = (pos_count / len(scores)) * 100 if scores else 0.0
    neg_pct = (neg_count / len(scores)) * 100 if scores else 0.0
    neu_pct = (neu_count / len(scores)) * 100 if scores else 0.0

    # Determine confidence level
    # High confidence: >20 tweets, <30% sarcasm detected
    # Medium: 10-20 tweets OR 30-50% sarcasm
    # Low: <10 tweets OR >50% sarcasm
    sarcasm_pct = (sarcasm_count / len(tweets)) * 100 if tweets else 0

    if len(tweets) >= 20 and sarcasm_pct < 30:
        confidence = "high"
    elif len(tweets) >= 10 and sarcasm_pct < 50:
        confidence = "medium"
    else:
        confidence = "low"

    if sarcasm_pct > 30:
        logger.warning(f"High sarcasm detected: {sarcasm_pct:.1f}% of tweets flagged, confidence downgraded")

    # Find top positive and negative tweets
    sorted_by_compound = sorted(tweet_scores, key=lambda x: x['compound'], reverse=True)

    top_positive = None
    if sorted_by_compound and sorted_by_compound[0]['compound'] > 0.2:
        top_tweet = sorted_by_compound[0]
        top_positive = {
            'text': top_tweet['tweet'].text,
            'username': top_tweet['tweet'].username,
            'score': top_tweet['compound'],
            'sarcasm': top_tweet['sarcasm']
        }

    top_negative = None
    if sorted_by_compound and sorted_by_compound[-1]['compound'] < -0.2:
        top_tweet = sorted_by_compound[-1]
        top_negative = {
            'text': top_tweet['tweet'].text,
            'username': top_tweet['tweet'].username,
            'score': top_tweet['compound'],
            'sarcasm': top_tweet['sarcasm']
        }

    logger.info(f"Sentiment analysis complete: {len(tweets)} tweets, avg={avg_sentiment:.3f}, pos={pos_pct:.1f}%, neg={neg_pct:.1f}%, confidence={confidence}")

    return SentimentResult(
        avg_sentiment=avg_sentiment,
        pos_pct=pos_pct,
        neg_pct=neg_pct,
        neu_pct=neu_pct,
        confidence=confidence,
        tweets_analyzed=len(tweets),
        top_positive=top_positive,
        top_negative=top_negative
    )
