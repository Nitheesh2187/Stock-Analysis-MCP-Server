import os
import httpx
import asyncio
from typing import Dict, Optional, Union
import yfinance as yf #ignore
import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import urllib.parse

# Load .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


def build_google_news_rss_url(query):
    encoded_query = urllib.parse.quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"


def parse_google_date(date_str: str) -> datetime:
    """
    Parse Google News RSS date format with proper error handling.
    
    Args:
        date_str: Date string from Google News RSS
        
    Returns:
        Parsed datetime object or datetime.min if parsing fails
    """
    try:
        # Google News RSS date format example: "Fri, 31 May 2024 06:00:00 GMT"
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return datetime.min
    except Exception as e:
        logger.error(f"Unexpected error parsing date '{date_str}': {e}")
        return datetime.min


def get_indian_stock_news(ticker: str, stock_name: str, query: str = None,max_items: int = 10) -> List[Dict[str, Any]]:
    """
    Combine latest news from yfinance and Google News RSS for an Indian stock.

    Args:
        ticker: Indian stock ticker in yfinance format, e.g. "INFY.NS"
        stock_name: Full company name or common name, e.g. "Infosys"
        max_items: Max combined number of news items to return

    Returns:
        List of dicts with keys: title, link, publisher/source, published (datetime)
        
    Raises:
        Exception: If both news sources fail to provide any data
    """
    logger.info(f"Fetching news for {ticker} ({stock_name}), max_items: {max_items}")
    
    combined_news = []
    yf_success = False
    google_success = False

    # 1. Fetch yfinance news
    try:
        logger.debug(f"Attempting to fetch Yahoo Finance news for {ticker}")
        stock = yf.Ticker(ticker)
        yf_news = stock.news or []
        
        logger.info(f"Retrieved {len(yf_news)} news items from Yahoo Finance")
        
        for i, item in enumerate(yf_news):
            try:
                # Validate required fields
                item = item["content"]
                if not item.get("title"):
                    logger.warning(f"Yahoo Finance news item {i} missing title, skipping")
                    continue
                
                # Handle timestamp conversion safely
                pub_time = datetime.min
                if item.get("pubDate"):
                    try:
                        pub_time = datetime.strptime(item["pubDate"], "%Y-%m-%dT%H:%M:%SZ")
                    except (ValueError, OSError) as e:
                        logger.warning(f"Invalid timestamp in Yahoo Finance news item {i}: {e}")
                
                #Extract the url
                logger.debug("Extracting the url from yfinance news response")
                url = ""
                if "canonicalUrl" in item:
                    url = item["canonicalUrl"].get("url","")
                elif "clickThroughUrl" in item:
                    url = item["clickThroughUrl"].get("url","")

                #Extract the provider
                logger.debug("Extracting the provider information from yfinance news response")
                if "provider" in item:
                    publisher = item["provider"]["displayName"]
                else:
                    publisher = "Unknown"
                
                if url:
                    combined_news.append({
                        "title": item.get("title", ""),
                        "link": url,
                        "publisher": publisher,
                        "published": pub_time,
                        "source": "Yahoo Finance",
                    })
                
            except Exception as e:
                logger.error(f"Error processing Yahoo Finance news item {i}: {e}")
                continue
        
        yf_success = True
        logger.debug(f"Successfully processed {len([n for n in combined_news if n['source'] == 'Yahoo Finance'])} Yahoo Finance news items")
        
    except Exception as e:
        logger.error(f"Failed to fetch Yahoo Finance news for {ticker}: {e}")

    # 2. Fetch Google News RSS
    try:
        logger.debug(f"Attempting to fetch Google News for '{stock_name}'")
        if query is None:
            query = f"{stock_name} stock India"
        
        rss_url = build_google_news_rss_url(query)
        
        # Add timeout and error handling for RSS feed parsing
        try:
            feed = feedparser.parse(rss_url)
            # Check if feed was parsed successfully
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"RSS feed parsing had issues: {getattr(feed, 'bozo_exception', 'Unknown error')}")
            
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in Google News RSS feed for query: {query}")
            else:
                logger.info(f"Retrieved {len(feed.entries)} news items from Google News")
                
                for i, entry in enumerate(feed.entries):
                    try:
                        # Validate required fields
                        if not entry.get("title"):
                            logger.warning(f"Google News entry {i} missing title, skipping")
                            continue
                        
                        pub_date = parse_google_date(entry.get("published", ""))
                        
                        # Extract publisher safely
                        publisher = "Unknown"
                        if hasattr(entry, 'source') and isinstance(entry.source, dict):
                            publisher = entry.source.get("title", "Unknown")
                        elif hasattr(entry, 'source'):
                            publisher = str(entry.source)
                        
                        combined_news.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "publisher": publisher,
                            "published": pub_date,
                            "source": "Google News",
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing Google News entry {i}: {e}")
                        continue
                
                google_success = True
                logger.debug(f"Successfully processed {len([n for n in combined_news if n['source'] == 'Google News'])} Google News items")
        
        except Exception as e:
            logger.error(f"Error parsing RSS feed from {rss_url}: {e}")
            
    except Exception as e:
        logger.error(f"Failed to fetch Google News for '{stock_name}': {e}")

    # Check if we got any news at all
    if not combined_news:
        error_msg = f"Failed to retrieve news from both Yahoo Finance and Google News for {ticker}"
        logger.error(error_msg)
        if not yf_success and not google_success:
            raise Exception(error_msg)
    
    # Sort combined news by published date (descending)
    try:
        combined_news.sort(key=lambda x: x["published"], reverse=True)
        logger.info(f"Successfully combined and sorted {len(combined_news)} news items")
    except Exception as e:
        logger.error(f"Error sorting news items: {e}")

    # Return requested number of items
    result = combined_news[:max_items]
    logger.info(f"Returning {len(result)} news items for {ticker}")
    
    return result


