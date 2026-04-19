import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# =========================
# CONFIG (UPDATE LINK CHUẨN)
# =========================
HISTORY_URL = "https://docs.google.com/spreadsheets/d/1yhBY-zRPlsd350gUEaEakIMmHeDsy7SCoyzONyoTiGM/export?format=csv&gid=1806324328"

# 👉 THAY gid EVENT vào đây
EVENT_URL = "https://docs.google.com/spreadsheets/d/1yhBY-zRPlsd350gUEaEakIMmHeDsy7SCoyzONyoTiGM/edit?gid=1566812210#gid=1566812210"

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=300)
def load_history():
    try:
        df = pd.read_csv(HISTORY_URL, skiprows=5)
    except Exception as e:
        st.error(f"Lỗi load HISTORY: {e}")
        return pd.DataFrame()

    # rename cột đầu
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)

    # convert date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # sort
    df = df.sort_values("Date")

    # drop dòng lỗi
    df = df.dropna(subset=["Date"])

    return df


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
        if base != 0:
            df_norm[col] = df[col] / base * 100
    df = df_norm

# =========================
# PLOT
# =========================
fig = go.Figure()

# MULTI AXIS
for i, asset in enumerate(selected_assets):
    axis_name = f"y{i+1}"

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df[asset],
        name=asset,
        yaxis=axis_name
    ))

    # label giá cuối
    if show_last:
        fig.add_trace(go.Scatter(
            x=[df["Date"].iloc[-1]],
            y=[df[asset].iloc[-1]],
            mode="markers+text",
            text=[f"{df[asset].iloc[-1]:,.2f}"],
            textposition="middle right",
            showlegend=False,
            yaxis=axis_name
        ))

    fig.update_layout({
        axis_name: dict(
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

        # event range
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
