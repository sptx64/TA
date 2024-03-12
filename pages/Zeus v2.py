import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from app.ta import ao, bob_ao, get_squeeze, get_kc, HU, RSI

st.set_page_config(layout = 'wide')

from app.logging import logging
logging(st.secrets["secret1"], st.secrets["secret2"])


import ta
import numpy as np

def div(df, close, indicator, indicator_filter) :
    import numpy as np
    df = df.reset_index(drop=True)
    ind = df[indicator].values
    df['top'], df['bot'] = False, False

    if indicator.startswith("RSI") or indicator.startswith("Volume"):
        from scipy.signal import argrelextrema
        distance = 9
        tops = argrelextrema(ind, np.greater, order=distance)
        bottoms = argrelextrema(ind, np.less, order=distance)

        for i in tops[0] :
            df['top'][i] = True

        for i in bottoms[0] :
            df['bot'][i] = True

    else :
        df.loc[(df[indicator_filter].values == "Bearish") & (df[indicator_filter].shift(1) == "Bullish"), "top"]=True
        df.loc[(df[indicator_filter].values == "Bullish") & (df[indicator_filter].shift(1) == "Bearish"), "bot"]=True


    df_bottom = df[df['bot'].values == True]
    df_bottom.loc[:, 'bullish_div'] = False
    df_bottom.loc[(df_bottom[indicator].values >= df_bottom[indicator].shift(1)) & (df_bottom[close] <= df_bottom[close].shift(1)), 'bullish_div'] = True

    df_top = df[df['top'].values == True]
    df_top.loc[:, 'bearish_div'] = False
    df_top.loc[(df_top[indicator] <= df_top[indicator].shift(1)) & (df_top[close] >= df_top[close].shift(1)), 'bearish_div'] = True
    return df, df_bottom, df_top










st.sidebar.caption("*NOT FINANCIAL ADVICE!! FOR EDUCATION ONLY*")
":zap:"
st.caption("_Zeus (/zjuːs/; Ancient Greek: Ζεύς)[a] is the sky and thunder god in ancient Greek religion and mythology, who rules as king of the gods on Mount Olympus. His name is cognate with the first syllable of his Roman equivalent Jupiter._")
""
c1,c2=st.sidebar.columns(2)
market = c1.radio('Market', ['sp500', 'crypto'], index=1)

broker="binance"
if market == "crypto" :
    broker = c2.radio("broker", ["binance","coinbase"], index=1)

path = f'dataset/{market}_{broker}/' if market == "crypto" else f'dataset/{market}/'

tables = [x.replace(".parquet","") for x in os.listdir(path)]

# Create dropdown menu to select ticker
ticker = st.sidebar.selectbox("Select a ticker:", tables)
emoji = ":chart_with_upwards_trend:" if market == "sp500" else ":coin:"
f"# {emoji} {market} - {ticker}"

try:
    # Download data for selected ticker
    data = pd.read_parquet(f"{path}{ticker}.parquet")
except :
    st.error('Erreur')
    st.stop()

if broker == "coinbase" :
    data["order"] = data["Date"].str[-4:] + data["Date"].str[3:5] + data["Date"].str[:2]
    data["order"] = data["order"].astype(int)

if data.empty :
    st.error('empty table')
    st.stop()


window = 20
list_col = ["Close", "Open", "High", "Low", "Volume"]
for col in list_col :
    data[col] = data[col].astype(float)

if market == 'crypto' :
    data['Date'] = data['order'].astype(str).str[6:8] + '/' + data['order'].astype(str).str[4:6] + '/' + data['order'].astype(str).str[:4]

data_len=len(data)
days = st.sidebar.slider("days to load", 2, data_len, 2000 if data_len>2000 else data_len)
data = data.tail(days)


col1,col2,col3,col4 = st.columns(4)
with col1.popover("Candles", use_container_width=True) :
    c1,c2=st.columns(2)
    incr_candle_color = c1.color_picker("incr. candle", "#FFFFFF")
    decr_candle_color = c2.color_picker("decr. candle", "#8E8E8E")

    