def get_indian_stock_fundamentals(ticker: str):
    """
    Gets all available fundamentals for an Indian stock from Yahoo Finance.
    
    Args:
        ticker: Stock ticker, e.g. "INFY.NS" for Infosys on NSE
        
    Returns:
        Dictionary containing stock fundamentals data
        
    Raises:
        Exception: If unable to fetch any fundamental data
    """
    logger.info(f"Fetching fundamentals for ticker: {ticker}")
    
    # Ensure proper suffix for Indian stocks
    original_ticker = ticker
    if not (ticker.endswith('.NS') or ticker.endswith('.BO')):
        ticker += '.NS'  # Default to NSE
    
    try:
        stock = yf.Ticker(ticker)
        logger.debug(f"Created yfinance Ticker object for {ticker}")
        
        data = {}
        try :
            logger.debug("Fetecting stock fundamenals....")

            # INFO
            info = stock.info
            if info:
                data["info"] = info
                logger.info(f"Successfully retrieved stock info ({len(info)} fields)")
            else:
                logger.warning("Stock info is empty")
                data["info"] = {}    

            # FINANCIALS
            financials = stock.financials
            if financials is not None and not financials.empty:
                data["financials"] = financials.to_dict()
                logger.info(f"Successfully retrieved financials ({financials.shape[0]} rows)")
            else:
                logger.warning("Financials are empty or None")
                data["financials"] = {}
            
            # BALANCE SHEET
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                data["balance_sheet"] = balance_sheet.to_dict()
                logger.info(f"Successfully retrieved balance sheet ({balance_sheet.shape[0]} rows)")
            else:
                logger.warning("Balance sheet is empty or None")
                data["balance_sheet"] = {}

            # CASHFLOW
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty:
                data["cashflow"] = cashflow.to_dict()
                logger.info(f"Successfully retrieved cash flow ({cashflow.shape[0]} rows)")
            else:
                logger.warning("Cash flow is empty or None")
                data["cashflow"] = {}

            # SUSTAINABILITY
            sustainability = stock.sustainability
            if sustainability is not None and not sustainability.empty:
                data["sustainability"] = sustainability.to_dict()
                logger.info("Successfully retrieved sustainability data")
            else:
                logger.debug("Sustainability data not available (normal for many stocks)")
                data["sustainability"] = {}

        except Exception as e:
            error_msg = f"Failed to fetch fundamentals: {e}"
            logger.error(error_msg)

        return data
    
    except Exception as e:
        if "No fundamental data available" in str(e):
            raise  # Re-raise our custom exception
        else:
            error_msg = f"Unexpected error fetching fundamentals for {ticker}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)


async def get_indian_stock_quote(symbol: str) -> Dict:
    """
    Get Indian stock quote with fallback mechanism.
    Tries Yahoo Finance first, then Alpha Vantage if Yahoo fails.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        api_key: Alpha Vantage API key (optional, required only if Yahoo fails)
    
    Returns:
        Dictionary containing stock data
    
    Raises:
        Exception: If both APIs fail to fetch data
    """
    
    # First attempt: Yahoo Finance
    try:
        logger.info(f"Attempting to fetch {symbol} from Yahoo Finance...")
        result = await get_indian_stock_quote_yahoo(symbol)
        logger.info(f"Successfully fetched {symbol} from Yahoo Finance")
        result['data_source'] = 'Yahoo Finance'
        return result
        
    except Exception as yahoo_error:
        logger.warning(f"Yahoo Finance failed for {symbol}: {str(yahoo_error)}")
        
        # Second attempt: Alpha Vantage (only if API key is provided)
        try:
            logger.info(f"Attempting to fetch {symbol} from Alpha Vantage...")
            result = await get_indian_stock_quote_alphavantage(symbol)
            logger.info(f"Successfully fetched {symbol} from Alpha Vantage")
            result['data_source'] = 'Alpha Vantage'
            return result
            
        except Exception as av_error:
            logger.error(f"Alpha Vantage also failed for {symbol}: {str(av_error)}")
            raise Exception(f"Both APIs failed - Yahoo: {str(yahoo_error)}, Alpha Vantage: {str(av_error)}")


