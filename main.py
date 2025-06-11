import os
from typing import Any, Optional, List, Dict
from src.tools import get_indian_stock_fundamentals, get_indian_stock_news, get_indian_stock_quote
from mcp.server.fastmcp import FastMCP
import logging
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create a timestamped log filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join(log_dir, f"stock_{timestamp}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Stock_Analysis_MCP")

@mcp.tool()
async def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """
    Get real-time Indian stock quote with automatic fallback between data sources.
    
    This tool fetches current stock prices, changes, volume, and market data for Indian stocks.
    It tries Yahoo Finance first for speed, then falls back to Alpha Vantage if needed.
    
    Args:
        symbol: Indian stock symbol (e.g., 'RELIANCE.NS', 'TCS.NS', 'INFY.BO', 'HDFCBANK.BO')
                The tool will automatically add .NS as default if any suffix is not provided.
    
    Returns:
        Dictionary with stock data including:
        - symbol: Stock symbol provided
        - current_price: Current trading price in INR
        - change: Price change from previous close
        - change_percent: Percentage change
        - day_high/day_low: Daily trading range
        - volume: Trading volume
        - previous_close: Previous day close price in INR
        - timestamp/latest_trading_day: When the price data was captured from the market.
                             Yahoo Finance: Unix timestamp of exact update time
                             Alpha Vantage: Date string (YYYY-MM-DD) of trading day
                             Use this to determine data freshness and market session relevance.
                             Recent timestamps indicate more reliable real-time data.
        - data_source: Which API provided the data
    
    Examples:
        - symbol="RELIANCE" for Reliance Industries
        - symbol="TCS" for Tata Consultancy Services
        - symbol="INFY" for Infosys
    
    Note: Works best during Indian market hours (9:15 AM - 3:30 PM IST, Mon-Fri)
    """
    logger.info(f"Fetching stock quote for symbol: {symbol}")
    
    try:
        # Call the function from your tools module
        quote_data = await get_indian_stock_quote(symbol)
        
        logger.info(f"Successfully retrieved quote for {symbol}")
        return {
            "success": True,
            "data": quote_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching stock quote for {symbol}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def get_stock_fundamentals(ticker: str) -> Dict[str, Any]:
    """
    Get comprehensive fundamental analysis data for Indian stocks.
    
    Retrieves detailed financial information including company info, financial statements,
    balance sheet, cash flow, and ESG sustainability data from Yahoo Finance.
    
    Args:
        ticker: Complete Indian stock ticker WITH exchange suffix
                Examples: 'INFY.NS', 'RELIANCE.NS', 'HDFCBANK.BO'
                Use .NS for NSE (National Stock Exchange)
                Use .BO for BSE (Bombay Stock Exchange)
    
    Returns:
        Dictionary containing:
        - info: Company details, ratios, market cap, P/E ratio, etc.
        - financials: Income statements for multiple years
        - balance_sheet: Assets, liabilities, equity data
        - cashflow: Operating, investing, financing cash flows
        - sustainability: ESG scores and environmental data (if available)
    
    Use Cases:
        - Financial analysis and valuation
        - Comparing company metrics
        - Investment research
        - Risk assessment
    
    Note: Some data may not be available for smaller companies
    """
    logger.info(f"Fetching stock fundamentals for ticker: {ticker}")
    
    try:
        # Call the function from your tools module
        fundamentals_data = get_indian_stock_fundamentals(ticker)
        
        logger.info(f"Successfully retrieved fundamentals for {ticker}")
        return {
            "success": True,
            "ticker": ticker,
            "data": fundamentals_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool()
async def get_stock_news(ticker: str, stock_name: str, query: Optional[str] = None, max_items: int = 10) -> Dict[str, Any]:
    """
    Get latest news articles about Indian stocks from multiple sources.
    
    Combines news from Yahoo Finance and Google News RSS to provide comprehensive
    coverage of company developments, earnings, market analysis, and industry news.
    
    Args:
        ticker: Stock ticker with exchange suffix (e.g., 'INFY.NS', 'RELIANCE.NS')
        stock_name: Full company name for better search results (e.g., 'Infosys', 'Reliance Industries')
        query: Custom search query to narrow down news (optional)
               Default searches for "{stock_name} stock India"
               Examples: "earnings", "merger", "quarterly results"
        max_items: Maximum number of news articles to return (1-50, default: 10)
    
    Returns:
        Dictionary with news articles containing:
        - title: Article headline
        - link: URL to full article
        - publisher: News source name
        - published: Publication timestamp
        - source: Whether from "Yahoo Finance" or "Google News"
    
    Best Practices:
        - Use official company names for better results
        - Recent news appears first (sorted by publication date)
        - Combine with scrape_article() to get full article content
    
    Examples:
        - ticker="TCS.NS", stock_name="Tata Consultancy Services"
        - ticker="HDFCBANK.NS", stock_name="HDFC Bank", query="quarterly earnings"
    """
    logger.info(f"Fetching stock news for {ticker} ({stock_name})")
    
    try:
        # Call the function from your tools module
        news_data = get_indian_stock_news(ticker, stock_name, query, max_items)
        
        logger.info(f"Successfully retrieved {len(news_data)} news items for {ticker}")
        return {
            "success": True,
            "ticker": ticker,
            "stock_name": stock_name,
            "news_count": len(news_data),
            "data": news_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker,
            "stock_name": stock_name,
            "timestamp": datetime.now().isoformat()
        }


@mcp.tool()
async def get_stock_analysis(ticker: str, stock_name: str, include_news: bool = True, max_news: int = 5) -> Dict[str, Any]:
    """
    Perform comprehensive stock analysis combining multiple data sources.
    
    This is a high-level tool that fetches and combines stock quote, fundamental data,
    and recent news into a single comprehensive report. Perfect for investment research.
    
    Args:
        ticker: Stock ticker with suffix (e.g., 'TCS.NS', 'RELIANCE.NS')
        stock_name: Full company name (e.g., 'Tata Consultancy Services')
        include_news: Whether to fetch recent news articles (default: True)
        max_news: Number of news articles to include if news is enabled (default: 5)
    
    Returns:
        Comprehensive dictionary containing:
        - quote: Real-time price, changes, volume data
        - fundamentals: Financial statements, ratios, company info
        - news: Recent articles (if include_news=True)
        - success: Overall success status
        - failed_components: List of any failed data sources
    
    Perfect For:
        - Investment decision making
        - Due diligence research
        - Market analysis reports
        - Portfolio review
    
    Example Usage:
        For quick analysis: include_news=False (faster)
        For full research: include_news=True, max_news=10
    
    Note: This tool may take 10-30 seconds to complete as it fetches from multiple sources
    """
    logger.info(f"Performing comprehensive analysis for {ticker} ({stock_name})")
    
    analysis_result = {
        "success": True,
        "ticker": ticker,
        "stock_name": stock_name,
        "timestamp": datetime.now().isoformat(),
        "data": {}
    }
    
    # Get stock quote
    try:
        quote_result = await get_stock_quote(ticker.replace('.NS', '').replace('.BO', ''))
        analysis_result["data"]["quote"] = quote_result
    except Exception as e:
        logger.error(f"Failed to get quote for {ticker}: {str(e)}")
        analysis_result["data"]["quote"] = {"success": False, "error": str(e)}
    
    # Get fundamentals
    try:
        fundamentals_result = await get_stock_fundamentals(ticker)
        analysis_result["data"]["fundamentals"] = fundamentals_result
    except Exception as e:
        logger.error(f"Failed to get fundamentals for {ticker}: {str(e)}")
        analysis_result["data"]["fundamentals"] = {"success": False, "error": str(e)}
    
    # Get news if requested
    if include_news:
        try:
            news_result = await get_stock_news(ticker, stock_name, max_items=max_news)
            analysis_result["data"]["news"] = news_result
        except Exception as e:
            logger.error(f"Failed to get news for {ticker}: {str(e)}")
            analysis_result["data"]["news"] = {"success": False, "error": str(e)}
    
    # Check if any component failed
    failed_components = []
    for component, result in analysis_result["data"].items():
        if not result.get("success", True):
            failed_components.append(component)
    
    if failed_components:
        analysis_result["success"] = False
        analysis_result["failed_components"] = failed_components
        logger.warning(f"Analysis for {ticker} completed with failures in: {', '.join(failed_components)}")
    else:
        logger.info(f"Comprehensive analysis completed successfully for {ticker}")
    
    return analysis_result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')