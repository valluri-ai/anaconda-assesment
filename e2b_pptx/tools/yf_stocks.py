from environs import Env
from langsmith import expect
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, TypedDict
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
import logging
from dotenv import load_dotenv
import time
import json
import os
import socket
import tempfile
import subprocess
import asyncio
from langchain_sandbox import PyodideSandbox
import threading
import signal

import requests

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
env = Env()
env.read_env()

# E2B_API_KEY = env.str('E2B_API_KEY')
# ANTHROPIC_API_KEY = env.str('ANTHROPIC_API_KEY')
# E2B_TEMPLATE_ID = env.str('E2B_TEMPLATE_ID')

class StYahooFinanceArgs(BaseModel):
    user_story: str = Field(description="User story for the financial dashboard")
    software_requirements: str = Field(description="Software requirements for the financial dashboard")
    features: str = Field(description="Features for the financial dashboard")
    key_details: str = Field(description="Key details for the financial dashboard")
    userID: str = Field(description="User ID for the financial dashboard")

class CodeFile(BaseModel):
    file_path: str
    file_content: str

class FragmentSchema(BaseModel):
    '''Schema for the Python financial dashboard generator.
    Example code:
    ```python
    import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy.stats import norm

@st.cache_data
def load_stock_data(symbol: str, period: str):
    """Cached function to load stock data"""
    stock = yf.Ticker(symbol)
    data = stock.history(period=period)
    return data, stock.info

class FinancialAnalyticsDashboard:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.setup_sidebar()
        
    def setup_sidebar(self):
        st.sidebar.title("📈 Advanced Analytics")
        
        # Stock Selection
        self.symbol = st.sidebar.text_input("Enter Stock Symbol", "AAPL").upper()
        
        # Time Period
        self.period = st.sidebar.selectbox(
            "Select Time Period",
            ["1y", "2y", "5y", "10y", "max"],
            index=0
        )
        
        # Analysis Options
        st.sidebar.subheader("Analysis Options")
        self.show_technical = st.sidebar.checkbox("Technical Analysis", True)
        self.show_volatility = st.sidebar.checkbox("Volatility Analysis", True)
        self.show_var = st.sidebar.checkbox("Value at Risk (VaR)", True)
        self.show_monte_carlo = st.sidebar.checkbox("Monte Carlo Simulation", True)
        
    def calculate_technical_indicators(self, data):
        # Moving averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # Bollinger Bands
        data['BB_middle'] = data['Close'].rolling(window=20).mean()
        data['BB_upper'] = data['BB_middle'] + 2*data['Close'].rolling(window=20).std()
        data['BB_lower'] = data['BB_middle'] - 2*data['Close'].rolling(window=20).std()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        return data
        
    def plot_technical_analysis(self, data):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Price and MA
        fig.add_trace(go.Candlestick(x=data.index,
                                    open=data['Open'],
                                    high=data['High'],
                                    low=data['Low'],
                                    close=data['Close'],
                                    name='OHLC'),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'],
                                name='SMA 20', line=dict(color='orange')),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_upper'],
                                name='BB Upper', line=dict(dash='dash')),
                     row=1, col=1)
        
        fig.add_trace(go.Scatter(x=data.index, y=data['BB_lower'],
                                name='BB Lower', line=dict(dash='dash')),
                     row=1, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI'],
                                name='RSI', line=dict(color='purple')),
                     row=2, col=1)
        
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        fig.update_layout(height=800, title_text="Technical Analysis")
        return fig
        
    def calculate_volatility(self, data):
        # Daily Returns
        data['Returns'] = data['Close'].pct_change()
        
        # Historical Volatility (20-day)
        data['Volatility'] = data['Returns'].rolling(window=20).std() * np.sqrt(252)
        
        return data
        
    def plot_volatility(self, data):
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=data.index, y=data['Volatility'],
                                name='20-day Volatility',
                                line=dict(color='red')))
        
        fig.update_layout(title='Historical Volatility',
                         yaxis_title='Annualized Volatility',
                         height=400)
        return fig
        
    def calculate_var(self, data, confidence_level=0.95):
        returns = data['Returns'].dropna()
        var = np.percentile(returns, (1-confidence_level)*100)
        cvar = returns[returns <= var].mean()
        
        return {
            'VaR': var,
            'CVaR': cvar
        }
        
    def monte_carlo_simulation(self, data, simulations=1000, days=252):
        returns = data['Returns'].dropna()
        mu = returns.mean()
        sigma = returns.std()
        
        sim_results = []
        last_price = data['Close'].iloc[-1]
        
        for _ in range(simulations):
            prices = [last_price]
            for _ in range(days):
                prices.append(prices[-1] * np.exp(np.random.normal(mu, sigma)))
            sim_results.append(prices)
            
        return np.array(sim_results)
        
    def plot_monte_carlo(self, simulations):
        fig = go.Figure()
        
        for sim in simulations[:100]:  # Plot first 100 simulations
            fig.add_trace(go.Scatter(y=sim, mode='lines',
                                   line=dict(width=0.5, color='blue'),
                                   opacity=0.1,
                                   showlegend=False))
            
        fig.add_trace(go.Scatter(y=simulations.mean(axis=0),
                                name='Average',
                                line=dict(color='red', width=2)))
                                
        fig.update_layout(title='Monte Carlo Simulation (1 Year Forecast)',
                         yaxis_title='Stock Price',
                         height=400)
        return fig
        
    def run(self):
        st.title(f"Advanced Financial Analytics - {self.symbol}")
        
        try:
            # Use the cached function instead of the class method
            data, info = load_stock_data(self.symbol, self.period)
            
            # Current Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", 
                         f"${data['Close'].iloc[-1]:.2f}",
                         f"{data['Close'].pct_change().iloc[-1]:.2%}")
            with col2:
                st.metric("Volume",
                         f"{data['Volume'].iloc[-1]:,.0f}")
            with col3:
                st.metric("Market Cap",
                         f"${info.get('marketCap', 0)/1e9:.2f}B")
            with col4:
                st.metric("52 Week High",
                         f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
            
            # Technical Analysis
            if self.show_technical:
                data = self.calculate_technical_indicators(data)
                st.plotly_chart(self.plot_technical_analysis(data),
                              use_container_width=True)
                
            # Volatility Analysis
            if self.show_volatility:
                data = self.calculate_volatility(data)
                st.plotly_chart(self.plot_volatility(data),
                              use_container_width=True)
                
            # Value at Risk
            if self.show_var:
                var_metrics = self.calculate_var(data)
                st.subheader("Value at Risk Analysis (95% Confidence)")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Daily VaR", f"{var_metrics['VaR']:.2%}")
                with col2:
                    st.metric("Daily CVaR", f"{var_metrics['CVaR']:.2%}")
                    
            # Monte Carlo Simulation
            if self.show_monte_carlo:
                st.subheader("Monte Carlo Simulation")
                simulations = self.monte_carlo_simulation(data)
                st.plotly_chart(self.plot_monte_carlo(simulations),
                              use_container_width=True)
                
                # Simulation Statistics
                final_prices = simulations[:, -1]
                st.write("Simulation Results (1 Year Forecast):")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Expected Price",
                             f"${np.mean(final_prices):.2f}")
                with col2:
                    st.metric("95% Confidence Upper Bound",
                             f"${np.percentile(final_prices, 95):.2f}")
                with col3:
                    st.metric("95% Confidence Lower Bound",
                             f"${np.percentile(final_prices, 5):.2f}")
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    dashboard = FinancialAnalyticsDashboard()
    dashboard.run()                                  

another example that works:
 import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler

class PortfolioAnalyzer:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.setup_sidebar()

    def setup_sidebar(self):
        st.sidebar.title("💼 Portfolio Analysis")
        
        # Portfolio Selection
        self.tickers = st.sidebar.text_input(
            "Enter Stock Symbols (comma-separated)", 
            "AAPL,MSFT,GOOGL,AMZN"
        ).upper().split(',')
        
        # Analysis Period
        self.period = st.sidebar.selectbox(
            "Analysis Period",
            ["1y", "2y", "3y", "5y"],
            index=0
        )
        
        # Portfolio Weights
        st.sidebar.subheader("Portfolio Weights")
        self.weights = []
        for ticker in self.tickers:
            weight = st.sidebar.slider(
                f"{ticker} Weight (%)",
                0, 100, 
                value=int(100/len(self.tickers))
            )
            self.weights.append(weight/100)

@st.cache_data
def fetch_data(tickers, period):
    data = pd.DataFrame()
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)['Close']
        data[ticker] = hist
    return data

@st.cache_data
def calculate_portfolio_metrics(data, weights):
    # Returns
    returns = data.pct_change()
    
    # Portfolio Return
    portfolio_return = np.sum(returns.mean() * weights) * 252
    
    # Portfolio Volatility
    portfolio_vol = np.sqrt(
        np.dot(weights, np.dot(returns.cov() * 252, weights))
    )
    
    # Sharpe Ratio (assuming rf=0.02)
    sharpe = (portfolio_return - 0.02) / portfolio_vol
    
    # Maximum Drawdown
    portfolio_value = (1 + (returns * weights).sum(axis=1)).cumprod()
    rolling_max = portfolio_value.expanding().max()
    drawdown = (portfolio_value - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    return {
        'return': portfolio_return,
        'volatility': portfolio_vol,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown
    }

def create_correlation_heatmap(returns):
    corr_matrix = returns.corr().round(2)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        hoverongaps=False,
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1
    ))
    
    fig.update_layout(
        title='Correlation Matrix',
        height=500,
        width=700
    )
    
    return fig

def create_efficient_frontier(returns, n_portfolios=1000):
    n_assets = returns.shape[1]
    returns_array = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    
    portfolios_returns = []
    portfolios_vols = []
    
    for _ in range(n_portfolios):
        weights = np.random.random(n_assets)
        weights = weights / np.sum(weights)
        
        portfolio_return = np.sum(returns_array * weights)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        portfolios_returns.append(portfolio_return)
        portfolios_vols.append(portfolio_vol)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolios_vols,
        y=portfolios_returns,
        mode='markers',
        marker=dict(
            size=5,
            color=np.array(portfolios_returns)/np.array(portfolios_vols),
            colorscale='Viridis',
            showscale=True
        ),
        name='Simulated Portfolios'
    ))
    
    fig.update_layout(
        title='Efficient Frontier',
        xaxis_title='Volatility',
        yaxis_title='Expected Return',
        height=600
    )
    
    return fig

class PortfolioApp:
    def __init__(self):
        self.analyzer = PortfolioAnalyzer()
        
    def run(self):
        st.title("Advanced Portfolio Analysis")
        
        try:
            # Fetch Data
            data = fetch_data(self.analyzer.tickers, self.analyzer.period)
            
            # Calculate returns
            returns = data.pct_change().dropna()
            
            # Portfolio Metrics
            metrics = calculate_portfolio_metrics(data, self.analyzer.weights)
            
            # Display Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Expected Return",
                    f"{metrics['return']:.2%}"
                )
            with col2:
                st.metric(
                    "Portfolio Volatility",
                    f"{metrics['volatility']:.2%}"
                )
            with col3:
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics['sharpe']:.2f}"
                )
            with col4:
                st.metric(
                    "Maximum Drawdown",
                    f"{metrics['max_drawdown']:.2%}"
                )
            
            # Price Evolution
            st.subheader("Price Evolution")
            scaled_data = pd.DataFrame(
                MinMaxScaler().fit_transform(data),
                columns=data.columns,
                index=data.index
            )
            fig = px.line(scaled_data, title="Normalized Price Evolution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlation Heatmap
            st.subheader("Correlation Analysis")
            corr_fig = create_correlation_heatmap(returns)
            st.plotly_chart(corr_fig, use_container_width=True)
            
            # Efficient Frontier
            st.subheader("Portfolio Optimization")
            ef_fig = create_efficient_frontier(returns)
            st.plotly_chart(ef_fig, use_container_width=True)
            
            # Rolling Statistics
            st.subheader("Rolling Statistics")
            window = st.slider("Rolling Window (days)", 20, 252, 60)
            
            rolling_returns = returns.rolling(window).mean() * 252
            rolling_vol = returns.rolling(window).std() * np.sqrt(252)
            
            col1, col2 = st.columns(2)
            with col1:
                fig_rr = px.line(rolling_returns, title=f"{window}-day Rolling Returns")
                st.plotly_chart(fig_rr, use_container_width=True)
            
            with col2:
                fig_rv = px.line(rolling_vol, title=f"{window}-day Rolling Volatility")
                st.plotly_chart(fig_rv, use_container_width=True)
            
            # Risk Contribution
            risk_contrib = (self.analyzer.weights * 
                          (np.dot(returns.cov() * 252, self.analyzer.weights))) / metrics['volatility']
            
            st.subheader("Risk Contribution Analysis")
            fig_risk = px.pie(
                values=risk_contrib,
                names=self.analyzer.tickers,
                title="Risk Contribution by Asset"
            )
            st.plotly_chart(fig_risk)
            
        except Exception as e:
            st.error(f"Error in analysis: {str(e)}")

if __name__ == "__main__":
    app = PortfolioApp()
    app.run()

And one more example that works:
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

class SectorAnalysis:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.setup_sidebar()
        
    def setup_sidebar(self):
        st.sidebar.title("🏢 Sector & Stock Analysis")
        
        # Sector selection
        self.sectors = {
            "Technology": ["AAPL", "MSFT", "NVDA", "AMD", "INTC"],
            "Healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK"],
            "Finance": ["JPM", "BAC", "GS", "MS", "WFC"],
            "Consumer": ["AMZN", "WMT", "COST", "PG", "KO"],
            "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"]
        }
        
        self.selected_sector = st.sidebar.selectbox(
            "Select Sector",
            list(self.sectors.keys())
        )
        
        # Time period
        self.period = st.sidebar.selectbox(
            "Analysis Period",
            ["1mo", "3mo", "6mo", "1y", "2y"],
            index=2
        )
        
        # Analysis options
        st.sidebar.subheader("Analysis Options")
        self.show_fundamentals = st.sidebar.checkbox("Show Fundamentals", True)
        self.show_performance = st.sidebar.checkbox("Show Performance", True)
        self.show_volatility = st.sidebar.checkbox("Show Volatility", True)

@st.cache_data
def fetch_sector_data(tickers, period):
    """Fetch data for entire sector"""
    data = pd.DataFrame()
    stock_info = {}
    
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        # Get historical data
        hist = stock.history(period=period)['Close']
        data[ticker] = hist
        # Get stock info
        stock_info[ticker] = {
            'marketCap': stock.info.get('marketCap', 0),
            'peRatio': stock.info.get('peRatio', 0),
            'forwardPE': stock.info.get('forwardPE', 0),
            'dividendYield': stock.info.get('dividendYield', 0),
            'beta': stock.info.get('beta', 0),
            'volume': stock.info.get('volume', 0)
        }
    
    return data, stock_info

def calculate_sector_metrics(data, stock_info):
    """Calculate key sector metrics"""
    returns = data.pct_change()
    
    metrics = {
        'daily_returns': returns.mean(),
        'volatility': returns.std() * np.sqrt(252),
        'sharpe': (returns.mean() * 252 - 0.02) / (returns.std() * np.sqrt(252)),
        'beta': pd.Series({ticker: info['beta'] for ticker, info in stock_info.items()}),
        'market_cap': pd.Series({ticker: info['marketCap']/1e9 for ticker, info in stock_info.items()}),
        'pe_ratio': pd.Series({ticker: info['peRatio'] for ticker, info in stock_info.items()}),
    }
    
    return metrics

def create_performance_chart(data):
    """Create relative performance chart"""
    normalized = data / data.iloc[0] * 100
    
    fig = go.Figure()
    for col in normalized.columns:
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized[col],
            name=col,
            mode='lines'
        ))
    
    fig.update_layout(
        title="Relative Performance",
        yaxis_title="Normalized Price (%)",
        height=500
    )
    
    return fig

def create_volatility_surface(returns):
    """Create volatility surface"""
    rolling_vol = returns.rolling(window=20).std() * np.sqrt(252) * 100
    
    fig = go.Figure(data=[
        go.Surface(
            z=rolling_vol.values.T,
            x=rolling_vol.index,
            y=rolling_vol.columns,
            colorscale='Viridis'
        )
    ])
    
    fig.update_layout(
        title='Volatility Surface',
        scene=dict(
            xaxis_title='Date',
            yaxis_title='Stock',
            zaxis_title='Volatility (%)'
        ),
        height=700
    )
    
    return fig

def create_fundamental_comparison(stock_info):
    """Create fundamental metrics comparison"""
    metrics = pd.DataFrame(stock_info).T
    
    fig = go.Figure()
    
    # Market Cap
    fig.add_trace(go.Bar(
        x=metrics.index,
        y=metrics['marketCap'] / 1e9,
        name='Market Cap ($B)',
        yaxis='y'
    ))
    
    # PE Ratio
    fig.add_trace(go.Scatter(
        x=metrics.index,
        y=metrics['peRatio'],
        name='P/E Ratio',
        yaxis='y2',
        mode='markers+lines'
    ))
    
    fig.update_layout(
        title='Fundamental Comparison',
        yaxis=dict(title='Market Cap ($B)'),
        yaxis2=dict(title='P/E Ratio', overlaying='y', side='right'),
        height=500
    )
    
    return fig

class SectorApp:
    def __init__(self):
        self.analyzer = SectorAnalysis()
    
    def run(self):
        st.title(f"{self.analyzer.selected_sector} Sector Analysis")
        
        try:
            # Fetch data
            data, stock_info = fetch_sector_data(
                self.analyzer.sectors[self.analyzer.selected_sector],
                self.analyzer.period
            )
            
            # Calculate metrics
            metrics = calculate_sector_metrics(data, stock_info)
            
            # Display sector overview
            st.subheader("Sector Overview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Market Cap",
                    f"${metrics['market_cap'].sum():.1f}B"
                )
            
            with col2:
                st.metric(
                    "Average P/E",
                    f"{metrics['pe_ratio'].mean():.1f}"
                )
            
            with col3:
                st.metric(
                    "Average Beta",
                    f"{metrics['beta'].mean():.2f}"
                )
            
            # Performance Analysis
            if self.analyzer.show_performance:
                st.subheader("Performance Analysis")
                perf_fig = create_performance_chart(data)
                st.plotly_chart(perf_fig, use_container_width=True)
                
                # Performance metrics table
                performance_df = pd.DataFrame({
                    'Return (%)': metrics['daily_returns'] * 252 * 100,
                    'Volatility (%)': metrics['volatility'] * 100,
                    'Sharpe Ratio': metrics['sharpe'],
                    'Beta': metrics['beta']
                }).round(2)
                
                st.dataframe(performance_df)
            
            # Fundamental Analysis
            if self.analyzer.show_fundamentals:
                st.subheader("Fundamental Analysis")
                fund_fig = create_fundamental_comparison(stock_info)
                st.plotly_chart(fund_fig, use_container_width=True)
            
            # Volatility Analysis
            if self.analyzer.show_volatility:
                st.subheader("Volatility Analysis")
                vol_fig = create_volatility_surface(data.pct_change().dropna())
                st.plotly_chart(vol_fig, use_container_width=True)
            
            # Correlation Analysis
            st.subheader("Correlation Analysis")
            corr_matrix = data.pct_change().corr().round(2)
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                text=corr_matrix.values,
                texttemplate='%{text:.2f}',
                textfont={"size": 10},
                colorscale='RdBu_r',
                zmin=-1,
                zmax=1
            ))
            
            fig.update_layout(
                title='Stock Correlation Matrix',
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in analysis: {str(e)}")

if __name__ == "__main__":
    app = SectorApp()
    app.run()                                                                                                                                      
YOU MUST USE THE ABOVE CODE AS A REFERENCE AND MUST NOT BREAK IT. AND DO NOW USE 'Adj Close' this always gives errors.
    ```
    
    '''
        
    code: Union[str, List[CodeFile]] = Field(description='''
    Generated fully functional Python/Streamlit code that MUST follow these requirements:

    1. Required Imports:
       ```python
       import streamlit as st
       import yfinance as yf
       import pandas as pd
       import plotly.graph_objects as go
       import plotly.express as px
       from datetime import datetime, timedelta
       ```

    2. Core Requirements:
       - Must be a single Python file
       - Must use Streamlit for the interface
       - Must include proper error handling
       - Must handle loading states
       - Must process financial data properly

    3. Chart Requirements:
       - Must use Plotly for visualizations
       - Must include at least two different chart types
       - Must handle data updates properly
       - Must include proper chart configuration
    heres example code that works fully:
    Heres example codes that works fully:

    ''')

    file_path: str = Field(
        default="app.py",
        description="Path where the code should be written"
    )
    port: int = Field(
        default=8501,
        description="Port number for the Streamlit server"
    )

