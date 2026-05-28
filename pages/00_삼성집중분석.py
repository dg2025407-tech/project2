import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

# 1. 웹페이지 기본 설정 (삼성전자 전용으로 변경)
st.set_page_config(page_title="삼성전자 집중 분석기", layout="wide")
st.title("🔎 삼성전자(005930) 단일 종목 집중 분석 대시보드")
st.markdown("당곡고등학교 경제/정보 융합 학습 - 오직 삼성전자의 주가 흐름, 이동평균선, 거래량에만 집중합니다.")

# 2. 사이드바 설정 (기간 및 차트 색상 설정만 남김)
st.sidebar.header("분석 설정")

chart_style = st.sidebar.radio(
    "1️⃣ 차트 색상 문화를 선택하세요",
    ("🇰🇷 한국식 (상승:빨강 / 하락:파랑)", "🇺🇸 미국식 (상승:초록 / 하락:빨강)")
)

start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 3. 데이터 불러오기 (삼성전자 고정)
@st.cache_data
def load_samsung_data(start, end):
    ticker = "005930.KS"  # 삼성전자 티커 고정
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    return df, stock.info

with st.spinner('삼성전자 데이터를 정밀 분석 중입니다...'):
    df, info = load_samsung_data(start_date, end_date)

if not df.empty:
    # --- 4. 데이터 전처리 (이동평균선 및 심화 지표 계산) ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()

    # 골든/데드 크로스 자동 계산
    golden_cross = (df['MA20'] > df['MA60']) & (df['MA20'].shift(1) <= df['MA60'].shift(1)) & df['MA60'].notna() & df['MA60'].shift(1).notna()
    dead_cross = (df['MA20'] < df['MA60']) & (df['MA20'].shift(1) >= df['MA60'].shift(1)) & df['MA60'].notna() & df['MA60'].shift(1).notna()
    
    # 거래량 폭발 지점 찾기 (평균의 2배)
    avg_volume = df['Volume'].mean()
    volume_spike = df['Volume'] > (avg_volume * 2)

    # --- 5. 삼성전자 핵심 요약 지표 출력 ---
    st.subheader("💡 삼성전자(005930) 요약 지표")
    start_price = df['Close'].iloc[0]
    end_price = df['Close'].iloc[-1]
    total_return = ((end_price / start_price) - 1) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("선택 기간 시작가", f"{int(start_price):,}원")
    col2.metric("현재 종가 (선택 기간 끝)", f"{int(end_price):,}원", f"{total_return:.2f}%")
    
    market_cap = info.get('marketCap', 0)
    if market_cap > 0:
        col3.metric("현재 시가총액", f"{market_cap / 1_000_000_000_000:,.1f}조 원")
    else:
        col3.metric("현재 시가총액", "정보 없음")
    col4.metric("평균 일일 거래량", f"{int(avg_volume):,} 주")

    st.write("---")

    # --- 6. Plotly를 이용한 전문가용 차트 그리기 ---
    st.subheader("📊 삼성전자 인터랙티브 심화 분석 차트")
    
    if "한국식" in chart_style:
        inc_color, dec_color = 'red', 'blue'
    else:
        inc_color, dec_color = 'green', 'red'

    colors = [inc_color if close >= open else dec_color for close, open in zip(df['Close'], df['Open'])]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, 
                        subplot_titles=('주가 및 이동평균선(Price & MA)', '거래량(Volume)'), 
                        row_width=[0.25, 0.75])

    # [1] 캔들차트 추가
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color=inc_color, decreasing_line_color=dec_color,
        name='주가(캔들)'
    ), row=1, col=1)

    # [2] 이동평균선 추가
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name='20일 이동평균'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='purple', width=1.5), name='60일 이동평균'), row=1, col=1)

    # [3] 골든/데드 크로스 마커 추가
    if golden_cross.any():
        fig.add_trace(go.Scatter(
            x=df.index[golden_cross], y=df['MA20'][golden_cross],
            mode='markers', marker=dict(symbol='triangle-up', size=15, color='gold', line=dict(width=2, color='black')),
            name='골든 크로스'
        ), row=1, col=1)
    
    if dead_cross.any():
        fig.add_trace(go.Scatter(
            x=df.index[dead_cross], y=df['MA20'][dead_cross],
            mode='markers', marker=dict(symbol='triangle-down', size=15, color='black', line=dict(width=2, color='white')),
            name='데드 크로스'
        ), row=1, col=1)

    # [4] 거래량 바 차트 추가
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], marker_color=colors, name='거래량'
    ), row=2, col=1)

    # [5] 거래량 폭발 마커 추가
    if volume_spike.any():
        fig.add_trace(go.Scatter(
            x=df.index[volume_spike], y=df['Volume'][volume_spike],
            mode='markers', marker=dict(symbol='star', size=10, color='yellow', line=dict(width=1, color='black')),
            name='거래량 폭발'
        ), row=2, col=1)

    fig.update_layout(
        height=700, xaxis_rangeslider_visible=False, hovermode='x unified', margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 7. 심화 학습 해설 섹션 ---
    st.subheader("📚 데이터에서 배우는 경제 심화 탐구")
    
    with st.expander("1️⃣ 문화권별 차트 색상이 다른 이유는? (클릭)"):
        st.write("""
        * **한국/중국/일본 (동양권):** 전통적으로 **빨간색(Red)** 은 부, 복, 생명력, 양(陽)의 기운 등 '긍정적인' 의미를 담고 있습니다. 그래서 주가가 오를 때 빨간색을 사용합니다.
        * **미국/유럽 (서양권):** 재무제표에서 적자(손실)를 'Red ink(빨간 잉크)'로 표기하는 관습이 있습니다. 반면 **초록색(Green)** 은 달러 지폐의 색깔이자 '통과, 안전'을 의미하여 상승을 초록색으로 표기합니다.
        """)

    with st.expander("2️⃣ 수학으로 찾은 주가 추세: 골든/데드 크로스 (클릭)"):
        st.write("""
        * **골든 크로스(황금색 ▲):** 단기(20일) 평균선이 장기(60일) 평균선을 아래에서 위로 뚫고 올라가는 지점입니다. 강력한 상승 추세의 시작으로 해석하곤 합니다.
        * **데드 크로스(검은색 ▼):** 반대로 단기(20일) 평균선이 장기(60일) 평균선을 위에서 아래로 뚫고 내려가는 지점입니다. 하락 추세로 전환될 가능성이 큽니다.
        """)

    with st.expander("3️⃣ 거래량 폭발(Volume Spike)의 비밀 (클릭)"):
        st.write("""
        * 주식 시장의 격언 중 **"주가는 속여도 거래량은 속이지 못한다"**는 말이 있습니다. 평균 거래량의 2배가 넘는 날(⭐)은 거대한 자본을 움직이는 뉴스나 큰손의 개입이 있었다는 증거입니다.
        """)

else:
    st.error("데이터를 불러오지 못했습니다. 날짜 설정을 확인해 주세요.")
