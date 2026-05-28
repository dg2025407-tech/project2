import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

# 1. 비교할 한/미 주요 주식 딕셔너리 설정 (이름: 티커)
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

selected_stocks = st.sidebar.multiselect(
    "비교할 주식을 선택하세요",
    options=list(STOCKS.keys()),
    default=["삼성전자", "Apple", "NVIDIA"]
)

start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 4. 데이터 불러오기 함수 (yfinance 업데이트 오류 해결 반영)
@st.cache_data
def load_data(stock_dict, start, end):
    df_list = []
    for name, ticker in stock_dict.items():
        # yfinance를 통해 데이터 다운로드
        data = yf.download(ticker, start=start, end=end, progress=False)
        
        if not data.empty:
            # yfinance 최신 버전의 MultiIndex 구조 대응
            # 첫 번째 레벨의 컬럼 이름에서 'Adj Close'나 'Close'를 찾습니다.
            if isinstance(data.columns, pd.MultiIndex):
                price_col = 'Adj Close' if 'Adj Close' in data.columns.get_level_values(0) else 'Close'
                # 2차원 DataFrame이므로 첫 번째 열만 추출하여 1차원 Series로 변환
                series = data[price_col].iloc[:, 0]
            else:
                price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                series = data[price_col]
                # Series가 아닌 DataFrame으로 반환될 경우를 대비한 안전장치
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
            
            # 이제 완벽한 1차원 데이터이므로 이름 변경(rename)이 정상 작동합니다.
            series = series.rename(name)
            df_list.append(series)
    
    # 리스트에 모인 데이터를 하나의 데이터프레임으로 합침
    if df_list:
        return pd.concat(df_list, axis=1)
    return pd.DataFrame()

# 5. 메인 화면 출력 로직
if selected_stocks:
    selected_dict = {name: STOCKS[name] for name in selected_stocks}
    
    with st.spinner('데이터를 불러오는 중입니다...'):
        df = load_data(selected_dict, start_date, end_date)

    if not df.empty:
        # 결측치 전처리
        df.ffill(inplace=True) 
        df.dropna(inplace=True)

        # 시작일을 기준(100)으로 환산한 정규화 데이터 생성
        df_normalized = (df / df.iloc[0]) * 100

        # --- 차트 그리기 ---
        st.subheader(f"📊 수익률 추이 비교 (시작일 기준 = 100)")
        st.markdown("시작일의 주가를 100으로 맞추어 각 주식의 상대적인 상승/하락 폭을 비교합니다.")
        st.line_chart(df_normalized)

        # --- 누적 수익률 계산 및 표시 ---
        st.subheader("💰 설정 기간 내 누적 수익률")
        returns = ((df.iloc[-1] / df.iloc[0]) - 1) * 100
        
        cols = st.columns(len(selected_stocks))
        for i, stock in enumerate(selected_stocks):
            with cols[i]:
                st.metric(label=stock, value=f"{returns[stock]:.2f}%")
        
        # --- 원본 데이터 테이블 표시 ---
        st.write("---")
        with st.expander("원시 데이터 확인하기 (클릭하여 펼치기)"):
            st.dataframe(df)
    else:
        st.error("데이터를 불러오지 못했습니다. 날짜나 인터넷 연결을 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 비교할 주식을 하나 이상 선택해 주세요.")