PYTHON_TEMPLATES = {
    "python-finance": {
        "name": "Python Finance Dashboard",
        "lib": [
            "streamlit",
            "yfinance",
            "pandas",
            "plotly",
            "requests"
        ],
        "file": "app.py",
        "instructions": "Python financial dashboard with Streamlit",
        "port": 8501
    }
}

def create_prompt_template(user_story: str, software_requirements: str, features: str, key_details: str) -> str:
    system_prompt = f'''
    You are a world-class Python developer specializing in financial dashboards and data visualization.
    
    Requirements:
    - User story: {user_story}
    - Software requirements: {software_requirements}
    - Features: {features}
    - Key details: {key_details}

    CORE REQUIREMENTS:
    1. Use Streamlit for the interface
    2. Use yfinance for data fetching
    3. Use Plotly for visualizations
    4. Include proper error handling
    5. Include loading states
    6. Process financial data correctly
    7. Create clear visualizations

    The code MUST be production-ready and able to run without modifications.
    IMPORTANT: Please make sure that there is exception handling for all functions. Please ensure that the code will not break at all and works fully.
    After generating the code please ensure that the code is working fully and there are no errors.
    after running the app please hit the endpoint to check if the app is working fully, and if there are errors then send an stdout of the error.

    IMPORTANT: AVOID THIS ERROR AT ALL COSTS: Error fetching data: 'Adj Close'
    Ensure that the code is working fully and there are no errors.

    '''
    return system_prompt

