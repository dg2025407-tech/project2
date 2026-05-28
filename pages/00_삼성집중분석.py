import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="삼성전자 집중 분석기", layout="wide")
st.title("🔎 삼성전자(005930) 집중 분석 대시보드")
st.markdown("당곡고등학교 경제/정보 융합 학습 - 캔들차트와 거래량을 활용한 미시적 주가 분석")

# 2. 사이드바 설정 (기간 설정)
st.sidebar.header("분석 기간 설정")
start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 3. 데이터 불러오기 (단일 종목 집중 분석용)
@st.cache_data
def load_samsung_data(start, end):
    ticker = "005930.KS"  # 삼성전자 티커
    # 단일 종목 집중 분석일 때는 .history()를 사용하면 시가, 고가, 저가, 종가, 거래량을 깔끔하게 가져옵니다.
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    return df, stock.info

with st.spinner('삼성전자 데이터를 정밀 분석 중입니다...'):
    df, info = load_samsung_data(start_date, end_date)

if not df.empty:
    # --- 4. 데이터 전처리 (이동평균선 계산) ---
    # 20일선(한 달 흐름), 60일선(세 달 흐름) 추가
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()

    # --- 5. 꼼꼼한 수익률 및 요약 정보 출력 ---
    st.subheader("💡 요약 지표")
    
    # 수익률 계산
    start_price = df['Close'].iloc[0]
    end_price = df['Close'].iloc[-1]
    total_return = ((end_price / start_price) - 1) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("선택 기간 시작가", f"{int(start_price):,}원")
    col2.metric("선택 기간 종가", f"{int(end_price):,}원", f"{total_return:.2f}%")
    
    # yfinance에서 제공하는 실시간/재무 정보 (없을 경우 예외 처리)
    market_cap = info.get('marketCap', 0)
    if market_cap > 0:
        # 시가총액을 조(兆) 단위로 변환하여 표시
        market_cap_jo = market_cap / 1_000_000_000_000
        col3.metric("시가총액", f"{market_cap_jo:,.1f}조 원")
    else:
        col3.metric("시가총액", "정보 없음")
        
    col4.metric("PER (주가수익비율)", info.get('trailingPE', '정보 없음'))

    st.write("---")

    # --- 6. Plotly를 이용한 전문가용 차트 그리기 ---
    st.subheader("📊 캔들차트 및 거래량 정밀 분석")
    st.markdown("한국 주식 시장의 전통적인 색상(상승=빨강, 하락=파랑)을 적용했습니다. 마우스를 올려 가격을 확인해 보세요.")

    # 그래프 영역을 2개로 나눔 (위: 주가 차트, 아래: 거래량 차트)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, 
                        subplot_titles=('주가 및 이동평균선(Price & MA)', '거래량(Volume)'), 
                        row_width=[0.25, 0.75]) # 위쪽 차트가 더 크게

    # 한국식 색상 설정 함수 (시가보다 종가가 높으면 붉은색, 낮으면 푸른색)
    # df.iterrows() 대신 벡터 연산을 사용하여 빠르고 간결하게 처리
    colors = ['red' if close >= open else 'blue' for close, open in zip(df['Close'], df['Open'])]

    # [1] 캔들차트 추가 (위쪽)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='red', decreasing_line_color='blue', # 한국식 색상 적용
        name='주가(캔들)'
    ), row=1, col=1)

    # [2] 이동평균선 추가 (위쪽)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1.5), name='20일 이동평균'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='green', width=1.5), name='60일 이동평균'), row=1, col=1)

    # [3] 거래량 바 차트 추가 (아래쪽)
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], marker_color=colors, name='거래량'
    ), row=2, col=1)

    # 레이아웃(디자인) 설정
    fig.update_layout(
        height=700, 
        xaxis_rangeslider_visible=False, # 캔들차트 기본 슬라이더 숨김 (화면을 깔끔하게)
        hovermode='x unified',           # 마우스를 올렸을 때 모든 정보를 한 번에 표시
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # 스트림릿에 차트 띄우기
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📝 캔들차트(봉차트) 보는 법 알아보기 (클릭)"):
        st.info("""
        * **양봉(빨간색):** 주식이 시작할 때(시가)보다 끝날 때(종가) **가격이 올랐음**을 의미합니다. 
        * **음봉(파란색):** 주식이 시작할 때보다 끝날 때 **가격이 내렸음**을 의미합니다. (미국은 반대로 초록색이 상승, 빨간색이 하락을 의미합니다!)
        * **위꼬리와 아래꼬리:** 하루 동안 주가가 가장 높았던 가격(고가)과 가장 낮았던 가격(저가)의 흔적을 보여줍니다.
        """)

else:
    st.error("데이터를 불러오지 못했습니다. 날짜 설정을 확인해 주세요.")
