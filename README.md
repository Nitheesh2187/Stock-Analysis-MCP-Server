# Stock Analysis MCP Server

A Model Context Protocol (MCP) server implementation for comprehensive Indian stock market analysis, providing real-time quotes, fundamental data, news, and complete investment research capabilities.

## Features

- **Real-time Stock Quotes**: Get current prices, changes, volume, and market data
- **Fundamental Analysis**: Access financial statements, ratios, and company information
- **News Integration**: Latest stock news from multiple sources
- **Comprehensive Analysis**: Combined reports with quotes, fundamentals, and news
- **Automatic Fallback**: Multiple data sources with intelligent switching
- **Rate Limiting**: Built-in retry mechanisms and error handling
- **Logging**: Comprehensive logging for debugging and monitoring

## Installation

### Option 1: Clone and Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/Nitheesh2187/Stock-Analysis-MCP-Server.git
cd stock-analysis-mcp

# Install using pip
pip install .
```

### Option 2: Docker Installation

```bash
# Build the Docker image
docker build -t stock-mcp .

# Run with API key as environment variable
docker run -it --rm -e ALPHAVANTAGE_API_KEY=your_api_key stock-mcp

# Or run with environment file
docker run -it --rm --env-file .env stock-mcp
```

## Configuration

### Environment Variables

#### Required
- `ALPHAVANTAGE_API_KEY`: Your Alpha Vantage API key for financial data
  - Get your free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)


### Configuration Examples

Create a `.env` file in your project directory:

```bash
# Required API key
ALPHAVANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

## Usage with Claude Desktop

