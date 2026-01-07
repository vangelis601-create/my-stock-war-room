# ==========================================
# Tab 5: 溫度計
# ==========================================
with tab5:
    st.header("🌡️ 台股大盤溫度計")
    if st.button("測量現在溫度"):
        with st.spinner("測量中..."):
            try:
                # 1. 下載數據
                df = yf.download("^TWII", period="5y")
                
                # 2. 資料清洗 (關鍵修復步驟)
                # 如果是 MultiIndex (多層索引)，嘗試只取 Close
                if isinstance(df.columns, pd.MultiIndex):
                    # 嘗試取 'Close'，如果失敗則取第一欄
                    try:
                        data = df['Close']
                    except:
                        data = df.iloc[:, 0] 
                else:
                    # 如果不是多層索引，直接取 Close 或第一欄
                    data = df['Close'] if 'Close' in df.columns else df.iloc[:, 0]

                # 雙重保險：如果 data 還是 DataFrame (表格)，強制轉為 Series (數列)
                if isinstance(data, pd.DataFrame):
                    data = data.iloc[:, 0]
                
                # 3. 計算乖離率
                ma200 = data.rolling(200).mean()
                bias = ((data - ma200) / ma200) * 100
                
                # 取得最新數值 (轉為純數字 float)
                current_index = float(data.iloc[-1])
                curr_bias = float(bias.iloc[-1])
                
                # 4. 顯示儀表板數字
                col1, col2 = st.columns(2)
                with col1: st.metric("目前大盤指數", f"{int(current_index):,}")
                with col2: st.metric("乖離率 (Bias)", f"{curr_bias:.2f}%")
                
                if curr_bias > 15: st.warning("🔴 過熱 (Overheated) - 建議分批慢買")
                elif curr_bias < 0: st.success("🟢 便宜 (Oversold) - 黃金買點")
                else: st.info("🟡 合理 (Fair) - 定期定額")
                
                # 5. 畫圖 (關鍵修復：轉為 numpy array 確保是一維)
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # 將 Series 的索引(日期)和數值(乖離率)分開提取，並確保是 1D
                dates = bias.index
                bias_values = bias.values.flatten() # <--- 這裡強制壓扁成一維陣列
                
                ax.plot(dates, bias_values, color='gray', label='Bias', linewidth=1)
                
                # fill_between 現在接收的是純一維陣列，不會再報錯
                ax.fill_between(dates, bias_values, 15, where=(bias_values>15), color='red', alpha=0.5)
                ax.fill_between(dates, bias_values, 0, where=(bias_values<0), color='green', alpha=0.5)
                
                ax.axhline(0, color='black', linestyle='--')
                ax.set_title("Market Bias History (5 Years)")
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"發生錯誤：{e}")
                # 顯示更詳細的錯誤以便除錯 (選用)
                # st.write(e)
