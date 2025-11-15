import os
import json
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Any, Dict, List

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    HAS_BCRYPT = False

st.set_page_config(page_title="FinanzApp", page_icon="💹", layout="wide")

DARK_CSS = """
<style>
body, .css-1d391kg { background-color:#0e1117; color:#e6eef3; }
.block-container { padding: 1rem 2rem; }
[data-testid="stSidebar"] { background-color:#0b0f14; color:#e6eef3; }
footer { visibility: hidden; }
.kpi .label { color:#9aa6b2; font-weight:600; display:block; }
.kpi .value { color:#e6eef3; font-weight:700; }
.card { background:#0b1116; border:1px solid #1b2430; border-radius:10px; padding:0.6rem; }
a { color: #9cc3ff; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

HEADER = "FinanzApp — powered by EODHD"
st.markdown(f"<div style='text-align:right;color:#9aa6b2;font-size:0.9rem'>{HEADER}</div>", unsafe_allow_html=True)

API_KEY = st.secrets.get("EODHD_API_KEY", "tu_api_key_aqui")
USERS_FILE = "users_example.json"

def load_users() -> Dict[str, Any]:
    if not os.path.exists(USERS_FILE):
        return {"usuarios": []}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "usuarios" in data:
        return data
    if isinstance(data, dict):
        usuarios = []
        for k,v in data.items():
            entry = {"username": k}
            entry.update(v if isinstance(v, dict) else {})
            usuarios.append(entry)
        return {"usuarios": usuarios}
    return {"usuarios": []}

def save_users(data: Dict[str, Any]) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def verify_password(stored: str, provided: str) -> bool:
    if not stored:
        return False
    if isinstance(stored, str) and stored.startswith("$2"):
        if not HAS_BCRYPT:
            return False
        try:
            return bcrypt.checkpw(provided.encode(), stored.encode())
        except Exception:
            return False
    return stored == provided

def authenticate_user(username: str, password: str) -> bool:
    users = load_users().get("usuarios", [])
    for u in users:
        if u.get("username") == username:
            return verify_password(u.get("password"), password)
    return False

def add_ticker_history(username: str, ticker: str) -> None:
    data = load_users()
    for u in data.get("usuarios", []):
        if u.get("username") == username:
            hist = u.setdefault("historial", [])
            if ticker not in hist:
                hist.insert(0, ticker)
                if len(hist) > 50:
                    hist.pop()
            break
    try:
        save_users(data)
    except Exception:
        pass

def get_user_history(username: str) -> List[str]:
    for u in load_users().get("usuarios", []):
        if u.get("username") == username:
            return u.get("historial", [])
    return []

BASE = "https://eodhd.com/api"

@st.cache_data(ttl=300)
def fetch_eod(ticker: str, start: date, end: date) -> pd.DataFrame:
    params = {"from": start.strftime("%Y-%m-%d"), "to": end.strftime("%Y-%m-%d"),
              "fmt":"json","period":"d","api_token":API_KEY}
    url = f"{BASE}/eod/{ticker}"
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or len(data) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={c:c.lower() for c in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    for col in ["open","high","low","close","volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("date")

@st.cache_data(ttl=600)
def fetch_fundamentals(ticker: str) -> Dict[str, Any]:
    url = f"{BASE}/fundamentals/{ticker}"
    r = requests.get(url, params={"api_token":API_KEY}, timeout=20)
    if r.status_code != 200:
        return {}
    return r.json()

@st.cache_data(ttl=300)
def fetch_news(ticker: str, start: date, end: date, limit: int = 5):
    url = f"{BASE}/news"
    r = requests.get(url, params={"s": ticker, "from": start.strftime("%Y-%m-%d"),
                                  "to": end.strftime("%Y-%m-%d"), "limit": str(limit), "api_token": API_KEY}, timeout=20)
    if r.status_code != 200:
        return []
    return r.json()

if "lang" not in st.session_state:
    st.session_state["lang"] = "es"
lang_choice = st.sidebar.selectbox("Idioma / Language", ["Español", "English"], index=0 if st.session_state["lang"]=="es" else 1)
st.session_state["lang"] = "es" if lang_choice.startswith("Esp") else "en"

L = {
    "es": {
        "title_login":"Iniciar sesión",
        "user":"Usuario", "pass":"Contraseña", "login":"Iniciar sesión", "logout":"Cerrar sesión",
        "symbol":"Símbolo (ej. AAPL.US)","period":"Período","show_volume":"Mostrar volumen",
        "show_fund":"Mostrar fundamentales","show_news":"Mostrar noticias","compare":"Comparar empresas",
        "no_data":"No se encontraron datos para el símbolo seleccionado.","sma_above":"🔔 El precio está por encima de la SMA20",
        "sma_below":"⚠️ El precio está por debajo de la SMA20","add_user":"Agregar usuario (admin)"
    },
    "en": {
        "title_login":"Login","user":"Username","pass":"Password","login":"Login","logout":"Logout",
        "symbol":"Symbol (e.g. AAPL.US)","period":"Period","show_volume":"Show volume",
        "show_fund":"Show fundamentals","show_news":"Show news","compare":"Compare companies",
        "no_data":"No data found for the selected symbol.","sma_above":"🔔 Price is above SMA20","sma_below":"⚠️ Price is below SMA20","add_user":"Add user (admin)"
    }
}[st.session_state["lang"]]

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.header(L["title_login"])
    uname = st.text_input(L["user"])
    pwd = st.text_input(L["pass"], type="password")
    if st.button(L["login"]):
        if authenticate_user(uname.strip(), pwd):
            st.session_state["user"] = uname.strip()
            st.success(f"{L['login']} ✅")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos" if st.session_state["lang"]=="es" else "Invalid username or password")
    st.stop()

st.sidebar.markdown(f"**Usuario:** {st.session_state['user']}")
symbol = st.sidebar.text_input(L["symbol"], value="AAPL.US").upper().strip()
period_choice = st.sidebar.selectbox(L["period"], ["1M","3M","6M","1Y","MAX"], index=2)
show_volume = st.sidebar.checkbox(L["show_volume"], value=True)
show_fund = st.sidebar.checkbox(L["show_fund"], value=False)
show_news = st.sidebar.checkbox(L["show_news"], value=False)
compare_mode = st.sidebar.checkbox(L["compare"], value=False)

if st.sidebar.button(L["add_user"]) and st.session_state.get("user") == "admin":
    newu = st.sidebar.text_input("Nuevo usuario")
    newp = st.sidebar.text_input("Nueva contraseña", type="password")
    if st.sidebar.button("Crear nuevo usuario"):
        data = load_users()
        data.setdefault("usuarios", [])
        data["usuarios"].append({"username": newu, "password": newp, "historial": []})
        save_users(data)
        st.sidebar.success("Usuario agregado")

if st.sidebar.button(L["logout"]):
    st.session_state.clear()
    st.experimental_rerun()

st.title("FinanzApp")

today = date.today()
if period_choice == "1M":
    start_date = today - relativedelta(months=1)
elif period_choice == "3M":
    start_date = today - relativedelta(months=3)
elif period_choice == "6M":
    start_date = today - relativedelta(months=6)
elif period_choice == "1Y":
    start_date = today - relativedelta(years=1)
else:
    start_date = today - relativedelta(years=5)

try:
    df = fetch_eod(symbol, start_date, today)
except Exception as e:
    st.error(f"Error fetching prices: {e}")
    df = pd.DataFrame()

if df.empty:
    st.warning(L["no_data"])
else:
    add_ticker_history(st.session_state["user"], symbol)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["date"], open=df.get("open"), high=df.get("high"), low=df.get("low"), close=df.get("close"), name=symbol))
    if show_volume and "volume" in df.columns:
        fig.add_trace(go.Bar(x=df["date"], y=df["volume"], name="Volume", opacity=0.2, yaxis="y2"))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False))
    fig.update_layout(template="plotly_dark", height=560, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig, use_container_width=True)

    if len(df) >= 20:
        sma20 = df["close"].rolling(20).mean().iloc[-1]
        last = df["close"].iloc[-1]
        if last > sma20:
            st.success(L["sma_above"])
        else:
            st.warning(L["sma_below"])

    if show_fund:
        f = fetch_fundamentals(symbol)
        st.subheader("Fundamentales" if st.session_state["lang"]=="es" else "Fundamentals")
        if f:
            gen = f.get("General", {})
            highlights = f.get("Highlights", {})
            df_f = pd.DataFrame({
                "Campo": ["Nombre","Sector","Market Cap","P/E","Dividend Yield"],
                "Valor": [gen.get("Name"), gen.get("Sector"), highlights.get("MarketCapitalization"), highlights.get("PERatio"), highlights.get("DividendYield")]
            })
            st.dataframe(df_f, use_container_width=True)
        else:
            st.info("No fundamentals found")

    if show_news:
        st.subheader("Noticias" if st.session_state["lang"]=="es" else "News")
        news = fetch_news(symbol, start, today)
        if not news:
            st.info("No news available")
        for n in news:
            title = n.get("title") or n.get("Title")
            link = n.get("link") or n.get("url") or ""
            st.markdown(f"**{title}**  \n{n.get('source','')}  \n[{link}]({link})")
            st.markdown("---")

    if compare_mode:
        st.subheader("Comparar empresas" if st.session_state["lang"]=="es" else "Compare companies")
        cmp = st.text_input("Ticker comparado (ej. MSFT.US)" if st.session_state["lang"]=="es" else "Ticker to compare (e.g. MSFT.US)")
        if cmp:
            try:
                df2 = fetch_eod(cmp.upper(), start_date, today)
                if not df2.empty:
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=df["date"], y=df["close"], name=symbol))
                    fig2.add_trace(go.Scatter(x=df2["date"], y=df2["close"], name=cmp.upper()))
                    fig2.update_layout(template="plotly_dark", height=420)
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