Add this configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["-m", "stock_mcp.server"],
      "env": {
        "ALPHAVANTAGE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```
NOTE: Make sure you install the package.

## Usage with Cursor

### Cursor v0.48.6+

1. Open Cursor Settings
2. Go to Features > MCP Servers
3. Click "+ Add new global MCP server"
4. Enter the following configuration:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["-m", "stock_mcp.server"],
      "env": {
        "ALPHAVANTAGE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cursor v0.45.6

1. Open Cursor Settings
2. Go to Features > MCP Servers
3. Click "+ Add New MCP Server"
4. Enter the following:
   - Name: "stock-analysis"
   - Type: "command"
   - Command: `python -m stock_mcp.server`
   - Environment Variables: `ALPHAVANTAGE_API_KEY=your_api_key_here`

## Available Tools

### 1. Get Stock Quote (`get_stock_quote`)

Get real-time stock quotes with automatic fallback between data sources.

**Best for:**
- Checking current stock prices and market data
- Getting quick price updates during trading hours
- Monitoring daily price movements

**Arguments:**
- `symbol` (string, required): Indian stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
  - The tool automatically adds .NS suffix if not provided
  - Supports both NSE (.NS) and BSE (.BO) symbols

**Example Usage:**
```json
{
  "name": "get_stock_quote",
  "arguments": {
    "symbol": "RELIANCE"
  }
}
```

**Returns:**
- Current price, change, change percentage
- Day high/low, volume, previous close
- Data source information and timestamp
- Market session relevance

### 2. Get Stock Fundamentals (`get_stock_fundamentals`)

Retrieve comprehensive fundamental analysis data for Indian stocks.

**Best for:**
- Investment research and valuation analysis
- Comparing company financial metrics
- Long-term investment decisions

**Arguments:**
- `ticker` (string, required): Complete stock ticker WITH exchange suffix
  - Examples: 'INFY.NS', 'RELIANCE.NS', 'HDFCBANK.BO'
  - .NS for NSE, .BO for BSE

**Example Usage:**
```json
{
  "name": "get_stock_fundamentals",
  "arguments": {
    "ticker": "TCS.NS"
  }
}
```

**Returns:**
- Company information and key metrics
- Financial statements (income, balance sheet, cash flow)
- Valuation ratios (P/E, P/B, etc.)
- ESG sustainability data (if available)

### 3. Get Stock News (`get_stock_news`)

Get latest news articles about Indian stocks from multiple sources.

**Best for:**
- Staying updated on company developments
- Research on recent events affecting stock price
- Monitoring earnings and corporate announcements

**Arguments:**
- `ticker` (string, required): Stock ticker with exchange suffix
- `stock_name` (string, required): Full company name for better search results
- `query` (string, optional): Custom search query to narrow results
- `max_items` (int, optional): Maximum articles to return (1-50, default: 10)

**Example Usage:**
```json
{
  "name": "get_stock_news",
  "arguments": {
    "ticker": "HDFCBANK.NS",
    "stock_name": "HDFC Bank",
    "query": "quarterly results",
    "max_items": 5
  }
}
```

**Returns:**
- Article titles, links, and publishers
- Publication timestamps
- Source attribution (Yahoo Finance or Google News)

### 4. Get Stock Analysis (`get_stock_analysis`)

Perform comprehensive stock analysis combining multiple data sources.

**Best for:**
- Complete investment research
- Due diligence for investment decisions
- Creating comprehensive stock reports

**Arguments:**
- `ticker` (string, required): Stock ticker with exchange suffix
- `stock_name` (string, required): Full company name
- `include_news` (bool, optional): Whether to include news (default: True)
- `max_news` (int, optional): Number of news articles if enabled (default: 5)

**Example Usage:**
```json
{
  "name": "get_stock_analysis",
  "arguments": {
    "ticker": "RELIANCE.NS",
    "stock_name": "Reliance Industries",
    "include_news": true,
    "max_news": 10
  }
}
```

**Returns:**
- Combined report with quotes, fundamentals, and news
- Success status for each component
- Comprehensive analysis ready for investment decisions

**Note:** This tool may take 10-30 seconds to complete as it fetches from multiple sources.

## How to Choose the Right Tool

Use this guide to select the appropriate tool for your needs:

| Tool | Best For | Speed | Data Depth |
|------|----------|-------|------------|
| `get_stock_quote` | Quick price checks | Fast | Basic |
| `get_stock_fundamentals` | Financial analysis | Medium | Deep |
| `get_stock_news` | Recent developments | Medium | Contextual |
| `get_stock_analysis` | Complete research | Slow | Comprehensive |

### Quick Reference

- **Need current price?** → Use `get_stock_quote`
- **Need financial data?** → Use `get_stock_fundamentals`
- **Need recent news?** → Use `get_stock_news`
- **Need everything?** → Use `get_stock_analysis`

## Data Sources

The server intelligently uses multiple data sources:

1. **Yahoo Finance**: Primary source for real-time quotes (fast, reliable)
2. **Alpha Vantage**: Fallback for quotes and primary for fundamentals
3. **Google News RSS**: News articles and market updates
4. **Yahoo Finance News**: Company-specific news and announcements

## Error Handling

The server includes robust error handling:

- Automatic fallback between data sources
- Retry mechanisms with exponential backoff
- Detailed error logging and reporting
- Graceful degradation when sources are unavailable

## Logging

Comprehensive logging system tracks:

- API calls and response times
- Data source usage and fallbacks
- Error conditions and retries
- User queries and system performance

Logs are stored in the `logs/` directory with timestamps.

## Market Hours

The tools work best during Indian market hours:
- **NSE/BSE Trading Hours**: 9:15 AM - 3:30 PM IST (Monday-Friday)
- **Pre-market**: 9:00 AM - 9:15 AM IST
- **After-market**: 3:40 PM - 4:00 PM IST

Outside market hours, the tools return the last available data with appropriate timestamps.

## Rate Limiting

The server implements intelligent rate limiting:
- Automatic retry with exponential backoff
- Respectful API usage to avoid hitting limits
- Smart caching to minimize redundant requests
- Fallback mechanisms when rate limits are reached

## Development

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Alpha Vantage API key

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd stock-analysis-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
python -m stock_mcp.server
```
### Reporting Issues

If you encounter any issues:

1. Check existing issues first
2. Provide detailed reproduction steps
3. Include error logs and environment details
4. Suggest potential solutions if possible

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- Open an issue on GitHub
- Check the documentation
- Review the logs for debugging information

## Acknowledgments

- Alpha Vantage for providing financial data API
- Yahoo Finance for real-time market data
- The MCP community for protocol development