with col2.popover("Moving averages", use_container_width=True) :
    MAs=st.multiselect("Moving average", [6, 14, 20, 50, 200], None, placeholder="Choose MA periods to display")
    if len(MAs)>0 :
        show_ema = st.toggle("Show EMA")
        c1,c2,c3 = st.columns(3)
        ma6_color=c1.color_picker("6MA", "#00FFFB")
        ma14_color=c2.color_picker("14MA", "#FFA200")
        ma20_color=c3.color_picker("20MA", "#E400DF")
        ma50_color=c1.color_picker("50MA", "#550092")
        ma200_color=c2.color_picker("200MA", "#0009FF")
        dict_ma_colors={"6":ma6_color, "14":ma14_color, "20":ma20_color, "50":ma50_color, "200":ma200_color}

with col3.popover("Indicators", use_container_width=True) :
    RSIs=st.multiselect("RSI", [6, 14, 20, 50, 200], [14], placeholder="Choose RSI periods to display")
    c1,c2=st.columns(2)
    SR=c1.toggle("S/R")
    VOL=c2.toggle("Volume")
    AO=c1.toggle("AO")
    SMOM=c2.toggle("Squeeze Mom Lazy Bear")
    
    
with col4.popover("Doji", use_container_width=True) :
    UHCs = st.toggle("Hammer/umbrella")
    DGCs = st.toggle("Dragonfly/Gravestone")
    tweez = st.toggle("Tweezer candles")





subplot=0

#compute

#Moving averages
ma_cns=[]
for ma in MAs :
    cn=f"EMA{ma}" if show_ema else f"SMA{ma}"
    data[f"{cn}"] = data["Close"].ewm(span=ma, adjust=False).mean() if show_ema else data["Close"].rolling(ma).mean()
    ma_cns.append(cn)

#Umbrella and Hammer
if UHCs or DGCs :
    data["HU"] = HU(data)
    hammers = data[data["HU"].values=="hammer"]
    umbrellas = data[data["HU"].values=="umbrella"]
    if DGCs :
        oc_delta=hammers["Close"].values-hammers["Open"].values
        hl_delta=hammers["High"].values-hammers["Low"].values
        gravestones = hammers[np.abs(oc_delta)<(hl_delta*0.02)]
        
        oc_delta=umbrellas["Close"].values-umbrellas["Open"].values
        hl_delta=umbrellas["High"].values-umbrellas["Low"].values
        dragonflys = umbrellas[np.abs(oc_delta)<(hl_delta*0.02)]
        
if tweez :
    high, low, open, close = data["High"].values, data["Low"].values, data["Open"].values, data["Close"].values
    rnge = high-low
    top,bot=[],[]
    delta_allowed=0.005
    for i in range(len(high)) :
        if i==0 :
            top.append(False)
            continue
        val=(np.abs(high[i]-high[i-1]) < rnge[i]*delta_allowed) and (close[i] < open[i])
        top.append(val)

    for i in range(len(low)) :
        if i==0 :
            bot.append(False)
            continue
        val = np.abs(low[i]-low[i-1]) < rnge[i]*delta_allowed and (close[i] > open[i])
        bot.append(val)

    data["tweezer top"],data["tweezer bot"]=top,bot
    TT, TB = data[data["tweezer top"]], data[data["tweezer bot"]]
    
    


#RSI
cns_rsi=[]
if len(RSIs) > 0 :
    subplot+=1
    for period in RSIs :
        cns_rsi.append(f"RSI{period}")
        data[f"RSI{period}"] = RSI(data, period)

if AO :
    data["ao"] = ao(data)
    data["bob_ao"] = bob_ao(data)
    subplot+=1
    neg_rising=data[(data["bob_ao"].values=="Bullish") & (data["ao"].values<=0)]
    pos_rising=data[(data["bob_ao"].values=="Bullish") & (data["ao"].values>0)]
    pos_falling=data[(data["bob_ao"].values=="Bearish") & (data["ao"].values>0)]
    neg_falling=data[(data["bob_ao"].values=="Bearish") & (data["ao"].values<=0)]
    
if VOL :
    subplot+=1

    
    # neg_rising=data[(data["ao"].values <= 0) 

