import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- 頁面基本設定 ---
st.set_page_config(page_title="AI 存股戰情室", layout="wide", page_icon="🏦")

# 設定圖表風格
plt.style.use('seaborn-v0_8')
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

st.title("🏦 AI 存股戰情室 (6合1 旗艦版)")
st.markdown("---")

# --- 共用函數 ---
def get_stock_data(sid):
    """取得股票基本資料與股息"""
    try:
        stock = yf.Ticker(sid)
        hist = stock.history(period="1d")
        if hist.empty: return None
        
        # 強制轉為純浮點數，避開 TypeError
        price = float(hist['Close'].iloc[-1])
        
        # 股利計算
        div = stock.dividends.resample('YE').sum()
        if len(div) >= 5:
            avg_div = div.iloc[-6:-1].mean()
        elif len(div) > 0:
            avg_div = div.mean()
        else:
            avg_div = 0
            
        return {"price": price, "avg_div": float(avg_div), "stock": stock}
    except:
        return None

# --- 分頁導航 ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🥊 個股PK", "🏆 排行榜", "🐢 退休目標", 
    "🍰 資產配置", "🌡️ 溫度計", "♟️ 智能進場(雙軌)"
])

# ==========================================
# Tab 1: 跨界 PK
# ==========================================
with tab1:
    st.header("🥊 個股超級比一比")
    col1, col2 = st.columns([2, 1])
    with col1:
        pk_input = st.text_input("輸入股票代號 (用逗號隔開)", '2886.TW, 2412.TW, 2330.TW')
    with col2:
        st.write("") 
        st.write("") 
        start_pk = st.button("開始 PK", use_container_width=True)

    if start_pk:
        stock_ids = [s.strip() for s in pk_input.split(',')]
        data = []
        with st.spinner('分析中...'):
            for sid in stock_ids:
                res = get_stock_data(sid)
                if res:
                    try:
                        info = res['stock'].info
                        roe = info.get('returnOnEquity', 0)
                        if roe is None: roe = 0
                    except: roe = 0
                    
                    data.append({
                        "代號": sid,
                        "股價": round(res['price'], 2),
                        "殖利率(%)": round((res['avg_div']/res['price'])*100, 2),
                        "ROE(%)": round(roe*100, 2)
                    })
        
        if data:
            df = pd.DataFrame(data).set_index("代號")
            st.dataframe(df.style.highlight_max(axis=0, color='lightgreen', subset=['殖利率(%)', 'ROE(%)']), use_container_width=True)
            
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            df['殖利率(%)'].plot(kind='bar', ax=ax[0], color='skyblue', title='Dividend Yield %')
            df['ROE(%)'].plot(kind='bar', ax=ax[1], color='orange', title='ROE %')
            st.pyplot(fig)

# ==========================================
# Tab 2: 排行榜
# ==========================================
with tab2:
    st.header("🏆 金融 vs ETF 大亂鬥")
    rank_input = st.text_input("新增比較代號 (預設已含5大金融)", '00878.TW, 0056.TW, 00919.TW')
    if st.button("更新排行榜"):
        default = ["2881.TW", "2886.TW", "2891.TW", "2892.TW", "5880.TW"]
        extras = [s.strip() for s in rank_input.split(',')]
        full_list = list(set(default + extras))
        
        results = []
        progress_bar = st.progress(0)
        
        for i, sid in enumerate(full_list):
            if not sid: continue
            res = get_stock_data(sid)
            if res:
                yield_rate = res['avg_div'] / res['price'] if res['price'] > 0 else 0
                results.append({
                    "代號": sid,
                    "股價": round(res['price'], 2),
                    "殖利率": f"{yield_rate:.2%}",
                    "Sort": yield_rate
                })
            progress_bar.progress((i + 1) / len(full_list))
            
        df = pd.DataFrame(results).sort_values("Sort", ascending=False).drop(columns="Sort")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

