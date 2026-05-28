import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

# 1. 비교할 한/미 주요 주식 딕셔너리 설정 (이름: 티커)
# 탐구 과제: 여기에 학생 본인이 관심 있는 다른 주식의 티커를 추가해 보세요!
STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Tesla": "TSLA"
}

# 2. 웹페이지 기본 설정
st.set_page_config(page_title="한미 주식 수익률 비교기", layout="wide")
st.title("📈 한국 vs 미국 주요 주식 수익률 비교기")
st.markdown("당곡고등학교 프로그래밍/경제 학습을 위한 주식 데이터 분석 웹앱입니다.")

# 3. 사이드바 UI 설정 (사용자 입력 필드)
st.sidebar.header("분석 설정")

# 여러 주식을 선택할 수 있는 멀티셀렉트 박스
selected_stocks = st.sidebar.multiselect(
    "비교할 주식을 선택하세요",
    options=list(STOCKS.keys()),
    default=["삼성전자", "Apple", "NVIDIA"]
)

# 분석 기간 설정 (기본값: 최근 1년)
start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 4. 데이터 불러오기 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def load_data(stock_dict, start, end):
    df_list = []
    for name, ticker in stock_dict.items():
        # yfinance를 통해 데이터 다운로드
        data = yf.download(ticker, start=start, end=end, progress=False)
        if not data.empty:
            # 보통 분석에는 수정종가(Adj Close)를 사용하지만, 없을 경우 종가(Close) 사용
            price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            # 시리즈 이름을 주식 이름으로 변경하여 리스트에 추가
            series = data[price_col].rename(name)
            df_list.append(series)
    
    # 리스트에 모인 데이터를 하나의 데이터프레임으로 합침
    if df_list:
        return pd.concat(df_list, axis=1)
    return pd.DataFrame()

# 5. 메인 화면 출력 로직
if selected_stocks:
    # 선택된 주식들의 티커만 모아서 딕셔너리로 만듦
    selected_dict = {name: STOCKS[name] for name in selected_stocks}
    
    with st.spinner('데이터를 불러오는 중입니다...'):
        df = load_data(selected_dict, start_date, end_date)

    if not df.empty:
        # 결측치(휴장일 등) 전처리
        df.ffill(inplace=True)  # 앞의 값으로 채우기
        df.dropna(inplace=True)

        # 시작일을 기준(100)으로 환산한 정규화 데이터 생성 (수익률 비교를 위해)
        df_normalized = (df / df.iloc[0]) * 100

        # --- 차트 그리기 ---
        st.subheader(f"📊 수익률 추이 비교 (시작일 기준 = 100)")
        st.markdown("시작일의 주가를 100으로 맞추어 각 주식의 상대적인 상승/하락 폭을 비교합니다.")
        st.line_chart(df_normalized)

        # --- 누적 수익률 계산 및 표시 ---
        st.subheader("💰 설정 기간 내 누적 수익률")
        # 수익률 공식: (마지막 날 주가 / 첫 날 주가 - 1) * 100
        returns = ((df.iloc[-1] / df.iloc[0]) - 1) * 100
        
        # 선택한 주식 수에 맞춰 컬럼을 나누어 깔끔하게 표시
        cols = st.columns(len(selected_stocks))
        for i, stock in enumerate(selected_stocks):
            with cols[i]:
                # Streamlit의 metric 위젯을 사용하여 수치 시각화
                st.metric(label=stock, value=f"{returns[stock]:.2f}%")
        
        # --- 원본 데이터 테이블 표시 ---
        st.write("---")
        with st.expander("원시 데이터 확인하기 (클릭하여 펼치기)"):
            st.dataframe(df)
    else:
        st.error("데이터를 불러오지 못했습니다. 날짜나 인터넷 연결을 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 비교할 주식을 하나 이상 선택해 주세요.")
