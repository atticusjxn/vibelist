# Reddit API Setup Guide

VibeList now supports **dual-source sentiment analysis** combining data from both **X (Twitter) and Reddit**!

## Why Reddit?

- ✅ **Official API** - No scraping, no account risk
- ✅ **Free tier** - 100 requests/minute, perfect for personal use
- ✅ **Rich discussions** - Subreddits like r/stocks, r/wallstreetbets, r/investing have active stock discussions
- ✅ **Better engagement data** - Upvotes + comments give quality signals
- ✅ **No login blocks** - Read-only access works reliably

## Setup Instructions

### Step 1: Create a Reddit App

1. **Log in to Reddit** at https://www.reddit.com/login

2. **Go to App Preferences**
   - Visit https://www.reddit.com/prefs/apps
   - Scroll to the bottom

3. **Click "Create App" or "Create Another App"**

4. **Fill in the form:**
   - **Name**: `VibeList Stock Sentiment` (or any name you like)
   - **App type**: Select **"script"** (important!)
   - **Description**: `Personal stock sentiment analysis for portfolio digest`
   - **About URL**: Leave blank
   - **Redirect URI**: `http://localhost:8080` (required but not used)
   - **Permissions**: Read-only is sufficient

5. **Click "Create app"**

### Step 2: Get Your Credentials

After creating the app, you'll see:

```
personal use script
<YOUR_CLIENT_ID>         ← This is under "personal use script"
───────────────────────
Secret: <YOUR_SECRET>    ← This is the client_secret
```

### Step 3: Update Your .env File

Add these three lines to your `.env` file:

```bash
# Reddit API Authentication
REDDIT_CLIENT_ID=<YOUR_CLIENT_ID>
REDDIT_CLIENT_SECRET=<YOUR_SECRET>
REDDIT_USER_AGENT=VibeList Stock Sentiment Bot v1.0
```

Replace `<YOUR_CLIENT_ID>` and `<YOUR_SECRET>` with the values from Step 2.

### Step 4: Test the Integration

Run a dry-run to test Reddit fetching:

```bash
python3 main.py --dry-run --log-level DEBUG
```

Look for logs like:

```
INFO - Fetching 30 Reddit posts for $AAPL (last 48h)
INFO - Connected to Reddit API (read-only: True)
INFO - $AAPL: Combined 0 tweets + 15 Reddit posts = 15 total
INFO - Sentiment analysis complete: 15 posts, avg=0.245, pos=60.0%, neg=20.0%, confidence=medium
```

## How It Works

### Dual-Source Sentiment

When `SENTIMENT_SOURCE=vader` (the current default), VibeList:

1. **Fetches from X/Twitter** using twikit (if credentials provided)
2. **Fetches from Reddit** using PRAW (if credentials provided)
3. **Combines both sources** into a single dataset
4. **Analyzes sentiment** using VADER on the combined posts
5. **Generates insights** based on all available data

### Subreddits Searched

The app automatically searches these stock-related subreddits:

- r/stocks
- r/investing
- r/wallstreetbets
- r/StockMarket
- r/options
- r/pennystocks
- r/RobinHood
- r/smallstreetbets

### Date Filtering

- **Time window**: Last 48 hours (configurable)
- **Sort by**: Engagement (upvotes + comments)
- **Filters out**: Very short posts, spam

## Example Output

With Reddit integrated, you'll see:

```
Analyzing X sentiment using mode: vader
────────────────────────────────────
$AAPL: Combined 0 tweets + 12 Reddit posts = 12 total
$TSLA: Combined 0 tweets + 25 Reddit posts = 25 total
$HOOD: Combined 0 tweets + 18 Reddit posts = 18 total

Successfully analyzed sentiment for 9 stocks
```

## Troubleshooting

### "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env"

- Make sure you've added the credentials to your `.env` file
- Check that there are no quotes around the values
- Verify the file is saved

### "No Reddit posts found for $AAPL"

- The stock might not have been discussed in the last 48 hours
- Try a more popular stock like TSLA or AAPL
- Check your Reddit API credentials are correct

### "403 Forbidden" errors

- Your app type might be wrong - it must be "script"
- Double-check your client_secret is correct
- Try regenerating your secret in Reddit app preferences

## Rate Limits

Reddit's free tier allows:

- **100 requests per minute**
- **10,000 requests per day**

For a portfolio of 9 stocks, you'll use approximately:
- 18 requests per run (2 queries × 9 stocks)
- Well within free tier limits

## Privacy & Security

- **Read-only access**: The app only reads public posts
- **No personal data**: Doesn't access your Reddit account
- **Anonymous**: Uses "script" authentication, not user login
- **Local only**: Credentials stored in local `.env` file only

## Next Steps

Now that Reddit is set up, you can:

1. **Compare sources**: See how X vs Reddit sentiment differs
2. **Rely on Reddit**: If X/Twitter blocks persist, Reddit provides reliable data
3. **Get richer insights**: Reddit discussions are often more detailed than tweets

---

**Status**: ✅ Reddit integration is ready to use!
**Cost**: $0/month (free tier)
**Reliability**: High (official API)