if SR :
    def float_to_rgba_jet(column):
        normalized_column = (column - column.min()) / (column.max() - column.min())
        rgb_column = []
        for i in normalized_column :
            if i <= 0.125:
                R, G, B, A = 0, 0, 4 * i + 0.5, 0.03
            elif i <= 0.375:
                R, G, B, A = 0, 4 * (i - 0.125), 1, 0.1
            elif i <= 0.625:
                R,G,B,A = 4 * (i - 0.375), 1, 1 - 4 * (i - 0.375), 0.2
            elif i <= 0.875:
                R, G, B, A = 1, 1 - 4 * (i - 0.625), 0, 0.5
            else:
                R,G,B,A = 1 - 4 * (i - 0.875), 0, 0, 0.7
                
            R, G, B = int(R * 255), int(G * 255), int(B * 255)
            rgb_value = (R, G, B, A)
            rgb_column.append('rgba'+str(rgb_value))
        return rgb_column

    data['volume_color'] = float_to_rgba_jet(data['Volume'])


if SMOM :
    def np_shift(array: np.ndarray, offset: int = 1, fill_value=np.nan):
        result = np.empty_like(array)
        if offset > 0:
            result[:offset] = fill_value
            result[offset:] = array[:-offset]
        elif offset < 0:
            result[offset:] = fill_value
            result[:offset] = array[-offset:]
        else:
            result[:] = array
        return result
    
    def Linreg(source, length, offset: int = 0):
        size = len(source)
        linear = np.zeros(size)
        for i in range(length, size):
            sumX = 0.0
            sumY = 0.0
            sumXSqr = 0.0
            sumXY = 0.0
    
            for z in range(length):
                val = source[i-z]
                per = z + 1.0
                sumX += per
                sumY += val
                sumXSqr += per * per
                sumXY += val * per
    
            slope = (length * sumXY - sumX * sumY) / (length * sumXSqr - sumX * sumX)
            average = sumY / length
            intercept = average - slope * sumX / length + slope
    
            linear[i] = intercept
    
        if offset != 0:
            linear = np_shift(linear, offset)
            
        return linear
    
    window, mult, window_kc, multKC = 20, 2.0, 20, 1.5
    
    # useTrueRange = input(true, title="Use TrueRange (KC)", type=bool)
    # Calculate BB
    source = data["Close"]
    basis = source.rolling(window).mean()
    dev = multKC * source.rolling(window).std()
    upperBB = basis + dev
    lowerBB = basis - dev
    
    # Calculate KC
    ma = source
    rnge = data["High"] - data["Low"]
    rangema = rnge.rolling(window_kc).mean()
    upperKC = ma + rangema * multKC
    lowerKC = ma - rangema * multKC
    
    sqzOn  = (lowerBB.values > lowerKC.values) & (upperBB.values < upperKC.values)
    sqzOff = (lowerBB.values < lowerKC.values) & (upperBB.values > upperKC.values)
    noSqz  = (sqzOn == False) & (sqzOff == False)
    
    mean_hl=[(x+y)/2 if (x>=0) & (y>=0) else 0 for x,y in zip(data["High"].rolling(window_kc).max().values, data["Low"].rolling(window_kc).min().values)]
    mean_hl_sma = [(x+y)/2 if (x>=0) & (y>=0) else 0 for x,y in zip(mean_hl, data["Close"].rolling(window_kc).mean())]
    
    data["Mom"] = Linreg(np.array((source.values-mean_hl_sma)), window_kc, 0)
    
    data["Squeeze"]="no sqz"
    data.loc[sqzOff, "Squeeze"]="sqz off"
    data.loc[sqzOn, "Squeeze"]="sqz on"
    
    data.loc[(data["Mom"].values <= data["Mom"].shift(1)), "bob_mom"]="Bearish"
    data.loc[(data["Mom"].values > data["Mom"].shift(1)), "bob_mom"]="Bullish"
    
    
    mom_neg_rising=data[(data["bob_mom"].values == "Bullish") & (data["Mom"]<0)]
    mom_pos_rising=data[(data["bob_mom"].values == "Bullish")  & (data["Mom"]>=0)]
    mom_pos_falling=data[(data["bob_mom"].values == "Bearish")  & (data["Mom"]>=0)]
    mom_neg_falling=data[(data["bob_mom"].values == "Bearish")  & (data["Mom"]<0)]
    
    subplot+=1



plotheight=700
subplotheight=150
#plot
if subplot>0 :
    heights=[0.7 if subplot<=2 else 0.6]
    for i in range(subplot) :
        heights.append((1-heights[0])/subplot)
    fig = make_subplots(rows=subplot+1, cols=1, row_heights=heights, shared_xaxes=True)
else :
    fig=go.Figure()

