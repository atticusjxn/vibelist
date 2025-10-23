# VibeList - Claude Development Guide

## Project Overview

VibeList is a single-user Python application that sends daily email digests summarizing stock portfolio performance with real-time X (Twitter) sentiment analysis powered by xAI's Grok API. The app features a retro 80s terminal UI aesthetic in its email templates.

**Key Technologies:**
- Python 3.x
- xAI API (Grok) for sentiment analysis
- Yahoo Finance API for stock data
- Resend API for email delivery
- GitHub Actions for automated scheduling

## Architecture

### Core Components

```
src/vibelist/
├── config.py            # Configuration management and validation
├── stock_data.py        # Yahoo Finance integration
├── sentiment.py         # xAI API (Grok) integration
├── analyzer.py          # Analysis and buy/sell/hold recommendations
├── email_generator.py   # HTML email generation with retro styling
├── email_sender.py      # Resend API integration
├── exceptions.py        # Custom exception definitions
└── utils.py             # Utility functions
```

### Data Flow

1. **Configuration Loading** (`config.py`): Load portfolio config from `config.json`
2. **Stock Data Fetching** (`stock_data.py`): Get real-time price data from Yahoo Finance
3. **Sentiment Analysis** (`sentiment.py`): Query Grok for X post sentiment analysis
4. **Analysis** (`analyzer.py`): Generate buy/sell/hold recommendations based on data
5. **Email Generation** (`email_generator.py`): Create HTML email with retro 80s styling
6. **Email Sending** (`email_sender.py`): Send via Resend API

### Entry Point

`main.py` - CLI entry point with options:
- `--test`: Test configuration and send test email
- `--dry-run`: Generate digest without sending
- `--create-sample`: Create sample config.json
- `--log-level`: Set logging verbosity

## Development Guidelines

### Code Style
- Follow PEP 8 conventions
- Use Black for formatting
- Use flake8 for linting
- Type hints are encouraged but not strictly required

### Configuration Management
- Portfolio config in `config.json` (not committed to git)
- API keys in `.env` file (never committed)
- GitHub Actions uses repository secrets
- Sample config available via `--create-sample` flag

### Error Handling
- Custom exceptions defined in `exceptions.py`
- All API calls should have proper error handling
- Failed API calls should be logged with appropriate detail
- Graceful degradation where possible

### Logging
- Use Python's logging module
- Log levels: DEBUG, INFO, WARNING, ERROR
- Logs stored in `logs/` directory (if enabled)
- GitHub Actions captures stdout/stderr

## Testing

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Test Coverage
- Unit tests for core logic
- Integration tests for API interactions
- Configuration validation tests
- Email generation tests

### Testing Strategy
- Mock external APIs (xAI, Yahoo Finance, Resend) in unit tests
- Use test fixtures for sample portfolio data
- Test edge cases (missing data, API failures, invalid configs)

## Key Patterns

### Portfolio Configuration
```json
{
  "stocks": [
    {"symbol": "AAPL", "weight": 0.4},
    {"symbol": "TSLA", "weight": 0.3}
  ],
  "email": "user@example.com"
}
```

Requirements:
- Weights must sum to 1.0
- All symbols must be valid tickers
- At least one stock required

### Environment Variables
```
XAI_API_KEY=required
XAI_MODEL=optional (defaults to grok-4-fast)
XAI_API_BASE_URL=optional
RESEND_API_KEY=required
FROM_EMAIL=required
TO_EMAIL=required
```

### Email Template
- Located in `templates/email_template.html`
- Features retro 80s CRT monitor aesthetic
- Responsive design with terminal-style monospace fonts
- Uses CSS animations for scanline effects

## Deployment

### GitHub Actions
- Workflow: `.github/workflows/daily-digest.yml`
- Runs weekdays at 4:30 PM EST
- Uses repository secrets for configuration
- Can be triggered manually via workflow_dispatch

### Local Development
1. Clone repository
2. Create `.env` from `.env.example`
3. Run `python main.py --create-sample`
4. Edit `config.json` with your portfolio
5. Run `python main.py --test`

## API Integrations

### xAI API (Grok)
- Used for sentiment analysis of X posts
- Model: grok-4-fast (configurable)
- Queries recent posts about portfolio stocks
- Returns sentiment scores and insights

### Yahoo Finance
- Free public API (no key required)
- Real-time stock price data
- Historical price changes
- Market status information

### Resend
- Email delivery service
- Requires verified domain for custom from addresses
- Uses API key authentication
- HTML email support

## Common Tasks

### Adding New Stock Data Fields
1. Update `stock_data.py` to fetch new fields
2. Modify data structures in `analyzer.py`
3. Update email template in `templates/email_template.html`
4. Add corresponding CSS styling if needed

### Modifying Email Template
1. Edit `templates/email_template.html`
2. Test with `python main.py --dry-run` (generates HTML file)
3. Maintain retro 80s aesthetic
4. Keep responsive design principles

### Adding New Analysis Features
1. Implement logic in `analyzer.py`
2. Add any new data fetching to `stock_data.py` or `sentiment.py`
3. Update email template to display new insights
4. Add tests for new functionality

### Changing Scheduling
1. Edit `.github/workflows/daily-digest.yml`
2. Modify cron expression
3. Consider market hours and time zones

## Important Notes

### Security
- Never commit API keys or `.env` files
- Use GitHub secrets for CI/CD
- Validate all user input
- Sanitize data before email generation

### Performance
- API calls are sequential (not parallel)
- Rate limits: respect xAI and Yahoo Finance limits
- Email generation is synchronous
- Consider caching for frequently accessed data

### Maintenance
- Keep dependencies updated (requirements.txt)
- Monitor API changes (xAI, Yahoo Finance, Resend)
- Check GitHub Actions logs regularly
- Test email delivery periodically

### Future Enhancements
- Multiple portfolio support
- Historical performance tracking
- Real-time alerts
- Portfolio rebalancing suggestions
- Web interface for configuration
- SMS notifications

## Troubleshooting

### Common Issues
1. **API Key Errors**: Check `.env` file format (no quotes around values)
2. **Stock Data Failures**: Verify ticker symbols are valid
3. **Email Not Sending**: Verify Resend domain and API key
4. **Sentiment Analysis Errors**: Check xAI API quota and key validity

### Debug Mode
Always test with: `python main.py --log-level DEBUG`

## Resources

- xAI API Docs: https://x.ai/
- Yahoo Finance: Public API (via yfinance library)
- Resend Docs: https://resend.com/docs
- GitHub Actions Docs: https://docs.github.com/actions