async def get_indian_stock_quote_yahoo(symbol: str) -> Dict:
    """
    Get Indian stock quote using Yahoo Finance API
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE.NS', 'TCS.NS', 'INFY.NS')
                Add .NS suffix for NSE stocks, .BO for BSE stocks
    
    Returns:
        Dictionary containing stock data
    """
    # Ensure proper suffix for Indian stocks
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        symbol += '.NS'  # Default to NSE
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data['chart']['error'] is not None:
                raise Exception(f"API Error: {data['chart']['error']}")
            
            result = data['chart']['result'][0]
            meta = result['meta']
            
            # Extract current price data
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('previousClose', 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'previous_close': previous_close,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'day_high': meta.get('regularMarketDayHigh', 0),
                'day_low': meta.get('regularMarketDayLow', 0),
                'volume': meta.get('regularMarketVolume', 0),
                'timestamp': meta.get('regularMarketTime', 0)
            }
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Error fetching stock data: {str(e)}")


async def get_indian_stock_quote_alphavantage(symbol: str) -> Dict:
    """
    Get Indian stock quote using Alpha Vantage API
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        api_key: Your Alpha Vantage API key (free at alphavantage.co)
    
    Returns:
        Dictionary containing stock data
    """
    # Add .BSE suffix for Alpha Vantage Indian stocks
    if not symbol.endswith('.BSE'):
        symbol += '.BSE'
    
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if 'Global Quote' not in data:
                raise Exception("Invalid response or API limit reached")
            
            quote = data['Global Quote']
            
            return {
                'symbol': quote.get('01. symbol', symbol),
                'current_price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'day_high': float(quote.get('03. high', 0)),
                'day_low': float(quote.get('04. low', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'latest_trading_day': quote.get('07. latest trading day', 'N/A')
            }
            
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Error fetching stock data: {str(e)}")



# Example usage
async def main():
    # Example 1: Using Yahoo Finance (no API key needed)
    try:
        reliance_data = await get_indian_stock_quote_yahoo('RELIANCE.NS')
        print("Reliance Stock Data:")
        print(f"Price: ₹{reliance_data['current_price']}")
        print(f"Change: {reliance_data['change']} ({reliance_data['change_percent']}%)")
        print(f"Day Range: ₹{reliance_data['day_low']} - ₹{reliance_data['day_high']}")
        print()
    except Exception as e:
        print(f"Error: {e}")
    
    # # Example 2: Using Alpha Vantage (requires API key)
    # try:
    #     tcs_data = await get_indian_stock_quote_alphavantage('TCS')
    #     print(tcs_data)
    #     print("TCS Stock Data:")
    #     print(f"Price: ₹{tcs_data['current_price']}")
    #     print(f"Change: {tcs_data['change']} ({tcs_data['change_percent']}%)")
    #     print()
    # except Exception as e:
    #     print(f"Error: {e}")

    
    # # Example 3: Fundamentals
    # try:
    #     infosys_fundamentals = get_indian_stock_fundamentals("INFY.NS")
    #     print("INFOSYS Stock fundamentals:")
    #     # print(infosys_fundamentals)
    #     print("INFO: ", infosys_fundamentals["info"])
    #     print("BALANCE SHEET: ",infosys_fundamentals["balance_sheet"])
    #     print("CASHFLOW: ",infosys_fundamentals["cashflow"])
    #     print("SUSTAINABILITY: ",infosys_fundamentals["sustainability"])
    # except Exception as e:
    #     print(f"Error for extracting fundamentals: ", e)
    
    # # Example 4: News
    # try:
    #     hdfc_news = get_indian_stock_news("HDFCBANK.NS","HDFC Bank")
    #     print("NEWS LINKS: ", hdfc_news)
    # except Exception as e:
    #     print(f"Error in extracting news links: ", e)


# Popular Indian stock symbols for reference
POPULAR_INDIAN_STOCKS = {
    'RELIANCE.NS': 'Reliance Industries',
    'TCS.NS': 'Tata Consultancy Services',
    'INFY.NS': 'Infosys',
    'HDFCBANK.NS': 'HDFC Bank',
    'ICICIBANK.NS': 'ICICI Bank',
    'HINDUNILVR.NS': 'Hindustan Unilever',
    'ITC.NS': 'ITC Limited',
    'SBIN.NS': 'State Bank of India',
    'BHARTIARTL.NS': 'Bharti Airtel',
    'KOTAKBANK.NS': 'Kotak Mahindra Bank'
}

if __name__ == "__main__":
    asyncio.run(main())