fig.add_trace(go.Candlestick( x=data["Date"].values, name="daily candles", open=data["Open"].values, high=data["High"].values, low=data["Low"].values, close=data["Close"].values,
                              increasing=dict(line=dict(color=incr_candle_color, width=0.5)), decreasing=dict(line=dict(color=decr_candle_color, width=0.5))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)
for cn in ma_cns :
    ma=cn.replace("EMA","") if show_ema else cn.replace("SMA","")
    fig.add_trace(go.Scatter(x=data["Date"].values, y=data[cn].values, name=cn, mode="lines", line_color=dict_ma_colors[ma]), col=None if subplot==0 else 1, row=None if subplot==0 else 1)

if UHCs :
    fig.add_trace(go.Candlestick( x=hammers["Date"].values, name="hammers", open=hammers["Open"].values,
                                 high=hammers["High"].values, low=hammers["Low"].values,
                                 close=hammers["Close"].values, increasing=dict(line=dict(color="gold", width=0.5)),
                                 decreasing=dict(line=dict(color="gold", width=0.5))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)

    fig.add_trace(go.Candlestick( x=umbrellas["Date"].values, name="umbrellas", open=umbrellas["Open"].values,
                                 high=umbrellas["High"].values, low=umbrellas["Low"].values,
                                 close=umbrellas["Close"].values, increasing=dict(line=dict(color="blue", width=0.5)),
                                 decreasing=dict(line=dict(color="blue", width=0.5))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)
if DGCs :
    fig.add_trace(go.Candlestick( x=gravestones["Date"].values, name="gravestones", open=gravestones["Open"].values,
                                 high=gravestones["High"].values, low=gravestones["Low"].values,
                                 close=gravestones["Close"].values, increasing=dict(line=dict(color="red", width=1)),
                                 decreasing=dict(line=dict(color="red", width=1))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)

    fig.add_trace(go.Candlestick( x=dragonflys["Date"].values, name="dragonflys", open=dragonflys["Open"].values,
                                 high=dragonflys["High"].values, low=dragonflys["Low"].values,
                                 close=dragonflys["Close"].values, increasing=dict(line=dict(color="lightseagreen", width=1)),
                                 decreasing=dict(line=dict(color="lightseagreen", width=1))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)

if tweez :
    fig.add_trace(go.Candlestick( x=TT["Date"].values, name="tweezer top", open=TT["Open"].values,
                                 high=TT["High"].values, low=TT["Low"].values,
                                 close=TT["Close"].values, increasing=dict(line=dict(color="orange", width=1)),
                                 decreasing=dict(line=dict(color="orange", width=1))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)
    
    fig.add_trace(go.Candlestick( x=TB["Date"].values, name="tweezer bot", open=TB["Open"].values,
                                 high=TB["High"].values, low=TB["Low"].values,
                                 close=TB["Close"].values, increasing=dict(line=dict(color="cyan", width=1)),
                                 decreasing=dict(line=dict(color="cyan", width=1))), col=None if subplot==0 else 1, row=None if subplot==0 else 1)

if SR :
    for i in range(len(data)) :
        row = data.iloc[i]
        fig.add_trace(go.Scatter(x=[row['Date'], data.iloc[-1]['Date']], y=[row['Close'], row['Close']], mode='lines', line_color=row['volume_color'], showlegend=False), col=None if subplot==0 else 1, row=None if subplot==0 else 1)



subplot_row = 2
if VOL:
    data_up=data[data["Open"].values<data["Close"].values]
    data_down=data[data["Open"].values>=data["Close"].values]
    for df, color in zip([data_up, data_down],["lightseagreen", "red"]) :
        fig.add_trace(go.Bar(x=df["Date"].values, y=df["Volume"].values, name="Volume", marker_color=color, marker_line_color="rgba(0,0,0,0)", marker_line_width=0), col=1, row=subplot_row)
    fig.update_layout(coloraxis_colorbar_x=-0.17)
    plotheight+=subplotheight
    subplot_row+=1




if len(RSIs) > 0 :
    for rs in cns_rsi :
        fig.add_trace(go.Scatter(x=data["Date"].values, y=data[rs].values, name=rs, mode="lines"), col=1, row=subplot_row)
        data, data_bottom, data_top = div(data, "Close", rs, None)
    
        for i in range(len(data_bottom)):
            row = data_bottom.iloc[i]
            prev_row = data_bottom.iloc[i-1]
            if row['bullish_div'] == True :
                x = [row['Date'], prev_row['Date']]
                y = [row[rs], prev_row[rs]]
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='limegreen', line_width=1, line_dash="dot", text=["BuD", "BuD"], textposition="bottom center", showlegend=False), col=1, row=subplot_row)
    
        for i in range(len(data_top)):
            row = data_top.iloc[i]
            prev_row = data_top.iloc[i-1]
            if row['bearish_div'] == True :
                x = [row['Date'], prev_row['Date']]
                y = [row[rs], prev_row[rs]]
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='crimson', line_width=1, line_dash="dot", text=["BeD", "BeD"], textposition="top center", showlegend = False), col=1, row=subplot_row)





    
    fig.add_hline(y=50, line_width=1, line_color="black", row=subplot_row)
    fig.add_hline(y=100, line_width=1, line_color="black", row=subplot_row)
    fig.add_hline(y=0, line_width=1, line_color="black", row=subplot_row)
    fig.add_hline(y=30, line_width=1, line_dash="dot", line_color="black", row=subplot_row)
    fig.add_hline(y=70, line_width=1, line_dash="dot", line_color="black", row=subplot_row)


    plotheight+=subplotheight
    subplot_row+=1

if AO :
    for df, color in zip([neg_rising, pos_rising, pos_falling, neg_falling],["lightseagreen", "lightseagreen", "red", "red"]) :
        fig.add_trace(go.Bar(x=df["Date"].values, y=df["ao"].values, name="AO", marker_color=color, marker_line_width=0), col=1, row=subplot_row)
    fig.add_hline(y=0, line_width=1, line_color="black", row=subplot_row)
    
    data, data_bottom, data_top = div(data, "Close", "ao", "bob_ao")

    for i in range(len(data_bottom)):
        row = data_bottom.iloc[i]
        prev_row = data_bottom.iloc[i-1]
        if row['bullish_div'] == True :
            x = [row['Date'], prev_row['Date']]
            y = [row['ao'], prev_row['ao']]
            fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='limegreen', line_width=1, line_dash="dot", text=["BuD", "BuD"], textposition="bottom center", showlegend=False), col=1, row=subplot_row)

    for i in range(len(data_top)):
        row = data_top.iloc[i]
        prev_row = data_top.iloc[i-1]
        if row['bearish_div'] == True :
            x = [row['Date'], prev_row['Date']]
            y = [row['ao'], prev_row['ao']]
            fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='crimson', line_width=1, line_dash="dot", text=["BeD", "BeD"], textposition="top center", showlegend = False), col=1, row=subplot_row)

    plotheight+=subplotheight
    subplot_row+=1

