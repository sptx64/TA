import streamlit as st
import yfinance as yf
import pandas as pd
import os
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from app.ta import ao, bob_ao, get_squeeze, get_kc, HU

st.set_page_config(layout = 'wide')

from app.logging import logging
logging(st.secrets["secret1"], st.secrets["secret2"])


import ta
import numpy as np
st.caption("*NOT FINANCIAL ADVICE!! FOR EDUCATION ONLY*")
"# :zap: Zeus"
st.caption("_Zeus (/zjuːs/; Ancient Greek: Ζεύς)[a] is the sky and thunder god in ancient Greek religion and mythology, who rules as king of the gods on Mount Olympus. His name is cognate with the first syllable of his Roman equivalent Jupiter._")
""
""

market = st.sidebar.radio('Market', ['sp500', 'crypto'], index=1)

broker="binance"
if market == "crypto" :
    broker = st.sidebar.radio("broker", ["binance","coinbase"], index=1)

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


with st.expander("Plot options") :
    col1,col2,col3,col4 = st.columns(4)
    MAs=col1.multiselect("Show moving averages", [6, 14, 20, 50, 200], None, placeholder="Choose MA to display")
    show_ema = col1.toggle("Show EMA")
    c1,c2,c3 = col1.columns(3)
    ma6_color=c1.color_picker("6MA", "#00FFFB")
    ma14_color=c2.color_picker("14MA", "#FFA200")
    ma20_color=c3.color_picker("20MA", "#E400DF")
    ma50_color=c1.color_picker("50MA", "#550092")
    ma200_color=c2.color_picker("200MA", "#0009FF")
    dict_ma_colors={"6":ma6_color, "14":ma14_color, "20":ma20_color, "50":ma50_color, "200":ma200_color}

    UHCs = col2.toggle("Show Hammer/Umbrella candles")
    



    

#compute
#Moving averages
ma_cns=[]
for ma in MAs :
    cn=f"EMA{ma}" if show_ema else f"SMA{ma}"
    data[f"{cn}"] = data["Close"].ewm(span=ma, adjust=False).mean() if show_ema else data["Close"].rolling(ma).mean()
    ma_cns.append(cn)

#Umbrella and Hammer
if UHCs :
    data["HU"] = HU(data)
    hammers = data[data["HU"]=="hammer"]
    umbrellas = data[data["HU"]=="umbrella"]


#plot
fig=go.Figure()
fig.add_trace(go.Candlestick( x=data["Date"].values, name="daily candles", open=data["Open"].values, high=data["High"].values, low=data["Low"].values, close=data["Close"].values,
                              increasing=dict(line=dict(color="palegreen")), decreasing=dict(line=dict(color="antiquewhite"))))
for cn in ma_cns :
    ma=cn.replace("EMA","") if show_ema else cn.replace("SMA","")
    fig.add_trace(go.Scatter(x=data["Date"].values, y=data[cn].values, name=cn, mode="lines", line_color=dict_ma_colors[ma]))

if UMCs :
    fig.add_trace(go.Candlestick( x=hammers["Date"].values, name="hammers", open=hammers["Open"].values,
                                 high=hammers["High"].values, low=hammers["Low"].values,
                                 close=hammers["Close"].values, increasing=dict(line=dict(color="red")),
                                 decreasing=dict(line=dict(color="red"))))

    fig.add_trace(go.Candlestick( x=umbrellas["Date"].values, name="umbrellas", open=umbrellas["Open"].values,
                                 high=umbrellas["High"].values, low=umbrellas["Low"].values,
                                 close=umbrellas["Close"].values, increasing=dict(line=dict(color="green")),
                                 decreasing=dict(line=dict(color="green"))))

fig.update_layout(height=650, template='simple_white', title_text=f"{ticker} daily")
fig.update_xaxes(rangeslider_visible=False, title="Date")

st.plotly_chart(fig, use_container_width=True)
