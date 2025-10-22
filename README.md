# VibeList

A simple, single-user Python script that sends you a daily email digest summarizing performance and sentiment for your stock portfolio using real-time X post insights from the Grok API.

## Features

- **Daily Portfolio Digest**: Automated email with portfolio performance and X sentiment analysis
- **Real-time Sentiment Analysis**: Uses Grok API to analyze X/Twitter posts about your stocks
- **Retro 80s Terminal UI**: Cool terminal-style email design with CRT monitor effects
- **Buy/Sell/Hold Recommendations**: AI-powered recommendations based on sentiment and price data
- **Portfolio Weighted Analysis**: Recommendations based on your actual portfolio allocation
- **Automated Scheduling**: Runs daily via GitHub Actions - no setup required

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/vibelist.git
cd vibelist
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Sample Configuration

```bash
python main.py --create-sample
```

This creates `config/portfolio.json` - edit it with your stocks and email:

```json
{
  "stocks": [
    {"symbol": "AAPL", "weight": 0.4},
    {"symbol": "TSLA", "weight": 0.3},
    {"symbol": "NVDA", "weight": 0.3}
  ],
  "email": "your-email@example.com"
}
```

### 4. Set Up API Keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your keys:
```
GROK_API_KEY=your_grok_api_key_here
RESEND_API_KEY=your_resend_api_key_here
FROM_EMAIL=noreply@yourdomain.com
TO_EMAIL=your_email@example.com
```

### 5. Test Configuration

```bash
python main.py --test
```

This will:
- Validate your configuration
- Test API connections
- Send a test email

### 6. Run Your First Digest

```bash
python main.py
```

## API Setup

### Grok API
1. Get access to Grok API at https://x.ai/
2. Generate an API key
3. Add it to your `.env` file

### Resend API (for Email)
1. Sign up at https://resend.com/
2. Verify your domain (for custom from email)
3. Generate an API key
4. Add it to your `.env` file

### Yahoo Finance
No setup required - uses free public API!

## Deployment Options

### Option 1: GitHub Actions (Recommended)

1. Fork this repository
2. Go to Settings → Secrets and variables → Actions
3. Add these repository secrets:
   - `GROK_API_KEY`: Your Grok API key
   - `RESEND_API_KEY`: Your Resend API key
   - `FROM_EMAIL`: Your verified email address
   - `TO_EMAIL`: Your recipient email

The daily digest will run automatically at 4:30 PM EST on weekdays.

### Option 2: Local Cron Job

1. Clone the repository locally
2. Set up your `.env` file
3. Add to your crontab:

```bash
# Run daily at 4:30 PM EST on weekdays
30 21 * * 1-5 cd /path/to/vibelist && /usr/bin/python3 main.py
```

### Option 3: Manual Execution

Run it manually whenever you want:

```bash
python main.py --log-level DEBUG
```

## Command Line Options

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH    Path to portfolio configuration file
  -t, --test           Test configuration and send test email
  -d, --dry-run        Generate digest without sending email
  --create-sample      Create sample portfolio configuration
  --log-level LEVEL    Set logging level (DEBUG|INFO|WARNING|ERROR)
```

## Portfolio Configuration

Your `config/portfolio.json` should look like this:

```json
{
  "stocks": [
    {"symbol": "AAPL", "weight": 0.4},
    {"symbol": "TSLA", "weight": 0.3},
    {"symbol": "NVDA", "weight": 0.2},
    {"symbol": "GOOGL", "weight": 0.1}
  ],
  "email": "your-email@example.com"
}
```

**Requirements:**
- Weights must sum to 1.0 (100%)
- All symbols must be valid stock tickers
- At least one stock is required

## Email Sample

The daily digest includes:

- **Portfolio Summary**: Overall score and market analysis
- **Individual Stock Analysis**: Price, change, sentiment, recommendation
- **Key Insights**: AI-generated insights about your portfolio
- **Top Performers**: Best and worst performing stocks

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Style

```bash
# Format code
black src/ main.py

# Check linting
flake8 src/ main.py
```

### Project Structure

```
vibelist/
├── src/vibelist/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── stock_data.py        # Yahoo Finance integration
│   ├── sentiment.py         # Grok API integration
│   ├── analyzer.py          # Analysis and recommendations
│   ├── email_generator.py   # HTML email generation
│   ├── email_sender.py      # Resend API integration
│   ├── exceptions.py        # Custom exceptions
│   └── utils.py             # Utility functions
├── templates/
│   └── email_template.html  # Retro 80s email template
├── config/                  # Portfolio configurations
├── logs/                    # Log files
├── .github/workflows/       # GitHub Actions
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Troubleshooting

### Common Issues

**1. "Portfolio configuration file not found"**
- Run `python main.py --create-sample` first
- Make sure `config/portfolio.json` exists

**2. "GROK_API_KEY environment variable is required"**
- Add your Grok API key to `.env` file
- Don't put quotes around the key

**3. "Failed to fetch stock data"**
- Check your internet connection
- Verify stock symbols are valid
- Try running with `--log-level DEBUG` for more details

**4. Email not sending**
- Verify Resend API key is correct
- Make sure your from email is verified in Resend
- Check your spam folder

### Debug Mode

Run with debug logging:

```bash
python main.py --log-level DEBUG
```

This will show detailed information about what's happening.

## Future Features

- [ ] Retro 80s website interface for configuration
- [ ] Multiple portfolio support
- [ ] SMS notifications
- [ ] Historical performance tracking
- [ ] Portfolio rebalancing suggestions
- [ ] Real-time alerts for major sentiment changes

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

If you run into issues:

1. Check the troubleshooting section above
2. Look at the logs in the `logs/` directory
3. Run with `--log-level DEBUG` for detailed output
4. Open an issue on GitHub

---

**Disclaimer**: This tool is for informational purposes only. Not financial advice. Always do your own research before making investment decisions.