if SMOM :
    for df, color in zip([mom_neg_rising, mom_pos_rising, mom_pos_falling, mom_neg_falling],["darkred", "palegreen", "lightseagreen", "red"]) :
        fig.add_trace(go.Bar(x=df["Date"].values, y=df["Mom"].values, name="Momentum", marker_color=color, marker_line_width=0), col=1, row=subplot_row)
    fig.add_hline(y=0, line_width=1, line_color="black", row=subplot_row)
    
    data, data_bottom, data_top = div(data, "Close", "Mom", "bob_mom")

    for i in range(len(data_bottom)):
        row = data_bottom.iloc[i]
        prev_row = data_bottom.iloc[i-1]
        if row['bullish_div'] == True :
            x = [row['Date'], prev_row['Date']]
            y = [row['Mom'], prev_row['Mom']]
            fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='limegreen', line_width=1, line_dash="dot", text=["BuD", "BuD"], textposition="bottom center", showlegend=False), col=1, row=subplot_row)

    for i in range(len(data_top)):
        row = data_top.iloc[i]
        prev_row = data_top.iloc[i-1]
        if row['bearish_div'] == True :
            x = [row['Date'], prev_row['Date']]
            y = [row['Mom'], prev_row['Mom']]
            fig.add_trace(go.Scatter(x=x, y=y, mode='markers+lines+text', line_color='crimson', line_width=1, line_dash="dot", text=["BeD", "BeD"], textposition="top center", showlegend = False), col=1, row=subplot_row)

    plotheight+=subplotheight
    subplot_row+=1

fig.update_layout(height=800, template='simple_white', title_text=f"{ticker} daily")
fig.update_xaxes(rangeslider_visible=False, title="Date", visible=False)

st.plotly_chart(fig, use_container_width=True)