# ==========================================
# Tab 3: 退休目標
# ==========================================
with tab3:
    st.header("🐢 退休目標計算機")
    c1, c2, c3 = st.columns(3)
    with c1: r_stock = st.text_input("存股代號", "0056.TW", key="retire_stock")
    with c2: r_goal = st.number_input("目標月領 (千元)", value=20, step=5)
    with c3: r_save = st.number_input("每月能存 (千元)", value=15, step=5)
        
    if st.button("計算退休藍圖"):
        res = get_stock_data(r_stock)
        if res:
            yield_rate = res['avg_div'] / res['price']
            if yield_rate == 0:
                st.error("此股票無配息紀錄，無法計算。")
            else:
                target_capital = (r_goal * 1000 * 12) / yield_rate
                assets = 0
                years = 0
                history = []
                while assets < target_capital:
                    years += 1
                    assets += (r_save * 1000 * 12)
                    assets += assets * yield_rate
                    history.append(assets)
                    if years > 60: break
                
                st.success(f"🎯 預計 {years} 年後達成財務自由！")
                st.metric("目標本金", f"{int(target_capital):,} 元", f"殖利率 {yield_rate:.2%}")
                
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.plot(range(1, years+1), history, marker='o')
                ax.axhline(y=target_capital, color='r', linestyle='--', label='Target')
                ax.set_title("Asset Growth Curve")
                st.pyplot(fig)

# ==========================================
# Tab 4: 資產配置
# ==========================================
with tab4:
    st.header("🍰 資產配置模擬器")
    c1, c2 = st.columns(2)
    with c1: qty = st.number_input("現有金融股 (張)", value=100)
    with c2: cash = st.number_input("新投入資金 (萬)", value=100)
        
    if st.button("模擬配置結果"):
        curr_val = qty * 1000 * 40 
        new_val = cash * 10000
        labels = ['Financials (Old)', 'ETF/Growth (New)']
        sizes = [curr_val, new_val]
        
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#ff9999','#66b3ff'], startangle=90)
        st.pyplot(fig)