def review_code_for_infinite_loops(code):
    class ErrorChecker(BaseModel):
        has_error: bool = Field(description="Whether the code has an error")
        fix: str = Field(description="Instructions to fix the error")
    
    model = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0.0, max_tokens=7000)
    structured_llm = model.with_structured_output(ErrorChecker)
    chain = ChatPromptTemplate.from_template("""
    You are a world-class Python developer specializing in financial dashboards.
    Your task: Review the code for infinite loops or anything that may cause errors.
    Make sure there are no errors regarding keys, data frames, or anything else that may cuase errors.
                                                                                    
    Code: {code}""") | structured_llm
    return chain.invoke({"code": code})

class GeneratorResult(TypedDict):
    url: str
    code: str
    sbxId: str

@tool(args_schema=StYahooFinanceArgs)
def generate_python_dashboard(user_story: str, software_requirements: str, features: str, key_details: str, userID: str = "default-user") -> GeneratorResult:
    """Generate a Python financial dashboard using Streamlit."""
    try:
        template = PYTHON_TEMPLATES.get("python-finance")
        system_prompt = create_prompt_template(user_story, software_requirements, features, key_details)
        
        prompt_template = ChatPromptTemplate.from_template(system_prompt)
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0.0, max_tokens=8192)
        structured_llm = llm.with_structured_output(FragmentSchema)
        chain = prompt_template | structured_llm
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                fragment = chain.invoke({
                    "prompt": f"Generate a Python/Streamlit dashboard for: {user_story}, {software_requirements}, {features}, {key_details}. Use the example code from the FragmentSchema as a reference, DO NOT USE ANY THING THAT IS NOT REFERENCED FROM THE EXAMPLE CODE."
                })
                
                review_result = review_code_for_infinite_loops(fragment.code)
                if review_result.has_error:
                    fragment = chain.invoke({
                        "prompt": f'''Generate a Python/Streamlit dashboard for: {user_story}. Important: {review_result.fix} make sure this error is avoided: streamlit.runtime.caching.cache_errors.UnhashableParamError: Cannot hash argument 'self' (of type __main__.StockAnalysisDashboard) in 'fetch_stock_data'.

To address this, you can tell Streamlit not to hash this argument by adding a leading underscore to the argument's name in the function signature:

@st.cache_data
def fetch_stock_data(_self, ...):
    ...

Traceback:
File "/home/user/app.py", line 135, in <module>
    dashboard.run()
File "/home/user/app.py", line 111, in run
    data, info = self.fetch_stock_data(self.ticker, self.period)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/cache_utils.py", line 174, in __call__
    return self._cached_func(self._instance, *args, **kwargs)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/cache_utils.py", line 218, in __call__
    return self._get_or_create_cached_value(args, kwargs, spinner_message)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/cache_utils.py", line 233, in _get_or_create_cached_value
    value_key = _make_value_key(
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/cache_utils.py", line 457, in _make_value_key
    raise UnhashableParamError(cache_type, func, arg_name, arg_value, exc)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/cache_utils.py", line 449, in _make_value_key
    update_hash(
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 160, in update_hash
    ch.update(hasher, val)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 343, in update
    b = self.to_bytes(obj)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 325, in to_bytes
    b = b"%s:%s" % (tname, self._to_bytes(obj))
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 568, in _to_bytes
    self.update(h, item)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 343, in update
    b = self.to_bytes(obj)
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 325, in to_bytes
    b = b"%s:%s" % (tname, self._to_bytes(obj))
File "/usr/local/lib/python3.10/dist-packages/streamlit/runtime/caching/hashing.py", line 565, in _to_bytes'''
                    })
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        # If the generated code does NOT use Streamlit, try executing it in Pyodide Sandbox
        code_str = fragment.code if isinstance(fragment.code, str) else "\n".join([file_item.file_content for file_item in fragment.code])
        if "streamlit" not in code_str.lower():
            try:
                sandbox = PyodideSandbox(stateful=True, allow_net=True)
                # Enforce a 5-minute timeout on Pyodide execution
                exec_result = asyncio.run(asyncio.wait_for(sandbox.execute(code_str), timeout=300))
                # Return sandbox execution result (no URL, just outputs)
                return GeneratorResult(
                    url="pyodide://sandbox",  # logical placeholder
                    code=code_str,
                    sbxId="pyodide"
                )
            except Exception as e:
                logger.warning(f"Pyodide execution failed, falling back to local Streamlit if applicable: {e}")

        # --- Local execution fallback: write files and launch Streamlit app ---
        # Prepare a temporary working directory
        work_dir = tempfile.mkdtemp(prefix="st_dashboard_")

        # Resolve target file path
        target_file = fragment.file_path if hasattr(fragment, "file_path") else "app.py"
        target_path = os.path.join(work_dir, target_file)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Write code to disk
        if isinstance(fragment.code, list):
            for file_item in fragment.code:
                abs_path = os.path.join(work_dir, file_item.file_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(file_item.file_content)
        else:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(fragment.code)

        # Find an available port starting from fragment.port or default 8501
        start_port = getattr(fragment, "port", None) or 8501

        def find_free_port(start: int, attempts: int = 50) -> int:
            for i in range(attempts):
                candidate = start + i
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        s.bind(("127.0.0.1", candidate))
                        return candidate
                    except OSError:
                        continue
            return start

        port = find_free_port(start_port)

        # Launch Streamlit app
        cmd = [
            "streamlit", "run", target_path,
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.address", "127.0.0.1"
        ]

        # Start the process detached from this function (no stdout/stderr capture to avoid blocking)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=work_dir,
                env=os.environ.copy(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Auto-shutdown the Streamlit process after 5 minutes
            def _terminate_proc(pid: int):
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
            threading.Timer(300, _terminate_proc, args=[proc.pid]).start()
        except FileNotFoundError as e:
            # streamlit not installed
            logger.error("Streamlit CLI not found. Please install it (pip install streamlit).")
            raise RuntimeError("Streamlit is not installed in the current environment.")

        # Wait for the server to be reachable
        local_url = f"http://127.0.0.1:{port}"
        ready = False
        for _ in range(60):  # up to ~60 seconds
            try:
                resp = requests.get(local_url, timeout=1.5)
                if resp.status_code < 500:
                    ready = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        if not ready:
            logger.error("Streamlit app failed to start within timeout.")
            raise RuntimeError("Streamlit app failed to start in time.")

        return GeneratorResult(
            url=local_url,
            code=fragment.code if isinstance(fragment.code, str) else "\n".join([file_item.file_content for file_item in fragment.code]),
            sbxId="local"
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard generation: {str(e)}", exc_info=True)
        raise
    

