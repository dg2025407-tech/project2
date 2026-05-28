import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

# 1. 테마별 한/미 주요 주식 중첩 딕셔너리 설정 (과학 분야 추가!)
STOCK_CATEGORIES = {
    "📊 전체(주요종목)": {
        "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "현대차": "005380.KS", "NAVER": "035420.KS",
        "Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Tesla": "TSLA"
    },
    "💻 한미 빅테크": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Alphabet(구글)": "GOOGL", 
        "NAVER": "035420.KS", "카카오": "035720.KS"
    },
    "🚀 반도체 테마": {
        "NVIDIA": "NVDA", "TSMC": "TSM", "AMD": "AMD", 
        "삼성전자": "005930.KS", "SK하이닉스": "000660.KS"
    },
    "🚗 자동차/모빌리티": {
        "Tesla": "TSLA", "현대차": "005380.KS", "기아": "000270.KS", "Ford": "F"
    },
    # --- 새롭게 추가된 과학 분야 테마 ---
    "🧬 바이오/생명과학": {
        "삼성바이오로직스": "207940.KS", 
        "셀트리온": "068270.KS", 
        "Moderna(모더나)": "MRNA", 
        "Pfizer(화이자)": "PFE"
    },
    "🌌 우주항공/과학기술": {
        "한화에어로스페이스": "012450.KS",
        "한국항공우주(KAI)": "047810.KS",
        "Lockheed Martin": "LMT",
        "Boeing(보잉)": "BA"
    }
}

# 2. 웹페이지 기본 설정
st.set_page_config(page_title="한미 융합 주식 분석기", layout="wide")
st.title("📈 한미 주요 주식 분석 웹앱 (과학 테마 포함)")
st.markdown("당곡고등학교 경제/정보/과학 융합 학습을 위한 주식 데이터 분석 웹앱입니다.")

# 3. 사이드바 UI 설정
st.sidebar.header("분석 설정")

selected_category = st.sidebar.selectbox(
    "분석할 테마(분야)를 선택하세요",
    options=list(STOCK_CATEGORIES.keys())
)

# 선택된 테마에 해당하는 주식 딕셔너리만 가져오기
current_stocks_dict = STOCK_CATEGORIES[selected_category]
current_stock_names = list(current_stocks_dict.keys())

default_selection = current_stock_names[:3] if len(current_stock_names) >= 3 else current_stock_names

selected_stocks = st.sidebar.multiselect(
    f"[{selected_category}] 비교할 주식을 선택하세요",
    options=current_stock_names,
    default=default_selection
)

start_date = st.sidebar.date_input("시작일", date.today() - timedelta(days=365))
end_date = st.sidebar.date_input("종료일", date.today())

# 4. 데이터 불러오기 함수
@st.cache_data
def load_data(stock_dict, start, end):
    df_list = []
    for name, ticker in stock_dict.items():
        data = yf.download(ticker, start=start, end=end, progress=False)
        if not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                price_col = 'Adj Close' if 'Adj Close' in data.columns.get_level_values(0) else 'Close'
                series = data[price_col].iloc[:, 0]
            else:
                price_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
                series = data[price_col]
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
            
            series = series.rename(name)
            df_list.append(series)
    
    if df_list:
        return pd.concat(df_list, axis=1)
    return pd.DataFrame()

# 기업 재무 정보 불러오기 함수
@st.cache_data
def load_company_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

# 5. 메인 화면 출력 로직
if selected_stocks:
    tab1, tab2 = st.tabs(["📊 통합 수익률 비교", "🔎 개별 종목 상세 분석"])

    selected_dict = {name: current_stocks_dict[name] for name in selected_stocks}
    
    with st.spinner('데이터를 불러오는 중입니다...'):
        df = load_data(selected_dict, start_date, end_date)

    if not df.empty:
        df.ffill(inplace=True) 
        df.dropna(inplace=True)

        # ====== [탭 1] 통합 수익률 비교 ======
        with tab1:
            df_normalized = (df / df.iloc[0]) * 100

            st.subheader(f"📊 {selected_category} 수익률 추이 비교")
            st.line_chart(df_normalized)

            st.subheader("💰 설정 기간 내 누적 수익률")
            returns = ((df.iloc[-1] / df.iloc[0]) - 1) * 100
            cols = st.columns(len(selected_stocks))
            for i, stock in enumerate(selected_stocks):
                with cols[i]:
                    st.metric(label=stock, value=f"{returns[stock]:.2f}%")
            
            with st.expander("원시 데이터 확인하기"):
                st.dataframe(df)

        # ====== [탭 2] 개별 종목 상세 분석 ======
        with tab2:
            st.subheader("기업 가치 및 차트 상세 분석")
            single_stock = st.selectbox("상세 분석할 종목을 선택하세요", options=selected_stocks)
            
            if single_stock:
                ticker = current_stocks_dict[single_stock]
                
                stock_df = pd.DataFrame(df[single_stock])
                stock_df.columns = ["주가(종가)"]
                stock_df["20일 이동평균선"] = stock_df["주가(종가)"].rolling(window=20).mean()
                
                st.line_chart(stock_df)
                
                st.markdown("#### 🏢 기업 주요 지표")
                info = load_company_info(ticker)
                
                sector = info.get('sector', '정보 없음')
                pe_ratio = info.get('trailingPE', '정보 없음')
                pb_ratio = info.get('priceToBook', '정보 없음')
                dividend = info.get('dividendYield', 0)
                
                if dividend != '정보 없음' and dividend is not None:
                    dividend = f"{dividend * 100:.2f}%"
                else:
                    dividend = "배당 없음"

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("산업군(Sector)", sector)
                col2.metric("PER (주가수익비율)", pe_ratio if isinstance(pe_ratio, str) else f"{pe_ratio:.2f}")
                col3.metric("PBR (주가순자산비율)", pb_ratio if isinstance(pb_ratio, str) else f"{pb_ratio:.2f}")
                col4.metric("배당수익률", dividend)

    else:
        st.error("데이터를 불러오지 못했습니다. 날짜나 인터넷 연결을 확인해 주세요.")
else:
    st.info("👈 왼쪽 사이드바에서 비교할 주식을 하나 이상 선택해 주세요.")
