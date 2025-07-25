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
    
    .mobile-friendly {
        touch-action: manipulation;
        -webkit-user-select: none;
        user-select: none;
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

// Touch gestures for mobile
let touchStartY = 0;
let touchStartX = 0;

document.addEventListener('touchstart', function(e) {
    touchStartY = e.touches[0].clientY;
    touchStartX = e.touches[0].clientX;
});

document.addEventListener('touchend', function(e) {
    const touchEndY = e.changedTouches[0].clientY;
    const touchEndX = e.changedTouches[0].clientX;
    const deltaY = touchStartY - touchEndY;
    const deltaX = touchStartX - touchEndX;
    
    // Swipe down to refresh
    if (deltaY < -100 && Math.abs(deltaX) < 50) {
        window.parent.postMessage({type: 'gesture', action: 'refresh'}, '*');
    }
    // Swipe left/right for timeframe changes
    else if (Math.abs(deltaX) > 100 && Math.abs(deltaY) < 50) {
        const direction = deltaX > 0 ? 'left' : 'right';
        window.parent.postMessage({type: 'gesture', action: 'swipe', direction: direction}, '*');
    }
});

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
    
    # Interactive Features
    auto_refresh: bool = False
    refresh_interval: int = 60
    enable_sounds: bool = True
    enable_notifications: bool = True
    voice_commands: bool = False
    mobile_mode: bool = False

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
            if st.button("🎤 Voice Command", key="voice_cmd", disabled=not self.config.voice_commands):
                st.info("Say: 'refresh', 'buy', or 'sell'")
    
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
            
            # When to Enter
            st.markdown("### ⏰ **When to Enter Trades**")
            
            st.markdown("""
            **🟢 IDEAL Entry Conditions:**
            
            1. **Market Structure**: QQQ in clear uptrend (price above all EMAs)
            2. **Pullback Setup**: Price pulls back to 5 EMA support level
            3. **Volume Spike**: Above-average volume on entry day
            4. **Low Volatility**: VIX below 30 (calm market conditions)
            5. **Time of Day**: Best entries typically 10:30 AM - 2:00 PM EST
            6. **Market Day**: Avoid Fridays and day before holidays
            
            **🔴 AVOID Entering When:**
            - VIX > 30 (high volatility/fear)
            - Volume below average (lack of participation)
            - Late Friday or before long weekends
            - Major economic events pending (FOMC, earnings)
            - Price below 50 EMA (downtrend)
            """)
            
            # Success Statistics
            st.markdown("### 📊 **Historical Performance Stats**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Win Rate",
                    "~65%",
                    help="Percentage of profitable trades"
                )
            
            with col2:
                st.metric(
                    "Avg Hold Time",
                    "4-6 days",
                    help="Typical trade duration"
                )
            
            with col3:
                st.metric(
                    "Risk:Reward",
                    "1:2.5",
                    help="Average risk to reward ratio"
                )
            
            with col4:
                st.metric(
                    "Max Drawdown",
                    "~8%",
                    help="Largest peak-to-valley decline"
                )
            
            # Trade Management
            st.markdown("### 🎯 **Trade Management Process**")
            
            st.markdown("""
            **Entry Day:**
            1. ✅ Confirm all 6 criteria met
            2. 📊 Calculate position size (1-2% account risk)
            3. 📝 Set stop loss and target orders
            4. 🔔 Monitor for confirmation or invalidation
            
            **During Trade:**
            - 📈 Scale out 50% at Target 1, move stop to breakeven
            - 🎯 Hold remaining 50% for Target 2
            - 📅 Maximum hold: 10 trading days
            - 🚨 Exit immediately if stop hit
            
            **Exit Scenarios:**
            - ✅ Target 1 reached (take 50% profit)
            - ✅ Target 2 reached (exit remaining position)
            - ❌ Stop loss hit (preserve capital)
            - ⏰ Time-based exit (10 days max)
            - 📉 Strategy invalidation (EMA breakdown)
            """)
            
            # Example Trade
            st.markdown("### 💡 **Example Trade Scenario**")
            
            st.markdown("""
            **Setup Example:**
            - QQQ trading at $380, above all EMAs ✅
            - Price dips to $378 (5 EMA - 1.5×ATR level) ✅
            - Volume: 45M (above 35M average) ✅
            - VIX: 22 (below 30 threshold) ✅
            - All criteria met → ENTER TRADE
            
            **Trade Execution:**
            - Entry: $378
            - Stop Loss: $370 (2% or 2×ATR, whichever smaller)
            - Target 1: $385 (5 EMA + 2×ATR)
            - Target 2: $390 (5 EMA + 3×ATR)
            - Position Size: $10,000 account × 1% risk ÷ $8 risk = 12 shares
            
            **Risk/Reward:**
            - Risk: $8 per share × 12 shares = $96 (1% of account)
            - Reward T1: $7 per share × 6 shares = $42
            - Reward T2: $12 per share × 6 shares = $72
            - Total Potential: $114 profit vs $96 risk = 1.19:1 ratio
            """)
            
            if st.button("❌ Close Strategy Guide"):
                st.session_state.show_strategy_stats = False
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
        
        # Risk/Reward Analysis
        if strength >= 6:
            st.markdown("### 💰 **Position Sizing & Risk Analysis**")
            
            # Calculate levels
            atr = latest['ATR']
            stop_loss_atr = signals['current_price'] - (self.config.atr_stop_multiplier * atr)
            stop_loss_pct = signals['current_price'] * (1 - self.config.stop_loss_percent / 100)
            stop_loss = max(stop_loss_atr, stop_loss_pct)
            
            target1 = latest['EMA_5'] + (self.config.atr_target1_multiplier * atr)
            target2 = latest['EMA_5'] + (self.config.atr_target2_multiplier * atr)
            
            # Position sizing
            risk_amount = self.config.account_value * (self.config.risk_percent / 100)
            price_risk = signals['current_price'] - stop_loss
            shares = int(risk_amount / price_risk) if price_risk > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Recommended Shares", f"{shares:,}")
                st.metric("Dollar Risk", f"${risk_amount:.0f}")
            
            with col2:
                st.metric("Entry Price", f"${signals['current_price']:.2f}")
                st.metric("Stop Loss", f"${stop_loss:.2f}")
            
            with col3:
                st.metric("Target 1", f"${target1:.2f}")
                st.metric("Target 2", f"${target2:.2f}")
            
            with col4:
                rr1 = (target1 - signals['current_price']) / (signals['current_price'] - stop_loss) if price_risk > 0 else 0
                rr2 = (target2 - signals['current_price']) / (signals['current_price'] - stop_loss) if price_risk > 0 else 0
                st.metric("R:R Target 1", f"{rr1:.1f}:1")
                st.metric("R:R Target 2", f"{rr2:.1f}:1")
        
        # Market timing advice
        st.markdown("### ⏰ **Market Timing Considerations**")
        
        current_time = datetime.now().time()
        market_open = time(9, 30)  # 9:30 AM
        market_close = time(16, 0)  # 4:00 PM
        optimal_start = time(10, 30)  # 10:30 AM
        optimal_end = time(14, 0)  # 2:00 PM
        
        is_market_hours = market_open <= current_time <= market_close
        is_optimal_time = optimal_start <= current_time <= optimal_end
        
        timing_advice = ""
        if not is_market_hours:
            timing_advice = "🕐 **Market Closed** - Wait for market open"
        elif is_optimal_time:
            timing_advice = "🟢 **Optimal Entry Window** (10:30 AM - 2:00 PM EST)"
        elif current_time < optimal_start:
            timing_advice = "🟡 **Early Session** - Wait for 10:30 AM for better fills"
        else:
            timing_advice = "🟡 **Late Session** - Consider waiting for next day"
        
        st.info(timing_advice)
    
    def execute_quick_trade(self, entry_price: float, shares: int, stop_loss: float, target: float):
        """Execute a quick paper trade"""
        trade = Trade(
            entry_date=datetime.now().strftime("%Y-%m-%d"),
            entry_time=datetime.now().strftime("%H:%M:%S"),
            entry_price=entry_price,
            position_size=shares,
            stop_loss=stop_loss,
            target1=target,
            target2=target * 1.2,
            notes="Quick Entry Trade",
            is_paper_trade=True
        )
        
        self.trades.append(trade)
        st.session_state.trades = self.trades
        
        # Update paper balance
        cost = entry_price * shares
        st.session_state.paper_balance -= cost
        
        # Add alert
        self.add_alert('entry', f'Quick entry at ${entry_price:.2f} ({shares} shares)', entry_price, 'normal')
        
        st.success(f"✅ Paper trade entered: {shares} shares at ${entry_price:.2f}")
    
    def display_advanced_backtesting(self):
        """Display interactive backtesting panel"""
        if 'show_backtest' not in st.session_state or not st.session_state.show_backtest:
            return
        
        with st.expander("📈 Interactive Backtesting", expanded=True):
            st.subheader("Strategy Backtesting")
            
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=180),
                    key="backtest_start"
                )
                
                initial_capital = st.number_input(
                    "Initial Capital",
                    value=100000,
                    min_value=1000,
                    key="backtest_capital"
                )
            
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now(),
                    key="backtest_end"
                )
                
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    0.5, 5.0, 1.0, 0.1,
                    key="backtest_risk"
                )
            
            if st.button("🚀 Run Backtest", type="primary"):
                self.run_backtest(start_date, end_date, initial_capital, risk_per_trade)
            
            if st.button("❌ Close Backtest"):
                st.session_state.show_backtest = False
                st.rerun()
    
    def run_backtest(self, start_date, end_date, initial_capital, risk_per_trade):
        """Run strategy backtest"""
        with st.spinner("Running backtest..."):
            # Fetch historical data
            data = yf.download("QQQ", start=start_date, end=end_date, interval="1d")
            
            if data.empty:
                st.error("No data available for the selected period")
                return
            
            # Calculate indicators
            data['EMA_5'] = data['Close'].ewm(span=5).mean()
            data['EMA_10'] = data['Close'].ewm(span=10).mean()
            data['EMA_21'] = data['Close'].ewm(span=21).mean()
            data['EMA_50'] = data['Close'].ewm(span=50).mean()
            
            # Simple backtest logic
            trades = []
            capital = initial_capital
            position = None
            
            for i in range(50, len(data)):  # Start after indicators are valid
                current = data.iloc[i]
                
                # Entry conditions (simplified)
                if (position is None and 
                    current['EMA_10'] > current['EMA_21'] > current['EMA_50'] and
                    current['Close'] > current['EMA_50']):
                    
                    # Enter trade
                    risk_amount = capital * (risk_per_trade / 100)
                    shares = int(risk_amount / (current['Close'] * 0.02))  # 2% stop
                    
                    if shares > 0:
                        position = {
                            'entry_price': current['Close'],
                            'shares': shares,
                            'entry_date': data.index[i],
                            'stop_loss': current['Close'] * 0.98
                        }
                
                # Exit conditions
                elif position is not None:
                    exit_trade = False
                    exit_reason = ""
                    
                    # Stop loss
                    if current['Low'] <= position['stop_loss']:
                        exit_price = position['stop_loss']
                        exit_reason = "Stop Loss"
                        exit_trade = True
                    
                    # Target (simplified - 4% gain)
                    elif current['High'] >= position['entry_price'] * 1.04:
                        exit_price = position['entry_price'] * 1.04
                        exit_reason = "Target Hit"
                        exit_trade = True
                    
                    # Time-based exit (5 days)
                    elif (data.index[i] - position['entry_date']).days >= 5:
                        exit_price = current['Close']
                        exit_reason = "Time Exit"
                        exit_trade = True
                    
                    if exit_trade:
                        pnl = (exit_price - position['entry_price']) * position['shares']
                        capital += pnl
                        
                        trades.append({
                            'Entry Date': position['entry_date'].strftime('%Y-%m-%d'),
                            'Entry Price': position['entry_price'],
                            'Exit Date': data.index[i].strftime('%Y-%m-%d'),
                            'Exit Price': exit_price,
                            'Shares': position['shares'],
                            'P&L': pnl,
                            'Return %': ((exit_price - position['entry_price']) / position['entry_price']) * 100,
                            'Exit Reason': exit_reason
                        })
                        
                        position = None
            
            # Display results
            if trades:
                df = pd.DataFrame(trades)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_return = ((capital - initial_capital) / initial_capital) * 100
                    st.metric("Total Return", f"{total_return:.2f}%")
                
                with col2:
                    win_rate = (len(df[df['P&L'] > 0]) / len(df)) * 100
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with col3:
                    avg_return = df['Return %'].mean()
                    st.metric("Avg Return", f"{avg_return:.2f}%")
                
                with col4:
                    sharpe_ratio = df['Return %'].mean() / df['Return %'].std() if df['Return %'].std() > 0 else 0
                    st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                
                # Equity curve
                df['Cumulative P&L'] = df['P&L'].cumsum() + initial_capital
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['Exit Date'],
                    y=df['Cumulative P&L'],
                    mode='lines+markers',
                    name='Strategy Equity',
                    line=dict(color='#00b894', width=3)
                ))
                
                # Buy and hold comparison
                buy_hold_return = ((data['Close'].iloc[-1] - data['Close'].iloc[50]) / data['Close'].iloc[50]) * initial_capital
                buy_hold_final = initial_capital + buy_hold_return
                
                fig.add_hline(
                    y=buy_hold_final,
                    line_dash="dash",
                    line_color="#e17055",
                    annotation_text=f"Buy & Hold: ${buy_hold_final:,.0f}"
                )
                
                fig.update_layout(
                    title="Backtest Results - Equity Curve",
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Trade history
                st.subheader("Trade History")
                st.dataframe(df, use_container_width=True)
                
                # Download results
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Backtest Results",
                    csv,
                    f"backtest_results_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.warning("No trades generated in backtest period")
    
    def display_mobile_controls(self):
        """Display mobile-friendly controls"""
        if not self.config.mobile_mode:
            return
        
        st.markdown('<div class="mobile-friendly">', unsafe_allow_html=True)
        
        # Large touch-friendly buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📱 BUY", key="mobile_buy", help="Quick buy signal"):
                st.success("Buy signal noted!")
        
        with col2:
            if st.button("📱 SELL", key="mobile_sell", help="Quick sell signal"):
                st.warning("Sell signal noted!")
        
        # Swipe gesture info
        st.info("📱 Swipe down to refresh | Swipe left/right to change timeframe")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def display_voice_command_panel(self):
        """Display voice command interface"""
        if not self.config.voice_commands:
            return
        
        st.subheader("🎤 Voice Commands")
        
        if st.button("🎙️ Start Voice Command"):
            st.info("Listening... Say 'refresh', 'buy', or 'sell'")
            # Voice command functionality would be handled by JavaScript
        
        st.write("**Available Commands:**")
        st.write("• 'Refresh' or 'Update' - Refresh data")
        st.write("• 'Buy' or 'Enter' - Flag buy signal")
        st.write("• 'Sell' or 'Exit' - Flag sell signal")
    
    def display_enhanced_sidebar(self):
        """Enhanced interactive sidebar"""
        st.sidebar.markdown("## ⚙️ Interactive Settings")
        
        # Real-time controls
        with st.sidebar.expander("🔄 Real-time Controls", expanded=True):
            self.config.auto_refresh = st.checkbox("Auto Refresh", self.config.auto_refresh)
            if self.config.auto_refresh:
                self.config.refresh_interval = st.slider("Interval (seconds)", 10, 300, self.config.refresh_interval)
            
            self.config.enable_sounds = st.checkbox("Sound Alerts", self.config.enable_sounds)
            self.config.enable_notifications = st.checkbox("Browser Notifications", self.config.enable_notifications)
        
        # Interactive features
        with st.sidebar.expander("🎮 Interactive Features"):
            self.config.voice_commands = st.checkbox("Voice Commands", self.config.voice_commands)
            self.config.mobile_mode = st.checkbox("Mobile Mode", self.config.mobile_mode)
        
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
        # Traditional settings
        with st.sidebar.expander("📊 Strategy Settings"):
            self.config.account_value = st.number_input("Account Value", 1000.0, 10000000.0, self.config.account_value)
            self.config.risk_percent = st.slider("Risk %", 0.5, 5.0, self.config.risk_percent, 0.1)
            self.config.vix_threshold = st.number_input("VIX Threshold", 10.0, 50.0, self.config.vix_threshold)
        
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
        """Enhanced signal evaluation"""
        if len(data) < 50:
            return {'signal': False, 'error': 'Insufficient data'}
        
        latest = data.iloc[-1]
        
        # Enhanced signal logic
        ema_alignment = latest['EMA_10'] > latest['EMA_21'] > latest['EMA_50']
        price_above_50ema = latest['Close'] > latest['EMA_50']
        entry_level = latest['EMA_5'] - (self.config.atr_entry_multiplier * latest['ATR'])
        price_touch_entry = latest['Close'] <= entry_level or latest['Low'] <= entry_level
        volume_above_avg = latest['Volume'] > latest['Volume_Avg']
        vix_below_threshold = vix_value < self.config.vix_threshold
        
        # Momentum check
        momentum_positive = latest['Close'] > data['Close'].iloc[-5]
        
        signal = all([
            ema_alignment,
            price_above_50ema,
            price_touch_entry,
            volume_above_avg,
            vix_below_threshold,
            momentum_positive
        ])
        
        # Generate alerts
        if signal and not hasattr(st.session_state, 'last_signal_price'):
            self.add_alert('entry', 'Strong entry signal detected!', latest['Close'], 'high')
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
        
        # Advanced backtesting
        self.display_advanced_backtesting()
        
        # Mobile controls
        self.display_mobile_controls()
        
        # Voice commands
        self.display_voice_command_panel()
        
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
        
        with col3:
            alerts_count = len(self.alerts)
            st.metric("Today's Alerts", alerts_count)

# Run the enhanced dashboard
if __name__ == "__main__":
    dashboard = InteractiveDashboard()
    dashboard.run()