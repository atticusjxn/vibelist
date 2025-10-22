"""
HTML email generation with retro 80s styling
"""

import os
from datetime import datetime
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import logging

from .analyzer import PortfolioAnalysis

logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generates HTML emails for VibeList digests"""

    def __init__(self, template_dir: str = "templates"):
        """
        Initialize email generator

        Args:
            template_dir: Directory containing email templates
        """
        self.template_dir = template_dir
        self.env = None
        self._setup_jinja_environment()

    def _setup_jinja_environment(self):
        """Setup Jinja2 environment with template directory"""
        try:
            if os.path.exists(self.template_dir):
                self.env = Environment(
                    loader=FileSystemLoader(self.template_dir),
                    autoescape=True
                )
                logger.info(f"Jinja2 environment setup with template dir: {self.template_dir}")
            else:
                logger.warning(f"Template directory not found: {self.template_dir}")
                # Fallback to inline template
                self.env = Environment(autoescape=True)

        except Exception as e:
            logger.error(f"Error setting up Jinja2 environment: {str(e)}")
            raise

    def generate_email_html(
        self,
        portfolio_analysis: PortfolioAnalysis,
        template_name: str = "email_template.html"
    ) -> str:
        """
        Generate HTML email from portfolio analysis

        Args:
            portfolio_analysis: Complete portfolio analysis
            template_name: Name of the template file

        Returns:
            Rendered HTML email content
        """
        try:
            logger.info("Generating HTML email content")

            # Prepare template context
            context = self._prepare_template_context(portfolio_analysis)

            # Load and render template
            if self.env and os.path.exists(os.path.join(self.template_dir, template_name)):
                template = self.env.get_template(template_name)
                html_content = template.render(**context)
            else:
                # Fallback to inline template
                logger.warning(f"Template {template_name} not found, using fallback")
                html_content = self._generate_fallback_html(context)

            logger.info("HTML email generation complete")
            return html_content

        except Exception as e:
            logger.error(f"Error generating HTML email: {str(e)}")
            raise

    def _prepare_template_context(self, portfolio_analysis: PortfolioAnalysis) -> Dict[str, Any]:
        """
        Prepare context data for template rendering

        Args:
            portfolio_analysis: Portfolio analysis data

        Returns:
            Dictionary with template context
        """
        context = {
            "portfolio_analysis": portfolio_analysis,
            "date_time": portfolio_analysis.last_updated.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_stocks": len(portfolio_analysis.stock_analyses),
        }

        # Add additional computed values
        context.update({
            "buy_count": sum(1 for a in portfolio_analysis.stock_analyses.values() if a.recommendation == "BUY"),
            "sell_count": sum(1 for a in portfolio_analysis.stock_analyses.values() if a.recommendation == "SELL"),
            "hold_count": sum(1 for a in portfolio_analysis.stock_analyses.values() if a.recommendation == "HOLD"),
        })

        return context

    def _generate_fallback_html(self, context: Dict[str, Any]) -> str:
        """
        Generate fallback HTML if template file is not available

        Args:
            context: Template context data

        Returns:
            Basic HTML email content
        """
        portfolio_analysis = context["portfolio_analysis"]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>VibeList Daily Digest</title>
            <style>
                body {{ font-family: monospace; background: #000; color: #0f0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ text-align: center; border-bottom: 2px solid #0f0; padding-bottom: 20px; }}
                .stock {{ border: 1px solid #0f0; padding: 10px; margin: 10px 0; }}
                .buy {{ background: rgba(0,255,0,0.1); }}
                .sell {{ background: rgba(255,0,0,0.1); }}
                .hold {{ background: rgba(255,255,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>VIBELIST DAILY DIGEST</h1>
                    <p>{context['date_time']}</p>
                </div>

                <div class="summary">
                    <h2>Portfolio Score: {portfolio_analysis.portfolio_score:+.3f}</h2>
                    <p>{portfolio_analysis.market_summary}</p>
                </div>

                <div class="stocks">
        """

        for symbol, analysis in portfolio_analysis.stock_analyses.items():
            css_class = analysis.recommendation.lower()
            html += f"""
                    <div class="stock {css_class}">
                        <h3>{analysis.symbol}</h3>
                        <p>Price: ${analysis.stock_info.current_price:.2f} ({analysis.stock_info.change_percent:+.2f}%)</p>
                        <p>Weight: {analysis.portfolio_weight*100:.1f}%</p>
                        <p>Sentiment: {analysis.sentiment_score.overall_sentiment:+.2f}</p>
                        <p><strong>{analysis.recommendation}</strong></p>
                        <p><em>{analysis.reasoning}</em></p>
                    </div>
            """

        html += """
                </div>

                <div class="insights">
                    <h2>Key Insights</h2>
        """

        for insight in portfolio_analysis.key_insights:
            html += f"<p>• {insight}</p>"

        html += """
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def generate_text_summary(self, portfolio_analysis: PortfolioAnalysis) -> str:
        """
        Generate plain text summary of the analysis

        Args:
            portfolio_analysis: Portfolio analysis data

        Returns:
            Plain text summary
        """
        try:
            lines = [
                "VIBELIST DAILY PORTFOLIO DIGEST",
                "=" * 40,
                f"Generated: {portfolio_analysis.last_updated.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "",
                "PORTFOLIO SUMMARY",
                "-" * 20,
                f"Portfolio Score: {portfolio_analysis.portfolio_score:+.3f}",
                f"Overall Sentiment: {portfolio_analysis.overall_sentiment:+.3f}",
                f"Market Summary: {portfolio_analysis.market_summary}",
                "",
                "STOCK ANALYSIS",
                "-" * 20,
            ]

            for symbol, analysis in portfolio_analysis.stock_analyses.items():
                lines.extend([
                    f"{symbol}:",
                    f"  Price: ${analysis.stock_info.current_price:.2f} ({analysis.stock_info.change_percent:+.2f}%)",
                    f"  Weight: {analysis.portfolio_weight*100:.1f}%",
                    f"  Sentiment: {analysis.sentiment_score.overall_sentiment:+.2f}",
                    f"  Recommendation: {analysis.recommendation}",
                    f"  Reasoning: {analysis.reasoning}",
                    ""
                ])

            lines.extend([
                "KEY INSIGHTS",
                "-" * 20,
            ])

            for insight in portfolio_analysis.key_insights:
                lines.append(f"• {insight}")

            if portfolio_analysis.top_performers:
                lines.append(f"Top Performers: {', '.join(portfolio_analysis.top_performers)}")

            if portfolio_analysis.underperformers:
                lines.append(f"Watch List: {', '.join(portfolio_analysis.underperformers)}")

            lines.extend([
                "",
                "=" * 40,
                "Powered by VibeList v1.0"
            ])

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error generating text summary: {str(e)}")
            return f"Error generating summary: {str(e)}"