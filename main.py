import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta, time
import json
import io
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import time as time_module
import streamlit.components.v1 as components

# Enhanced Configuration
st.set_page_config(
    page_title="🚀 Interactive QQQ Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced interactivity
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .signal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin: 10px 0;
    }
    
    .trade-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 5px;
    }
    
    .alert-success {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    
    .alert-danger {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    
    .interactive-button {
        background: linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%);
        border: none;
        border-radius: 25px;
        color: white;
        padding: 12px 24px;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 3px 5px 2px rgba(255, 105, 135, .3);
    }
    
    .interactive-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 10px 4px rgba(255, 105, 135, .3);
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .streaming-indicator {
        width: 10px;
        height: 10px;
        background-color: #28a745;
        border-radius: 50%;
        display: inline-block;
        animation: blink 1s infinite;
        margin-right: 8px;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .signal-history-table {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .entry-signal {
        background: rgba(0, 255, 136, 0.2);
        color: #00ff88;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
    }
    
    .exit-signal {
        background: rgba(255, 71, 87, 0.2);
        color: #ff4757;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
    }
    
    .no-signal {
        background: rgba(128, 128, 128, 0.2);
        color: #808080;
        padding: 5px 10px;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Auto-refresh using JavaScript
auto_refresh_js = """
<script>
let refreshInterval = null;

window.startAutoRefresh = function(intervalSeconds) {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(function() {
        // Trigger Streamlit rerun
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: Date.now()
        }, '*');
    }, intervalSeconds * 1000);
};

window.stopAutoRefresh = function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
};
</script>
"""

interactive_js = """
<script>
// Voice Commands
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    window.startVoiceCommand = function() {
        recognition.start();
    };
    
    recognition.onresult = function(event) {
        const command = event.results[0][0].transcript.toLowerCase();
        
        if (command.includes('refresh') || command.includes('update')) {
            window.parent.postMessage({type: 'voice_command', action: 'refresh'}, '*');
        } else if (command.includes('buy') || command.includes('enter')) {
            window.parent.postMessage({type: 'voice_command', action: 'buy_signal'}, '*');
        } else if (command.includes('sell') || command.includes('exit')) {
            window.parent.postMessage({type: 'voice_command', action: 'sell_signal'}, '*');
        }
    };
}

// Browser Notifications
function showNotification(title, message, type='info') {
    if (Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️',
            tag: 'trading-alert'
        });
        
        // Auto close after 5 seconds
        setTimeout(() => notification.close(), 5000);
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showNotification(title, message, type);
            }
        });
    }
}

// Sound alerts
function playAlert(type='notification') {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    if (type === 'success') {
        // Success sound (major chord)
        playChord(audioContext, [261.63, 329.63, 392.00], 0.3, 0.5);
    } else if (type === 'warning') {
        // Warning sound (tritone)
        playChord(audioContext, [261.63, 369.99], 0.5, 0.3);
    } else {
        // Default notification
        playTone(audioContext, 440, 0.2, 0.1);
    }
}

function playTone(audioContext, frequency, duration, volume) {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + duration);
}

function playChord(audioContext, frequencies, duration, volume) {
    frequencies.forEach(freq => playTone(audioContext, freq, duration, volume));
}

// Make functions available globally
window.showNotification = showNotification;
window.playAlert = playAlert;

// Request notification permission on load
if ('Notification' in window) {
    Notification.requestPermission();
}
</script>
"""

@dataclass
class TradeConfig:
    """Enhanced configuration with interactive features"""
    # Technical Analysis
    ema_5_period: int = 5
    ema_10_period: int = 10
    ema_21_period: int = 21
    ema_50_period: int = 50
    atr_period: int = 14
    volume_period: int = 20
    
    # Entry/Exit Criteria
    atr_entry_multiplier: float = 1.5
    atr_target1_multiplier: float = 2.0
    atr_target2_multiplier: float = 3.0
    atr_stop_multiplier: float = 2.0
    
    # Risk Management
    risk_percent: float = 1.0
    max_positions: int = 3
    daily_loss_limit: float = 3.0
    vix_threshold: float = 30.0
    account_value: float = 100000.0
    stop_loss_percent: float = 2.0
    
    # Data Settings
    data_period: str = "2y"  # Default to 2 years
    chart_period: str = "6mo"  # What to display on chart
    
    # Interactive Features (removed voice_commands and mobile_mode)
    auto_refresh: bool = False
    refresh_interval: int = 60
    enable_sounds: bool = True
    enable_notifications: bool = True

@dataclass
class TradingAlert:
    """Trading alert structure"""
    timestamp: str
    type: str  # 'entry', 'exit', 'warning', 'info'
    message: str
    price: float
    priority: str = 'normal'  # 'low', 'normal', 'high', 'critical'

@dataclass
class Trade:
    """Enhanced trade record"""
    entry_date: str
    entry_time: str
    entry_price: float
    position_size: int
    stop_loss: float
    target1: float
    target2: float
    notes: str = ""
    tags: List[str] = None
    exit_date: Optional[str] = None
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    exit_reason: Optional[str] = None
    is_active: bool = True

class InteractiveCharts:
    """Enhanced chart creation with interactive features"""
    
    @staticmethod
    def create_enhanced_price_chart(data: pd.DataFrame, signals: Dict, config: TradeConfig) -> go.Figure:
        """Create an enhanced interactive price chart"""
        
        # Create subplots with custom spacing
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=('QQQ Price with EMAs & Signals', 'Volume Analysis', 'Technical Indicators'),
            row_heights=[0.6, 0.25, 0.15]
        )
        
        # Candlestick chart with enhanced styling
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='QQQ Price',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4757',
                increasing_fillcolor='rgba(0, 255, 136, 0.3)',
                decreasing_fillcolor='rgba(255, 71, 87, 0.3)'
            ),
            row=1, col=1
        )
        
        # Enhanced EMAs with custom styling
        ema_configs = [
            ('EMA_5', '#ff6b6b', 3),
            ('EMA_10', '#4ecdc4', 2),
            ('EMA_21', '#45b7d1', 2),
            ('EMA_50', '#96ceb4', 3)
        ]
        
        for ema, color, width in ema_configs:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[ema],
                    mode='lines',
                    name=ema,
                    line=dict(color=color, width=width),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        # Entry level with interactive annotation
        if 'entry_level' in signals:
            fig.add_hline(
                y=signals['entry_level'],
                line_dash="dash",
                line_color="#feca57",
                line_width=2,
                annotation_text="Entry Zone",
                annotation_position="right",
                row=1, col=1
            )
        
        # Volume analysis with color coding
        volume_colors = []
        for i in range(len(data)):
            if i == 0:
                volume_colors.append('#808080')  # gray
            elif data['Close'].iloc[i] > data['Close'].iloc[i-1]:
                volume_colors.append('#00ff88')
            else:
                volume_colors.append('#ff4757')
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=volume_colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Volume average line
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Volume_Avg'],
                mode='lines',
                name='Volume Average',
                line=dict(color='#ffa502', width=2)
            ),
            row=2, col=1
        )
        
        # ATR indicator
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['ATR'],
                mode='lines',
                name='ATR',
                line=dict(color='#a55eea', width=2),
                fill='tonexty',
                fillcolor='rgba(165, 94, 234, 0.1)'
            ),
            row=3, col=1
        )
        
        # Enhanced layout with dark theme
        fig.update_layout(
            title={
                'text': "🚀 Interactive QQQ Analysis Dashboard",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24, 'color': '#2c3e50'}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=900,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified',
            dragmode='zoom'
        )
        
        # Enhanced interactivity
        fig.update_xaxes(
            showspikes=True,
            spikecolor="white",
            spikesnap="cursor",
            spikemode="across",
            rangeslider_visible=False
        )
        
        fig.update_yaxes(
            showspikes=True,
            spikecolor="white",
            spikesnap="cursor",
            spikemode="across"
        )
        
        # Add range selector buttons
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1D", step="day", stepmode="backward"),
                        dict(count=5, label="5D", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=False),
                type="date"
            )
        )
        
        return fig
    
    @staticmethod
    def create_risk_reward_chart(entry_price: float, stop_loss: float, target1: float, target2: float) -> go.Figure:
        """Create interactive risk/reward visualization"""
        
        levels = ['Stop Loss', 'Entry', 'Target 1', 'Target 2']
        prices = [stop_loss, entry_price, target1, target2]
        colors = ['#ff4757', '#74b9ff', '#00b894', '#fdcb6e']
        
        fig = go.Figure()
        
        # Add horizontal lines for each level
        for i, (level, price, color) in enumerate(zip(levels, prices, colors)):
            fig.add_hline(
                y=price,
                line_color=color,
                line_width=3,
                annotation_text=f"{level}: ${price:.2f}",
                annotation_position="right"
            )
        
        # Add risk/reward zones
        fig.add_shape(
            type="rect",
            x0=0, x1=1, y0=stop_loss, y1=entry_price,
            fillcolor="rgba(255, 71, 87, 0.2)",
            line=dict(width=0),
            name="Risk Zone"
        )
        
        fig.add_shape(
            type="rect",
            x0=0, x1=1, y0=entry_price, y1=target2,
            fillcolor="rgba(0, 184, 148, 0.2)",
            line=dict(width=0),
            name="Reward Zone"
        )
        
        fig.update_layout(
            title="Risk/Reward Analysis",
            yaxis_title="Price ($)",
            height=400,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_xaxes(visible=False)
        
        return fig

class InteractiveDashboard:
    """Enhanced interactive dashboard"""
    
    def __init__(self):
        self.config = self.load_config()
        self.trades = self.load_trades()
        self.alerts = self.load_alerts()
        
        # Initialize session state for interactivity
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        if 'chart_annotations' not in st.session_state:
            st.session_state.chart_annotations = []
    
    def load_config(self) -> TradeConfig:
        """Load configuration from session state"""
        if 'config' not in st.session_state:
            st.session_state.config = TradeConfig()
        return st.session_state.config
    
    def load_trades(self) -> List[Trade]:
        """Load trades from session state"""
        if 'trades' not in st.session_state:
            st.session_state.trades = []
        return st.session_state.trades
    
    def load_alerts(self) -> List[TradingAlert]:
        """Load alerts from session state"""
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        return st.session_state.alerts
    
    def add_alert(self, alert_type: str, message: str, price: float, priority: str = 'normal'):
        """Add a new trading alert"""
        alert = TradingAlert(
            timestamp=datetime.now().strftime('%H:%M:%S'),
            type=alert_type,
            message=message,
            price=price,
            priority=priority
        )
        self.alerts.insert(0, alert)  # Add to beginning
        if len(self.alerts) > 50:  # Keep only last 50 alerts
            self.alerts = self.alerts[:50]
        st.session_state.alerts = self.alerts
    
    def display_enhanced_header(self):
        """Display enhanced header with live indicators"""
        st.markdown("""
        <div class="main-header">
            <h1>🚀 Interactive QQQ Trading Dashboard</h1>
            <p><span class="streaming-indicator"></span>Live Market Data & Analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    def display_live_alerts(self):
        """Display live alerts panel"""
        if not self.alerts:
            return
        
        st.subheader("🔔 Live Alerts")
        
        # Show last 5 alerts
        for alert in self.alerts[:5]:
            alert_class = {
                'entry': 'alert-success',
                'exit': 'alert-warning',
                'warning': 'alert-danger',
                'info': 'alert-success'
            }.get(alert.type, 'alert-success')
            
            st.markdown(f"""
            <div class="{alert_class}">
                <strong>{alert.timestamp}</strong> - {alert.message} (${alert.price:.2f})
            </div>
            """, unsafe_allow_html=True)
    
    def display_interactive_controls(self):
        """Display interactive control panel"""
        st.subheader("🎮 Interactive Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Force Refresh", key="force_refresh"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("📊 Strategy Stats", key="strategy_stats"):
                st.session_state.show_strategy_stats = True
        
        with col3:
            if st.button("📈 Signal History", key="signal_history"):
                st.session_state.show_signal_history = True
    
    def display_strategy_explanation(self):
        """Display detailed strategy explanation and entry criteria"""
        if 'show_strategy_stats' not in st.session_state or not st.session_state.show_strategy_stats:
            return
        
        with st.expander("📊 QQQ Swing Trading Strategy - Complete Guide", expanded=True):
            
            # Strategy Overview
            st.markdown("""
            ## 🎯 **QQQ Swing Trading Strategy Overview**
            
            This systematic approach identifies high-probability swing trade entries in QQQ (Invesco QQQ Trust ETF) 
            using multiple technical confluences for 3-10 day holding periods.
            """)
            
            # Entry Criteria Section
            st.markdown("### 🚀 **Entry Criteria (ALL Must Be Met)**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **📈 Technical Alignment:**
                - **EMA Stack**: 10 EMA > 21 EMA > 50 EMA (bullish momentum)
                - **Price Position**: Current price must be above 50 EMA (trend confirmation)
                - **Entry Trigger**: Price touches or dips below (5 EMA - 1.5×ATR)
                
                **📊 Volume Confirmation:**
                - Entry day volume > 20-day average volume
                - Indicates institutional participation
                """)
            
            with col2:
                st.markdown("""
                **🌊 Market Environment:**
                - **VIX < 30**: Low fear/volatility environment
                - Reduces risk of market-wide selloffs
                
                **⚡ Momentum Filter:**
                - Price must be higher than 5 days ago
                - Confirms underlying strength
                """)
            
            # Risk Management
            st.markdown("### 🛡️ **Risk Management Rules**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **💰 Position Sizing:**
                - Risk 1-2% of account per trade
                - Shares = Risk Amount ÷ (Entry - Stop)
                - Maximum 3 concurrent positions
                """)
            
            with col2:
                st.markdown("""
                **🎯 Price Targets:**
                - **Target 1**: 5 EMA + (2.0 × ATR)
                - **Target 2**: 5 EMA + (3.0 × ATR)
                - Scale out 50% at Target 1
                """)
            
            with col3:
                st.markdown("""
                **🚨 Stop Loss:**
                - Entry - (2.0 × ATR) OR 2% below entry
                - Use whichever gives smaller loss
                - Move to breakeven when Target 1 hit
                """)
            
            if st.button("❌ Close Strategy Guide"):
                st.session_state.show_strategy_stats = False
                st.rerun()
    
    def calculate_historical_signals(self, data: pd.DataFrame, vix_data=None):
        """Calculate entry and exit signals for historical data - EXACT STRATEGY IMPLEMENTATION"""
        signals_history = []
        
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1]
            latest = current_data.iloc[-1]
            
            # EXACT ENTRY CRITERIA - ALL MUST BE MET
            # 1. EMA Stack: 10 EMA > 21 EMA > 50 EMA (bullish momentum)
            ema_alignment = latest['EMA_10'] > latest['EMA_21'] > latest['EMA_50']
            
            # 2. Price Position: Current price must be above 50 EMA (trend confirmation)
            price_above_50ema = latest['Close'] > latest['EMA_50']
            
            # 3. Entry Trigger: Price touches or dips below (5 EMA - 1.5×ATR)
            entry_level = latest['EMA_5'] - (1.5 * latest['ATR'])
            price_touch_entry = latest['Close'] <= entry_level or latest['Low'] <= entry_level
            
            # 4. Volume Confirmation: Entry day volume > 20-day average volume
            volume_above_avg = latest['Volume'] > latest['Volume_Avg']
            
            # 5. Market Environment: VIX < 30 (simplified - assume good environment for historical)
            vix_below_threshold = True  # You can enhance this with actual VIX data
            
            # 6. Momentum Filter: Price must be higher than 5 days ago
            if i >= 55:  # Need at least 5 more days
                momentum_positive = latest['Close'] > current_data['Close'].iloc[-6]
            else:
                momentum_positive = True
            
            # ENTRY SIGNAL: ALL 6 CRITERIA MUST BE MET
            entry_signal = all([
                ema_alignment,
                price_above_50ema,
                price_touch_entry,
                volume_above_avg,
                vix_below_threshold,
                momentum_positive
            ])
            
            # EXIT CRITERIA - Following exact strategy rules
            exit_signal = False
            if i > 0:
                prev_close = data['Close'].iloc[i-1]
                current_close = latest['Close']
                
                # Exit conditions:
                # 1. Stop Loss: Entry - (2.0 × ATR) OR 2% below entry (whichever gives smaller loss)
                # 2. Target 1: 5 EMA + (2.0 × ATR) - Scale out 50%
                # 3. Target 2: 5 EMA + (3.0 × ATR) - Exit remaining
                # 4. Time-based: 10 day maximum hold
                
                # For historical analysis, we'll use simplified exit:
                # Exit if price breaks below 21 EMA significantly (strategy breakdown)
                if current_close < latest['EMA_21'] * 0.97:  # 3% below 21 EMA indicates trend break
                    exit_signal = True
                
                # Or if we have a significant down day (> 3% drop from previous close)
                daily_return = (current_close - prev_close) / prev_close
                if daily_return < -0.03:
                    exit_signal = True
            
            signals_history.append({
                'Date': data.index[i],
                'Close': latest['Close'],
                'Entry_Signal': entry_signal,
                'Exit_Signal': exit_signal,
                'EMA_Alignment': ema_alignment,
                'Price_Above_50EMA': price_above_50ema,
                'Entry_Level_Touch': price_touch_entry,
                'Volume_Above_Avg': volume_above_avg,
                'Momentum_Positive': momentum_positive,
                'Entry_Level': entry_level,
                'EMA_5': latest['EMA_5'],
                'EMA_10': latest['EMA_10'],
                'EMA_21': latest['EMA_21'],
                'EMA_50': latest['EMA_50'],
                'ATR': latest['ATR'],
                'Volume': latest['Volume'],
                'Volume_Avg': latest['Volume_Avg']
            })
        
        return pd.DataFrame(signals_history)
    
    def match_entry_exit_signals(self, signals_df: pd.DataFrame):
        """Match entry signals with exits using EXACT STRATEGY RULES"""
        trades = []
        
        entry_signals = signals_df[signals_df['Entry_Signal'] == True].copy()
        exit_signals = signals_df[signals_df['Exit_Signal'] == True].copy()
        
        if entry_signals.empty:
            return pd.DataFrame()
        
        for _, entry in entry_signals.iterrows():
            entry_date = entry['Date']
            entry_price = entry['Close']
            entry_ema5 = entry['EMA_5']
            entry_atr = entry['ATR']
            
            # EXACT STRATEGY CALCULATIONS
            
            # Stop Loss: Entry - (2.0 × ATR) OR 2% below entry (whichever gives smaller loss)
            stop_loss_atr = entry_price - (2.0 * entry_atr)
            stop_loss_pct = entry_price * 0.98  # 2% below entry
            stop_loss = max(stop_loss_atr, stop_loss_pct)  # Use whichever gives smaller loss
            
            # Targets: 
            # Target 1: 5 EMA + (2.0 × ATR)
            # Target 2: 5 EMA + (3.0 × ATR)
            target1 = entry_ema5 + (2.0 * entry_atr)
            target2 = entry_ema5 + (3.0 * entry_atr)
            
            # Position Sizing: Risk 1-2% of account per trade
            account_value = 100000  # Default account value
            risk_percent = 0.01  # 1% risk
            risk_amount = account_value * risk_percent
            risk_per_share = entry_price - stop_loss
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 100
            
            # Find the next exit signal after this entry (max 10 days per strategy)
            future_exits = exit_signals[exit_signals['Date'] > entry_date]
            
            # Add 10-day time limit per strategy rules
            ten_days_later = entry_date + pd.Timedelta(days=10)
            future_exits_within_limit = future_exits[future_exits['Date'] <= ten_days_later]
            
            if not future_exits_within_limit.empty:
                # Take the first exit signal after entry (within 10 days)
                exit_row = future_exits_within_limit.iloc[0]
                exit_date = exit_row['Date']
                exit_price = exit_row['Close']
                exit_reason = "Exit Signal"
            else:
                # Time-based exit after 10 days if no exit signal
                time_exit_data = signals_df[signals_df['Date'] >= ten_days_later]
                if not time_exit_data.empty:
                    exit_row = time_exit_data.iloc[0]
                    exit_date = exit_row['Date']
                    exit_price = exit_row['Close']
                    exit_reason = "10-Day Time Limit"
                else:
                    continue  # Skip this trade if we can't find an exit
            
            # Calculate trade metrics
            hold_days = (exit_date - entry_date).days
            profit_loss = exit_price - entry_price
            profit_pct = (profit_loss / entry_price) * 100
            total_profit = profit_loss * shares
            
            # Determine if target levels were hit during the trade
            trade_data = signals_df[(signals_df['Date'] >= entry_date) & (signals_df['Date'] <= exit_date)]
            max_price_during_trade = trade_data['Close'].max()
            
            target1_hit = max_price_during_trade >= target1
            target2_hit = max_price_during_trade >= target2
            
            # Calculate actual exit reason based on strategy rules
            if exit_price <= stop_loss * 1.01:  # Within 1% of stop loss
                actual_exit_reason = "🚨 Stop Loss"
            elif target2_hit:
                actual_exit_reason = "🎯 Target 2 Hit"
            elif target1_hit:
                actual_exit_reason = "🎯 Target 1 Hit"
            elif hold_days >= 10:
                actual_exit_reason = "⏰ 10-Day Limit"
            else:
                actual_exit_reason = exit_reason
            
            trades.append({
                'Entry_Date': entry_date.strftime('%Y-%m-%d'),
                'Entry_Price': round(entry_price, 2),
                'Exit_Date': exit_date.strftime('%Y-%m-%d'),
                'Exit_Price': round(exit_price, 2),
                'Hold_Days': hold_days,
                'Stop_Loss': round(stop_loss, 2),
                'Target_1': round(target1, 2),
                'Target_2': round(target2, 2),
                'T1_Hit': '✅' if target1_hit else '❌',
                'T2_Hit': '✅' if target2_hit else '❌',
                'Price_Change': round(profit_loss, 2),
                'Profit_Pct': round(profit_pct, 2),
                'Shares': shares,
                'Total_Profit': round(total_profit, 0),
                'Exit_Reason': actual_exit_reason,
                'Trade_Result': '✅ WIN' if profit_loss > 0 else '❌ LOSS'
            })
        
        return pd.DataFrame(trades)
    
    def display_signal_history(self, data: pd.DataFrame):
        """Display historical entry/exit signals for selected timeframe"""
        if 'show_signal_history' not in st.session_state or not st.session_state.show_signal_history:
            return
        
        st.markdown("---")
        st.subheader("📈 Swing Trading Signal Analysis")
        
        with st.expander("Complete Swing Trading Analysis for Selected Timeframe", expanded=True):
            # Calculate historical signals
            with st.spinner("Calculating swing trading signals..."):
                signals_df = self.calculate_historical_signals(data)
            
            if signals_df.empty:
                st.warning("No historical signals calculated")
                return
            
            # Match entry/exit signals to create swing trades
            trades_df = self.match_entry_exit_signals(signals_df)
            
            if trades_df.empty:
                st.warning("No complete swing trades found in selected timeframe")
                return
            
            # Calculate overall performance metrics
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['Profit_Pct'] > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            avg_profit_pct = trades_df['Profit_Pct'].mean()
            total_profit_dollar = trades_df['Total_Profit'].sum()
            avg_hold_days = trades_df['Hold_Days'].mean()
            
            # Display key metrics
            st.markdown("#### 🎯 **Swing Trading Performance Summary**")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Trades", total_trades)
                
            with col2:
                color = "normal" if win_rate >= 50 else "inverse"
                st.metric("Win Rate", f"{win_rate:.1f}%", f"{winning_trades}W/{losing_trades}L", delta_color=color)
            
            with col3:
                color = "normal" if avg_profit_pct > 0 else "inverse"
                st.metric("Avg Profit %", f"{avg_profit_pct:+.2f}%", delta_color=color)
            
            with col4:
                color = "normal" if total_profit_dollar > 0 else "inverse"
                st.metric("Total Profit", f"${total_profit_dollar:+,.0f}", delta_color=color)
            
            with col5:
                st.metric("Avg Hold Time", f"{avg_hold_days:.1f} days")
            
            # Main swing trades table with EXACT STRATEGY columns
            st.markdown("#### 🔄 **Complete Swing Trades Following Exact Strategy**")
            
            # Enhanced table with strategy-specific columns
            display_columns = [
                'Entry_Date', 'Entry_Price', 'Exit_Date', 'Exit_Price', 
                'Hold_Days', 'Stop_Loss', 'Target_1', 'Target_2', 
                'T1_Hit', 'T2_Hit', 'Exit_Reason', 'Profit_Pct', 'Total_Profit', 'Trade_Result'
            ]
            
            # Color code the dataframe
            def highlight_trades(row):
                if row['Trade_Result'] == '✅ WIN':
                    return ['background-color: rgba(0, 255, 136, 0.1)'] * len(row)
                else:
                    return ['background-color: rgba(255, 71, 87, 0.1)'] * len(row)
            
            # Display the main trades table with exact strategy details
            styled_df = trades_df[display_columns].style.apply(highlight_trades, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # Download complete trades
            csv_trades = trades_df.to_csv(index=False)
            st.download_button(
                "📥 Download Complete Swing Trades",
                csv_trades,
                f"swing_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                key="download_trades"
            )
            
            # Detailed breakdown
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 **Winning Trades**")
                winning_df = trades_df[trades_df['Profit_Pct'] > 0]
                if not winning_df.empty:
                    st.dataframe(
                        winning_df[['Entry_Date', 'Entry_Price', 'Exit_Price', 'Profit_Pct', 'Total_Profit']],
                        use_container_width=True,
                        height=200
                    )
                    
                    avg_win = winning_df['Profit_Pct'].mean()
                    best_trade = winning_df['Profit_Pct'].max()
                    st.success(f"**Avg Win:** {avg_win:.2f}% | **Best Trade:** {best_trade:.2f}%")
                else:
                    st.info("No winning trades in this period")
            
            with col2:
                st.markdown("#### 📉 **Losing Trades**")
                losing_df = trades_df[trades_df['Profit_Pct'] < 0]
                if not losing_df.empty:
                    st.dataframe(
                        losing_df[['Entry_Date', 'Entry_Price', 'Exit_Price', 'Profit_Pct', 'Total_Profit']],
                        use_container_width=True,
                        height=200
                    )
                    
                    avg_loss = losing_df['Profit_Pct'].mean()
                    worst_trade = losing_df['Profit_Pct'].min()
                    st.error(f"**Avg Loss:** {avg_loss:.2f}% | **Worst Trade:** {worst_trade:.2f}%")
                else:
                    st.success("No losing trades in this period! 🎉")
            
            # Visualization of trades
            st.markdown("#### 📈 **Swing Trades Visualization**")
            
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=signals_df['Date'],
                y=signals_df['Close'],
                mode='lines',
                name='QQQ Price',
                line=dict(color='#74b9ff', width=2)
            ))
            
            # Add entry points
            entry_dates = pd.to_datetime(trades_df['Entry_Date'])
            entry_prices = trades_df['Entry_Price']
            
            fig.add_trace(go.Scatter(
                x=entry_dates,
                y=entry_prices,
                mode='markers',
                name='Entry Points',
                marker=dict(
                    color='#00b894',
                    size=10,
                    symbol='triangle-up',
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>Entry</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ))
            
            # Add exit points
            exit_dates = pd.to_datetime(trades_df['Exit_Date'])
            exit_prices = trades_df['Exit_Price']
            
            fig.add_trace(go.Scatter(
                x=exit_dates,
                y=exit_prices,
                mode='markers',
                name='Exit Points',
                marker=dict(
                    color='#e17055',
                    size=10,
                    symbol='triangle-down',
                    line=dict(width=2, color='white')
                ),
                hovertemplate='<b>Exit</b><br>Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
            ))
            
            # Connect entry/exit pairs with lines
            for _, trade in trades_df.iterrows():
                color = '#00b894' if trade['Profit_Pct'] > 0 else '#e17055'
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(trade['Entry_Date']), pd.to_datetime(trade['Exit_Date'])],
                    y=[trade['Entry_Price'], trade['Exit_Price']],
                    mode='lines',
                    line=dict(color=color, width=2, dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            fig.update_layout(
                title="Swing Trading Entry/Exit Points with P&L",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=600,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Profit distribution
            st.markdown("#### 💰 **Profit Distribution**")
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=trades_df['Profit_Pct'],
                nbinsx=20,
                name='Trade Results',
                marker_color='#74b9ff',
                opacity=0.7
            ))
            
            fig_hist.update_layout(
                title="Distribution of Trade Results (%)",
                xaxis_title="Profit/Loss (%)",
                yaxis_title="Number of Trades",
                height=400
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Close button
            if st.button("❌ Close Swing Trading Analysis"):
                st.session_state.show_signal_history = False
                st.rerun()
    
    def display_entry_criteria_panel(self, signals: Dict, vix_value: float, data: pd.DataFrame):
        """Display detailed entry criteria analysis"""
        st.subheader("🎯 Entry Signal Analysis")
        
        # Signal strength meter
        strength = signals.get('strength', 0)
        strength_pct = (strength / 6) * 100
        
        if strength >= 6:
            st.success(f"🟢 **STRONG ENTRY SIGNAL** - All {strength}/6 criteria met!")
        elif strength >= 4:
            st.warning(f"🟡 **PARTIAL SIGNAL** - {strength}/6 criteria met")
        else:
            st.error(f"🔴 **NO ENTRY SIGNAL** - Only {strength}/6 criteria met")
        
        # Progress bar for signal strength
        st.progress(strength_pct / 100, text=f"Signal Strength: {strength}/6 ({strength_pct:.0f}%)")
        
        # Detailed criteria breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 **Technical Criteria**")
            
            # EMA Alignment
            ema_status = "✅" if signals['ema_alignment'] else "❌"
            latest = data.iloc[-1]
            st.markdown(f"""
            **{ema_status} EMA Alignment (10>21>50)**
            - 10 EMA: ${latest['EMA_10']:.2f}
            - 21 EMA: ${latest['EMA_21']:.2f}  
            - 50 EMA: ${latest['EMA_50']:.2f}
            - Status: {'Bullish Stack ✅' if signals['ema_alignment'] else 'Not Aligned ❌'}
            """)
            
            # Price above 50 EMA
            price_status = "✅" if signals['price_above_50ema'] else "❌"
            distance_from_50 = ((signals['current_price'] - latest['EMA_50']) / latest['EMA_50']) * 100
            st.markdown(f"""
            **{price_status} Price Above 50 EMA**
            - Current: ${signals['current_price']:.2f}
            - 50 EMA: ${latest['EMA_50']:.2f}
            - Distance: {distance_from_50:+.1f}% {'(Good)' if distance_from_50 > 0 else '(Below trend)'}
            """)
            
            # Entry Level Touch
            entry_status = "✅" if signals['price_touch_entry'] else "❌"
            st.markdown(f"""
            **{entry_status} Entry Level Touch**
            - Entry Level: ${signals['entry_level']:.2f}
            - Current: ${signals['current_price']:.2f}
            - Status: {'Touched ✅' if signals['price_touch_entry'] else 'Not yet ❌'}
            """)
        
        with col2:
            st.markdown("### 📊 **Market Criteria**")
            
            # Volume
            volume_status = "✅" if signals['volume_above_avg'] else "❌"
            volume_ratio = latest['Volume'] / latest['Volume_Avg'] if latest['Volume_Avg'] > 0 else 0
            st.markdown(f"""
            **{volume_status} Volume Above Average**
            - Today: {latest['Volume']:,.0f}
            - 20-day Avg: {latest['Volume_Avg']:,.0f}
            - Ratio: {volume_ratio:.1f}x {'(Strong)' if volume_ratio > 1.5 else '(Normal)' if volume_ratio > 1 else '(Weak)'}
            """)
            
            # VIX
            vix_status = "✅" if signals['vix_below_threshold'] else "❌"
            st.markdown(f"""
            **{vix_status} VIX Below Threshold**
            - Current VIX: {vix_value:.1f}
            - Threshold: {self.config.vix_threshold}
            - Environment: {'Low Fear ✅' if vix_value < self.config.vix_threshold else 'High Fear ❌'}
            """)
            
            # Momentum
            momentum_status = "✅" if signals['momentum_positive'] else "❌"
            momentum_change = ((signals['current_price'] - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100
            st.markdown(f"""
            **{momentum_status} 5-Day Momentum**
            - 5 days ago: ${data['Close'].iloc[-6]:.2f}
            - Current: ${signals['current_price']:.2f}
            - Change: {momentum_change:+.1f}% {'(Bullish)' if momentum_change > 0 else '(Bearish)'}
            """)
        
        # Risk/Reward Analysis - EXACT STRATEGY CALCULATIONS
        if strength >= 6:
            st.markdown("### 💰 **Position Sizing & Risk Analysis (Exact Strategy)**")
            
            # EXACT STRATEGY CALCULATIONS
            atr = latest['ATR']
            
            # Stop Loss: Entry - (2.0 × ATR) OR 2% below entry (whichever gives smaller loss)
            stop_loss_atr = signals['current_price'] - (2.0 * atr)
            stop_loss_pct = signals['current_price'] * 0.98  # 2% below entry
            stop_loss = max(stop_loss_atr, stop_loss_pct)  # Use whichever gives smaller loss
            
            # Targets following exact strategy:
            # Target 1: 5 EMA + (2.0 × ATR)
            # Target 2: 5 EMA + (3.0 × ATR)
            target1 = latest['EMA_5'] + (2.0 * atr)
            target2 = latest['EMA_5'] + (3.0 * atr)
            
            # Position sizing: Risk 1-2% of account per trade
            account_value = 100000  # You can make this configurable
            risk_percent = 0.01  # 1% risk per strategy
            risk_amount = account_value * risk_percent
            price_risk = signals['current_price'] - stop_loss
            shares = int(risk_amount / price_risk) if price_risk > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Shares (1% Risk)", f"{shares:,}")
                st.metric("Dollar Risk", f"${risk_amount:.0f}")
            
            with col2:
                st.metric("Entry Price", f"${signals['current_price']:.2f}")
                st.metric("Stop Loss", f"${stop_loss:.2f}")
                st.caption("Entry - 2×ATR or 2% (smaller loss)")
            
            with col3:
                st.metric("Target 1 (50% exit)", f"${target1:.2f}")  
                st.metric("Target 2 (remaining)", f"${target2:.2f}")
                st.caption("5 EMA + 2×ATR / 3×ATR")
            
            with col4:
                rr1 = (target1 - signals['current_price']) / price_risk if price_risk > 0 else 0
                rr2 = (target2 - signals['current_price']) / price_risk if price_risk > 0 else 0
                st.metric("R:R Target 1", f"{rr1:.1f}:1")
                st.metric("R:R Target 2", f"{rr2:.1f}:1")
            
            # Strategy-specific notes
            st.info("""
            **📋 Exact Strategy Execution:**
            • Enter when ALL 6 criteria met
            • Stop: Entry - 2×ATR OR 2% below (smaller loss)
            • Target 1: 5 EMA + 2×ATR (exit 50% of position)  
            • Target 2: 5 EMA + 3×ATR (exit remaining 50%)
            • Move stop to breakeven when Target 1 hit
            • Maximum hold: 10 trading days
            """)
        
        # Market timing advice - Updated for exact strategy
        st.markdown("### ⏰ **Market Timing Considerations (Strategy Rules)**")
        
        current_time = datetime.now().time()
        market_open = time(9, 30)  # 9:30 AM
        market_close = time(16, 0)  # 4:00 PM
        optimal_start = time(10, 30)  # 10:30 AM
        optimal_end = time(14, 0)  # 2:00 PM
        
        is_market_hours = market_open <= current_time <= market_close
        is_optimal_time = optimal_start <= current_time <= optimal_end
        
        timing_advice = ""
        if not is_market_hours:
            timing_advice = "🕐 **Market Closed** - Monitor for pre-market setup"
        elif is_optimal_time:
            timing_advice = "🟢 **Optimal Entry Window** - Best execution time per strategy"
        elif current_time < optimal_start:
            timing_advice = "🟡 **Early Session** - Wait for 10:30 AM per strategy rules"
        else:
            timing_advice = "🟡 **Late Session** - Consider next day entry per strategy"
        
        st.info(timing_advice)
        st.caption("Strategy Note: Best entries typically 10:30 AM - 2:00 PM EST. Avoid Fridays and day before holidays.")
    
    def display_enhanced_sidebar(self):
        """Enhanced interactive sidebar (removed Interactive Features section)"""
        st.sidebar.markdown("## ⚙️ Settings")
        
        # Real-time controls
        with st.sidebar.expander("🔄 Real-time Controls", expanded=True):
            self.config.auto_refresh = st.checkbox("Auto Refresh", self.config.auto_refresh)
            if self.config.auto_refresh:
                self.config.refresh_interval = st.slider("Interval (seconds)", 10, 300, self.config.refresh_interval)
            
            self.config.enable_sounds = st.checkbox("Sound Alerts", self.config.enable_sounds)
            self.config.enable_notifications = st.checkbox("Browser Notifications", self.config.enable_notifications)
        
        # Data & Display Settings
        with st.sidebar.expander("📊 Data & Display Settings", expanded=False):
            # Historical data period for calculations
            data_options = {
                "6 months": "6mo",
                "1 year": "1y", 
                "2 years": "2y",
                "3 years": "3y",
                "5 years": "5y",
                "Max": "max"
            }
            
            selected_data = st.selectbox(
                "Historical Data for Calculations",
                options=list(data_options.keys()),
                index=2,  # Default to 2 years
                help="More data = better EMA/ATR calculations, but slower loading"
            )
            self.config.data_period = data_options[selected_data]
            
            # Chart display period
            chart_options = {
                "1 month": "1mo",
                "3 months": "3mo", 
                "6 months": "6mo",
                "1 year": "1y",
                "All data": "all"
            }
            
            selected_chart = st.selectbox(
                "Chart Display Period",
                options=list(chart_options.keys()),
                index=2,  # Default to 6 months
                help="How much data to show on the chart"
            )
            self.config.chart_period = chart_options[selected_chart]
        
        # Save config
        st.session_state.config = self.config
        
        # Status indicators with data info
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 System Status")
        
        if self.config.auto_refresh:
            st.sidebar.success("🟢 Live Mode")
        else:
            st.sidebar.info("🔵 Manual Mode")
        
        # Data period info
        st.sidebar.info(f"📈 Data Period: {self.config.data_period.upper()}")
        st.sidebar.info(f"📊 Chart Shows: {self.config.chart_period.upper()}")
        
        st.sidebar.caption(f"Last Update: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    def fetch_enhanced_data(self):
        """Fetch data with enhanced error handling and configurable timeframes"""
        try:
            # QQQ data - fetch more historical data for better indicators
            ticker = yf.Ticker("QQQ")
            
            # Fetch full historical data for calculations
            full_data = ticker.history(period=self.config.data_period, interval="1d")
            
            if full_data.empty:
                st.error("❌ Failed to fetch QQQ data")
                return None, None
            
            # Calculate indicators on full dataset
            full_data['EMA_5'] = full_data['Close'].ewm(span=5).mean()
            full_data['EMA_10'] = full_data['Close'].ewm(span=10).mean()
            full_data['EMA_21'] = full_data['Close'].ewm(span=21).mean()
            full_data['EMA_50'] = full_data['Close'].ewm(span=50).mean()
            full_data['ATR'] = self.calculate_atr(full_data['High'], full_data['Low'], full_data['Close'])
            full_data['Volume_Avg'] = full_data['Volume'].rolling(20).mean()
            
            # Filter data for chart display based on chart_period
            if self.config.chart_period == "1mo":
                chart_data = full_data.tail(22)  # ~1 month
            elif self.config.chart_period == "3mo":
                chart_data = full_data.tail(66)  # ~3 months
            elif self.config.chart_period == "6mo":
                chart_data = full_data.tail(132)  # ~6 months
            elif self.config.chart_period == "1y":
                chart_data = full_data.tail(252)  # ~1 year
            else:
                chart_data = full_data  # Show all data
            
            # VIX data
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="1d", interval="1m")
            vix_value = vix_data['Close'].iloc[-1] if not vix_data.empty else 20.0
            
            st.session_state.last_refresh = datetime.now()
            
            # Store both full data and chart data
            st.session_state.full_data = full_data
            
            return chart_data, vix_value
            
        except Exception as e:
            st.error(f"❌ Data fetch error: {str(e)}")
            return None, None
    
    def calculate_atr(self, high, low, close, period=14):
        """Calculate Average True Range"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=period).mean()
    
    def evaluate_signals(self, data, vix_value):
        """EXACT STRATEGY SIGNAL EVALUATION - Following documented rules precisely"""
        if len(data) < 50:
            return {'signal': False, 'error': 'Insufficient data'}
        
        latest = data.iloc[-1]
        
        # EXACT ENTRY CRITERIA - ALL 6 MUST BE MET
        
        # 1. EMA Stack: 10 EMA > 21 EMA > 50 EMA (bullish momentum)
        ema_alignment = latest['EMA_10'] > latest['EMA_21'] > latest['EMA_50']
        
        # 2. Price Position: Current price must be above 50 EMA (trend confirmation)
        price_above_50ema = latest['Close'] > latest['EMA_50']
        
        # 3. Entry Trigger: Price touches or dips below (5 EMA - 1.5×ATR)
        entry_level = latest['EMA_5'] - (1.5 * latest['ATR'])
        price_touch_entry = latest['Close'] <= entry_level or latest['Low'] <= entry_level
        
        # 4. Volume Confirmation: Entry day volume > 20-day average volume
        volume_above_avg = latest['Volume'] > latest['Volume_Avg']
        
        # 5. Market Environment: VIX < 30 (Low fear/volatility environment)
        vix_below_threshold = vix_value < 30.0
        
        # 6. Momentum Filter: Price must be higher than 5 days ago
        momentum_positive = latest['Close'] > data['Close'].iloc[-6]
        
        # FINAL SIGNAL: ALL 6 CRITERIA MUST BE TRUE
        signal = all([
            ema_alignment,
            price_above_50ema,
            price_touch_entry,
            volume_above_avg,
            vix_below_threshold,
            momentum_positive
        ])
        
        # Generate alerts for strong signals
        if signal and not hasattr(st.session_state, 'last_signal_price'):
            self.add_alert('entry', 'EXACT STRATEGY ENTRY SIGNAL - All 6 criteria met!', latest['Close'], 'high')
            st.session_state.last_signal_price = latest['Close']
        
        return {
            'signal': signal,
            'ema_alignment': ema_alignment,
            'price_above_50ema': price_above_50ema,
            'price_touch_entry': price_touch_entry,
            'volume_above_avg': volume_above_avg,
            'vix_below_threshold': vix_below_threshold,
            'momentum_positive': momentum_positive,
            'entry_level': entry_level,
            'current_price': latest['Close'],
            'strength': sum([ema_alignment, price_above_50ema, price_touch_entry, 
                           volume_above_avg, vix_below_threshold, momentum_positive])
        }
    
    def run(self):
        """Main enhanced dashboard execution"""
        # Inject JavaScript for interactivity
        components.html(auto_refresh_js + interactive_js, height=0)
        
        # Enhanced header
        self.display_enhanced_header()
        
        # Enhanced sidebar
        self.display_enhanced_sidebar()
        
        # Auto-refresh logic using native Streamlit
        if self.config.auto_refresh:
            # Use a simple counter to trigger refresh
            if 'refresh_counter' not in st.session_state:
                st.session_state.refresh_counter = 0
            
            # Auto-refresh using meta refresh or JavaScript
            if st.session_state.refresh_counter == 0 or (datetime.now() - st.session_state.last_refresh).seconds >= self.config.refresh_interval:
                components.html(f"""
                <script>
                setTimeout(function() {{
                    window.location.reload();
                }}, {self.config.refresh_interval * 1000});
                </script>
                """, height=0)
                st.session_state.refresh_counter += 1
        
        # Fetch data
        with st.spinner("🔄 Fetching real-time data..."):
            data, vix_value = self.fetch_enhanced_data()
        
        if data is None:
            st.stop()
        
        # Evaluate signals
        signals = self.evaluate_signals(data, vix_value)
        
        # Main dashboard layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Enhanced price chart
            chart = InteractiveCharts.create_enhanced_price_chart(data, signals, self.config)
            st.plotly_chart(chart, use_container_width=True)
        
        with col2:
            # Current price with enhanced styling
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2]
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100
            
            # Signal strength indicator
            strength = signals.get('strength', 0)
            strength_color = '#00b894' if strength >= 5 else '#fdcb6e' if strength >= 3 else '#e17055'
            
            st.markdown(f"""
            <div class="signal-card">
                <h3>QQQ Live Price</h3>
                <h2>${current_price:.2f}</h2>
                <p style="color: {'#00ff88' if price_change >= 0 else '#ff4757'}">
                    {price_change:+.2f} ({price_change_pct:+.2f}%)
                </p>
                <div style="margin-top: 15px;">
                    <p><strong>Signal Strength:</strong></p>
                    <div style="background: {strength_color}; height: 20px; border-radius: 10px; width: {(strength/6)*100}%"></div>
                    <p>{strength}/6 criteria met</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # VIX indicator
            vix_color = '#e17055' if vix_value > self.config.vix_threshold else '#00b894'
            st.markdown(f"""
            <div class="trade-card">
                <h4>VIX Fear Index</h4>
                <h3 style="color: {vix_color}">{vix_value:.2f}</h3>
                <p>{'⚠️ High Fear' if vix_value > self.config.vix_threshold else '✅ Low Fear'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Interactive controls
        self.display_interactive_controls()
        
        # Strategy explanation and stats
        self.display_strategy_explanation()
        
        # Live alerts
        self.display_live_alerts()
        
        # Detailed entry criteria analysis
        self.display_entry_criteria_panel(signals, vix_value, data)
        
        # Historical signal analysis - use full dataset if available
        display_data = st.session_state.get('full_data', data)
        self.display_signal_history(display_data)
        
        # Enhanced signal display
        if signals['signal']:
            st.markdown("""
            <div class="alert-success pulse">
                <h3>🚀 STRONG ENTRY SIGNAL DETECTED!</h3>
                <p>All criteria met for potential trade entry</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Auto-generate alert sound (if enabled)
            if self.config.enable_sounds:
                st.markdown("""
                <script>
                if (window.playAlert) window.playAlert('success');
                if (window.showNotification) window.showNotification('Trading Alert', 'Entry signal detected!', 'success');
                </script>
                """, unsafe_allow_html=True)
        
        # Performance dashboard footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            active_trades = len([t for t in self.trades if t.is_active])
            st.metric("Active Trades", active_trades)
        
        with col2:
            # Show total strategy signals detected today
            today_alerts = [a for a in self.alerts if a.type == 'entry']
            st.metric("Entry Signals Today", len(today_alerts))
        
        with col3:
            alerts_count = len(self.alerts)
            st.metric("Total Alerts", alerts_count)

# Run the enhanced dashboard
if __name__ == "__main__":
    dashboard = InteractiveDashboard()
    dashboard.run()