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