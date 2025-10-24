"""
Reddit post/comment scraping using PRAW with date filtering and engagement sorting
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import praw

logger = logging.getLogger(__name__)

# Relevant stock-related subreddits
STOCK_SUBREDDITS = [
    'stocks',
    'investing',
    'wallstreetbets',
    'StockMarket',
    'options',
    'pennystocks',
    'RobinHood',
    'smallstreetbets',
]


class RedditPostData:
    """Structured Reddit post/comment data"""
    def __init__(self, text: str, author: str, created_utc: float, url: Optional[str] = None,
                 score: int = 0, num_comments: int = 0):
        self.text = text
        self.author = author
        self.created_utc = created_utc
        self.url = url
        self.score = score
        self.num_comments = num_comments
        self.parsed_date: Optional[datetime] = None
        self._parse_date()

    def _parse_date(self):
        """Parse Unix timestamp to datetime"""
        try:
            self.parsed_date = datetime.fromtimestamp(self.created_utc)
        except Exception as e:
            logger.debug(f"Date parse failed for '{self.created_utc}': {e}")
            self.parsed_date = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'text': self.text,
            'author': self.author,
            'created_utc': self.created_utc,
            'url': self.url,
            'score': self.score,
            'num_comments': self.num_comments
        }


def is_recent(post: RedditPostData, max_age_hours: int = 48) -> bool:
    """
    Check if post is recent enough

    Args:
        post: RedditPostData object
        max_age_hours: Maximum age in hours (default 48 = 2 days)

    Returns:
        True if post is within the age threshold
    """
    if not post.parsed_date:
        return False

    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    return post.parsed_date > cutoff


def fetch_reddit_posts(
    ticker: str,
    count: int = 30,
    max_age_hours: int = 48,
) -> List[RedditPostData]:
    """
    Fetch Reddit posts about a stock ticker using PRAW with date filtering

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        count: Number of posts to fetch
        max_age_hours: Maximum age of posts in hours (default: 48)

    Returns:
        List of RedditPostData objects sorted by engagement (score + comments)
    """
    try:
        logger.info(f"Fetching {count} Reddit posts for ${ticker} (last {max_age_hours}h)")

        # Get Reddit API credentials from environment
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "VibeList Stock Sentiment Bot v1.0")
        reddit_username = os.getenv("REDDIT_USERNAME")
        reddit_password = os.getenv("REDDIT_PASSWORD")

        if not client_id or not client_secret:
            logger.error("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env")
            return []

        # Initialize PRAW
        # For script apps: requires username/password
        # For web apps: can work read-only without username/password
        if reddit_username and reddit_password:
            logger.info("Using Reddit authentication with username/password (script app)")
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
                username=reddit_username,
                password=reddit_password,
            )
        else:
            logger.info("Using Reddit read-only mode (web app)")
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )

        logger.info(f"Connected to Reddit API (read-only: {reddit.read_only})")

        # Build search queries
        queries = [
            f"${ticker}",  # $AAPL
            f"{ticker} stock",  # AAPL stock
            ticker,  # AAPL
        ]

        all_posts: List[RedditPostData] = []
        seen_ids = set()

        # Search across multiple subreddits
        subreddit_str = '+'.join(STOCK_SUBREDDITS)
        subreddit = reddit.subreddit(subreddit_str)

        for query in queries:
            try:
                logger.debug(f"Searching Reddit for '{query}'")

                # Search with "new" sort to get recent posts
                search_results = subreddit.search(
                    query,
                    sort='new',
                    time_filter='week',  # Filter to last week
                    limit=count * 2  # Get more to filter
                )

                for submission in search_results:
                    try:
                        # Skip if we've seen this post
                        if submission.id in seen_ids:
                            continue

                        # Get post data
                        text = f"{submission.title}\n{submission.selftext}" if submission.selftext else submission.title
                        author = str(submission.author) if submission.author else "[deleted]"
                        created_utc = submission.created_utc
                        url = f"https://reddit.com{submission.permalink}"
                        score = submission.score
                        num_comments = submission.num_comments

                        # Create RedditPostData
                        post = RedditPostData(
                            text=text,
                            author=author,
                            created_utc=created_utc,
                            url=url,
                            score=score,
                            num_comments=num_comments
                        )

                        # Apply date filter
                        if not is_recent(post, max_age_hours=max_age_hours):
                            logger.debug(f"Filtering old post: {post.parsed_date}")
                            continue

                        # Skip very short posts
                        if len(post.text.strip()) < 20:
                            continue

                        seen_ids.add(submission.id)
                        all_posts.append(post)

                    except Exception as e:
                        logger.debug(f"Error parsing submission: {e}")
                        continue

            except Exception as e:
                logger.warning(f"Query '{query}' failed: {e}")
                continue

            # If we have enough posts, stop querying
            if len(all_posts) >= count:
                break

        # Sort by engagement (score + num_comments) - highest first
        all_posts.sort(key=lambda p: p.score + p.num_comments, reverse=True)

        # Limit to requested count
        final_posts = all_posts[:count]

        logger.info(f"Fetched {len(final_posts)} recent, high-engagement Reddit posts for ${ticker}")
        if final_posts:
            logger.info(f"Top Reddit posts by engagement:")
            for p in final_posts[:5]:
                engagement = p.score + p.num_comments
                ts = p.parsed_date.strftime("%Y-%m-%d %H:%M") if p.parsed_date else str(p.created_utc)
                logger.info(f" - [{ts}] u/{p.author}: {engagement} eng, {p.text[:60]}...")

        if len(final_posts) < 5:
            logger.warning(f"Only {len(final_posts)} Reddit posts found for ${ticker}")

        return final_posts

    except Exception as e:
        logger.error(f"Reddit scraping failed for ${ticker}: {e}", exc_info=True)
        return []


def fetch_reddit_data(ticker: str, count: int = 30) -> Dict[str, Any]:
    """
    Fetch Reddit posts using PRAW with date filtering and engagement sorting.

    Args:
        ticker: Stock ticker symbol
        count: Desired number of posts

    Returns:
        Dictionary with:
        - source: "reddit"
        - posts: List of RedditPostData objects sorted by engagement
        - error: Error message if any
    """
    posts = fetch_reddit_posts(ticker, count)

    # Return whatever we have; caller decides if it's sufficient
    error_msg = None
    if len(posts) < max(5, count // 3):
        error_msg = f"Only {len(posts)} Reddit posts found"

    return {
        'source': 'reddit',
        'posts': posts,
        'error': error_msg,
    }