# ==========================================
# Tab 5: 溫度計 (雙圖表終極版)
# ==========================================
with tab5:
    st.header("🌡️ 台股大盤溫度計 (雙鏡頭)")
    st.markdown("上圖：**大盤走勢與年線** (看趨勢) | 下圖：**乖離率溫度計** (看買賣點)")
    
    if st.button("啟動雙鏡頭分析"):
        with st.spinner("資料讀取與繪圖中..."):
            try:
                # 1. 下載數據
                df = yf.download("^TWII", period="5y")
                
                # 2. 資料清洗 (確保抓到單一數列)
                if isinstance(df.columns, pd.MultiIndex):
                    try: data = df['Close']
                    except: data = df.iloc[:, 0]
                else:
                    data = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]

                if isinstance(data, pd.DataFrame):
                    data = data.iloc[:, 0]
                
                # 3. 計算數據
                ma200 = data.rolling(200).mean()
                bias = ((data - ma200) / ma200) * 100
                
                # 取得最新數值
                current_price = float(data.iloc[-1])
                curr_bias = float(bias.iloc[-1])
                curr_ma = float(ma200.iloc[-1])
                
                # 4. 顯示儀表板數據
                c1, c2, c3 = st.columns(3)
                c1.metric("加權指數", f"{int(current_price):,}")
                c2.metric("200日年線", f"{int(curr_ma):,}")
                c3.metric("乖離率", f"{curr_bias:.2f}%")
                
                # 判斷燈號
                if curr_bias > 15: st.warning("🔴 警告：過熱 (Overheated) - 小心回檔")
                elif curr_bias < 0: st.success("🟢 機會：便宜 (Oversold) - 黃金買點")
                else: st.info("🟡 狀態：合理 (Fair) - 順勢操作")
                
                # 5. 繪製雙層圖表 (重點修改)
                # sharex=True 代表上下兩張圖共用時間軸，拖動一個另一個也會動
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
                
                # 準備繪圖數據 (壓扁成 1D)
                dates = data.index
                price_values = data.values.flatten()
                ma_values = ma200.values.flatten()
                bias_values = bias.values.flatten()
                
                # --- 上圖：股價走勢 ---
                ax1.plot(dates, price_values, label='TAIEX Index', color='#1f77b4', linewidth=1.5)
                ax1.plot(dates, ma_values, label='200 MA (Yearly)', color='orange', linestyle='--', linewidth=1.2)
                ax1.set_title("台股走勢 vs 年線", fontsize=12)
                ax1.legend(loc='upper left')
                ax1.grid(True, linestyle=':', alpha=0.6)
                
                # --- 下圖：乖離率溫度計 ---
                ax2.plot(dates, bias_values, color='gray', linewidth=1, label='Bias %')
                ax2.fill_between(dates, bias_values, 15, where=(bias_values>15), color='red', alpha=0.5, label='Overheated')
                ax2.fill_between(dates, bias_values, 0, where=(bias_values<0), color='green', alpha=0.5, label='Oversold')
                ax2.axhline(0, color='black', linestyle='-', linewidth=1) # 0軸實線
                ax2.axhline(15, color='red', linestyle=':', alpha=0.5)    # 過熱線
                ax2.set_title("乖離率 (溫度計)", fontsize=12)
                ax2.grid(True, linestyle=':', alpha=0.6)
                
                plt.tight_layout()
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")
# ==========================================
# Tab 6: 智能進場策略 (雙軌制 - 升級版)
# ==========================================
with tab6:
    st.header("♟️ 智能進場策略表 (雙軌制)")
    st.markdown("將資金分為 **「主力部隊 (定期定額)」** 與 **「游擊部隊 (保留現金)」**，並依據乖離率動態調整。")
    
    c1, c2, c3 = st.columns(3)
    with c1: s_capital = st.number_input("總投入金額 (萬元)", value=12, step=1)
    with c2: s_stock = st.text_input("買進代號", "0056.TW", key="strat_stock")
    with c3: s_months = st.slider("預計佈局時間 (月)", 1, 24, 12)

    if st.button("生成戰略計畫書"):
        try:
            with st.spinner(f"分析 {s_stock} 位階中..."):
                stock = yf.Ticker(s_stock)
                hist = stock.history(period="1y")
                
                if hist.empty:
                    st.error("無法取得資料，請確認代號正確。")
                else:
                    # --- 關鍵修正：強制轉為 float ---
                    current_price = float(hist['Close'].iloc[-1])
                    ma200_raw = hist['Close'].rolling(200).mean().iloc[-1]
                    
                    if pd.isna(ma200_raw):
                        ma200 = float(hist['Close'].rolling(60).mean().iloc[-1])
                        ma_name = "60MA"
                    else:
                        ma200 = float(ma200_raw)
                        ma_name = "200MA"
                    
                    bias = ((current_price - ma200) / ma200) * 100
                    # ------------------------------
                    
                    # 邏輯：依乖離率決定保留現金比例
                    if bias > 15:
                        reserve_ratio = 0.4
                        bias_status = "🔴 過熱警戒"
                    elif bias > 5:
                        reserve_ratio = 0.3
                        bias_status = "🟡 股價偏強"
                    elif bias > 0:
                        reserve_ratio = 0.2
                        bias_status = "🟢 合理區間"
                    else:
                        reserve_ratio = 0.1
                        bias_status = "🔵 超跌黃金坑"

                    total_cap = s_capital * 10000
                    reserve_cash = total_cap * reserve_ratio
                    dca_cash = total_cap - reserve_cash
                    monthly_amt = dca_cash // s_months

                    # 顯示儀表板
                    st.markdown("### 📊 市場診斷與資金分配")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("目前乖離率", f"{bias:.2f}%", f"{bias_status}")
                    m2.metric("主力部隊 (定期定額)", f"{int(dca_cash):,} 元", f"每月 {int(monthly_amt):,} 元")
                    m3.metric("游擊部隊 (保留現金)", f"{int(reserve_cash):,} 元", f"佔比 {int(reserve_ratio*100)}%")
                    st.divider()

                    # 顯示兩張表
                    col_t1, col_t2 = st.columns([1.2, 1])
                    
                    with col_t1:
                        st.subheader("🗓️ 主力部隊時程")
                        schedule = []
                        today = datetime.now()
                        for i in range(s_months):
                            date = today + timedelta(days=30*i)
                            schedule.append({
                                "扣款月份": date.strftime("%Y-%m"),
                                "投入金額": f"${int(monthly_amt):,}",
                                "執行動作": "紀律買進"
                            })
                        st.dataframe(pd.DataFrame(schedule), use_container_width=True)

                    with col_t2:
                        st.subheader("⚡ 游擊部隊訊號")
                        st.info("保留現金放在活存，見訊號單筆投入。")
                        price_green = ma200
                        price_oversold = ma200 * 0.9
                        
                        sig_data = [
                            {"訊號": "🟢 回測年線", "價格約": f"{price_green:.2f}", "動作": f"投入 ${int(reserve_cash*0.5):,}"},
                            {"訊號": "🔵 跌破年線", "價格約": f"{price_oversold:.2f}", "動作": f"投入 ${int(reserve_cash*0.5):,}"}
                        ]
                        st.table(pd.DataFrame(sig_data))
                        
        except Exception as e:
            st.error(f"發生錯誤：{e}")

