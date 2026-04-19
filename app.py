import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =========================
# CONFIG
# =========================
HISTORY_URL = "https://docs.google.com/spreadsheets/d/1yhBY-zRPlsd350gUEaEakIMmHeDsy7SCoyzONyoTiGM/export?format=csv&gid=1806324328"

# 👉 UPDATE gid event của bạn
EVENT_URL = "https://docs.google.com/spreadsheets/d/1yhBY-zRPlsd350gUEaEakIMmHeDsy7SCoyzONyoTiGM/edit?gid=1566812210#gid=1566812210"

# =========================
# LOAD HISTORY
# =========================
@st.cache_data(ttl=300)
def load_history():
    try:
        df = pd.read_csv(HISTORY_URL, skiprows=5)
    except Exception as e:
        st.error(f"Lỗi load HISTORY: {e}")
        return pd.DataFrame()

    # rename
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # 🔥 CLEAN NUMBER (QUAN TRỌNG)
    for col in df.columns[1:]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(" ", "", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")

    return df


# =========================
# LOAD EVENT
# =========================
@st.cache_data(ttl=300)
def load_event():
    try:
        df = pd.read_csv(EVENT_URL)
    except:
        return pd.DataFrame()

    if "Ngày bắt đầu" in df.columns:
        df["Ngày bắt đầu"] = pd.to_datetime(df["Ngày bắt đầu"], errors="coerce")

    if "Ngày kết thúc" in df.columns:
        df["Ngày kết thúc"] = pd.to_datetime(df["Ngày kết thúc"], errors="coerce")

    return df


# =========================
# INIT
# =========================
st.set_page_config(layout="wide")
st.title("🌍 Macro Market Dashboard")

df = load_history()
event_df = load_event()

if df.empty:
    st.stop()

assets = df.columns[1:]

# =========================
# SIDEBAR
# =========================
st.sidebar.header("⚙️ Cài đặt")

selected_assets = st.sidebar.multiselect(
    "Chọn tài sản",
    assets,
    default=list(assets)
)

normalize = st.sidebar.checkbox("Normalize về 100", False)

time_range = st.sidebar.selectbox(
    "Khoảng thời gian",
    ["1M", "3M", "1Y", "ALL"]
)

show_last = st.sidebar.checkbox("Hiển thị giá hiện tại", True)

# =========================
# FILTER TIME
# =========================
def filter_time(df):
    if time_range == "ALL":
        return df

    days_map = {"1M": 30, "3M": 90, "1Y": 365}
    days = days_map[time_range]

    cutoff = df["Date"].max() - pd.Timedelta(days=days)
    return df[df["Date"] >= cutoff]

df = filter_time(df)

# =========================
# NORMALIZE
# =========================
if normalize:
    df_norm = df.copy()
    for col in selected_assets:
        base = df[col].iloc[0]
        if pd.notna(base) and base != 0:
            df_norm[col] = df[col] / base * 100
    df = df_norm

# =========================
# PLOT
# =========================
fig = go.Figure()

for i, asset in enumerate(selected_assets):

    if i == 0:
        axis_name = "y"
        layout_axis = "yaxis"
    else:
        axis_name = f"y{i+1}"
        layout_axis = f"yaxis{i+1}"

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df[asset],
        name=asset,
        yaxis=axis_name
    ))

    # label giá cuối
    if show_last and len(df) > 0:
        value = df[asset].iloc[-1]

        label = f"{value:,.2f}" if pd.notna(value) else "N/A"

        fig.add_trace(go.Scatter(
            x=[df["Date"].iloc[-1]],
            y=[value],
            mode="markers+text",
            text=[label],
            textposition="middle right",
            showlegend=False,
            yaxis=axis_name
        ))

    # 🔥 FIX ĐÚNG CHUẨN PLOTLY
    fig.update_layout({
        layout_axis: dict(
            overlaying="y",
            showticklabels=False
        )
    })

# =========================
# EVENT OVERLAY
# =========================
if not event_df.empty and "Ngày bắt đầu" in event_df.columns:

    for _, row in event_df.iterrows():

        start = row.get("Ngày bắt đầu")
        end   = row.get("Ngày kết thúc")
        label = row.get("Nội dung", "")
        color = row.get("Mã màu", "rgba(255,0,0,0.2)")

        if pd.isna(start):
            continue

        if pd.isna(end):
            end = df["Date"].max()

        if start != end:
            fig.add_vrect(
                x0=start,
                x1=end,
                fillcolor=color,
                opacity=0.2,
                line_width=0,
                annotation_text=label,
                annotation_font_size=10
            )
        else:
            fig.add_vline(
                x=start,
                line_dash="dot",
                line_color=color,
                annotation_text=label,
                annotation_font_size=10
            )

# =========================
# LAYOUT
# =========================
fig.update_layout(
    height=700,
    hovermode="x unified",
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)
