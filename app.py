import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 頁面與基本設定
# ==========================================
st.set_page_config(page_title="咒語魔法書 Prompt Guidebook", page_icon="✨", layout="wide")
st.title("✨ 咒語魔法書 Prompt Guidebook")
st.markdown("將模糊的自然語言，一鍵轉譯為高精準度、無雜訊、具備結構化防呆機制的AI指令提示詞。")

# ==========================================
# 2. 側邊欄：API Key 設定與【菁英模型雷達】
# ==========================================
with st.sidebar:
    st.header("⚙️ 魔法書後端設定")
    # 💡 趣味文案：將 API Key 包裝成魔力來源
    api_key = st.text_input("🔑 輸入你的魔力來源 (Google Gemini API Key)", type="password")
    st.markdown("[取得免費 API Key (Google AI Studio)](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.subheader("📡 模型雷達 (Model Radar)")
    
    MODEL_RADAR = {
        "Gemini 2.5 Flash 🥇 推薦：最新極速運算、邏輯編譯首選": "models/gemini-2.5-flash",
        "Gemini 2.0 Flash (經典穩定版)：高性價比、穩健輸出": "models/gemini-2.0-flash",
        "Gemini 2.0 Flash-Lite (極速版)：最低延遲反應": "models/gemini-2.0-flash-lite",
        "Gemini Flash Latest (最新滾動版)：動態更新端點": "models/gemini-flash-latest"
    }
    
    model_choice_label = st.selectbox("選擇 AI 施法引擎", options=list(MODEL_RADAR.keys()), index=0)
    actual_model_name = MODEL_RADAR[model_choice_label]

# ==========================================
# 3. 核心大腦：Meta-Prompt (系統指令)
# ==========================================
META_PROMPT = """
# Role & Persona (角色與人設)
你是《咒語魔法書 Prompt Guidebook》的核心編譯引擎。你是一個「雙面人格」的頂尖提示詞大師：
1. 【火烤大師】：精準吐槽原始提示詞的缺陷與可能導致的 AI 災難（絕對禁止人身攻擊）。
2. 【特教老師】：吐槽完後，用白話文解釋「為什麼這樣改會更好」，並給予實用的觀念指導。

# 🧠 Dynamic Visual Judgment (動態視覺判定雙層網) - ⚠️ 極度重要
仔細分析使用者傳入的【使用者期望的視覺呈現】與【原始需求】：
- 第一層攔截：若使用者明確指定了「表格」或「流程圖/心智圖」，你必須在優化後的 `Output_Format` 中，嚴格規定 AI 必須產出該格式。若指定為圖表，強制要求 AI 產出「複雜、高細節且具備專業設計感的 Mermaid 視覺圖表」。你必須在提示詞中對 AI 下達以下 5 個鐵血規定：
  1. 必須使用多樣化的節點形狀（例如：菱形代表判斷、圓角矩形代表行動）。
  2. 必須在箭頭連接線上加上說明文字（例如：-->|是/否|）。
  3. 絕對要使用 `style` 或 `classDef` 語法為節點塗上專業的色彩（如專業商務藍、莫蘭迪色系背景），禁止全白底色。
  4. 程式碼開頭必須嚴格標示為 ```mermaid （絕對禁止寫成 ```graph 或純文字）。
  5. 【防呆死線】：嚴格規定 AI「必須直接輸出純 Markdown 文本與 Mermaid 區塊，絕對禁止將結果包裝成 JSON 格式」。
- 第二層攔截：若使用者選擇「純文字」，但你判定該任務（如 SOP、策略企劃、時間排程）高度適合視覺化，你必須【主動】在 `Output_Format` 中加入上述的高階 Mermaid 產圖指令，並在診斷報告中由「特教老師」向使用者說明：「針對這類任務，我已經主動幫你加入了圖表產出指令，效果會更好喔！」

# Constraints & Rules (絕對邊界與規則)
必須嚴格遵循【七大核心 + 兩項動態彈性】的次世代提示詞結構來重組優化版本的指令。

# Output Format (強制 JSON 輸出格式)
請嚴格依照以下 JSON Schema 輸出，不要輸出任何 Markdown 標記，只要純 JSON 字串：
{
  "optimized_prompt": {
    "Role": "...", "Context": "...", "Task": "...", "Success_Criteria": "...", 
    "Output_Format": "具體格式要求（此處為控制視覺圖表產出的核心，請注入鐵血規定）", "Constraints": "...", "Tone": "...", 
    "Examples": "...", "Steps": "..."
  },
  "diagnostics": [{"roast": "...", "guide": "..."}],
  "scorecard": {"score": 60, "evaluation": "..."},
  "summary": "...",
  "markdown_export": "..."
}
"""

# ==========================================
# 4. 主畫面：💡 快速靈感庫 (懶人無腦版)
# ==========================================
st.markdown("### 💡 快速靈感模板 (懶人無腦版)")
st.markdown("不想努力了？點擊下方按鈕，直接套用草稿並修改括號內容：")

if "draft_text" not in st.session_state:
    st.session_state.draft_text = ""

def set_template(template_str):
    st.session_state.draft_text = template_str

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🤝 商務溝通", use_container_width=True): 
        set_template("我要寫一封信給 [填入:客戶/老闆名稱]，告知他們 [填入:專案延遲/預算追加] 的情況，請幫我加上合理的解釋與補救措施，語氣要委婉但專業。")
with col2:
    if st.button("📢 社群行銷", use_container_width=True): 
        set_template("幫我寫一篇關於 [填入:產品/活動名稱] 的 [填入:IG/FB] 貼文，目標客群是 [填入:年輕上班族/學生]，風格要幽默活潑，並包含行動呼籲。")
with col3:
    if st.button("💻 程式除錯", use_container_width=True): 
        set_template("我正在用 [填入:Python/JavaScript] 開發，但這段程式碼一直報錯 [填入:錯誤訊息]。請幫我找出根本原因，並提供修改後的完整程式碼。")
with col4:
    if st.button("🧠 企劃發想", use_container_width=True): 
        set_template("我是 [填入:行銷/專案經理]，請幫我發想 3 個關於 [填入:節慶行銷/新功能推廣] 的創新提案，需包含目標、執行步驟與預期效益。")

# ==========================================
# 5. 主畫面：使用者輸入區與【讀心按鈕】
# ==========================================
st.subheader("📝 自行輸入指令 (新手上路版)")
original_prompt = st.text_area(
    "請盡情傾吐你的需求（就算是結巴的白話文也行），魔法書會自動幫你轉譯：",
    height=150, 
    placeholder="例如：我來不及交報告，幫我寫一封文情並茂的信。",
    key="draft_text" 
)

visual_choice = st.radio(
    "🎯 期望的最終視覺呈現",
    options=[
        "📝 結構化提示詞版型 (預設)",
        "📊 簡易 結構化表格 (適合對照比較、數據)",
        "🗺️ 簡易 流程圖/心智圖 (Mermaid 視覺圖表)"
    ],
    horizontal=True
)

# ==========================================
# 6. 編譯引擎執行邏輯
# ==========================================
# 💡 趣味文案：增加詠唱的儀式感
if st.button("✨ 施咒轉譯！一鍵編譯與優化", type="primary"):
    if not api_key:
        st.error("請先在左側邊欄輸入 API Key（注入魔力）！")
    elif not original_prompt:
        st.warning("請輸入你的原始指令！")
    else:
        if 'execution_result' in st.session_state:
            del st.session_state['execution_result']
            
        combined_prompt = f"【使用者原始需求】\n{original_prompt}\n\n【使用者期望的視覺呈現】\n{visual_choice}"
            
        display_engine_name = model_choice_label.split('🥇')[0].split('(')[0].strip()
        with st.spinner(f"魔法書正在施咒轉譯中（使用引擎：{display_engine_name}），請稍候..."):
            try:
                genai.configure(api_key=api_key)
                generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
                model = genai.GenerativeModel(model_name=actual_model_name, system_instruction=META_PROMPT, generation_config=generation_config)
                
                response = model.generate_content(combined_prompt)
                
                raw_text = response.text.strip()
                start_idx, end_idx = raw_text.find('{'), raw_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = raw_text[start_idx:end_idx+1]
                else:
                    raise ValueError("JSON_ERROR")

                st.session_state['compiled_result'] = json.loads(clean_json_str)
                st.success("✨ 咒語編譯完成！請查看下方各頁籤的報告。")
                st.balloons()
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg: st.error("🛑 當日魔力額度已用盡！請明天再來，或更換 API Key。")
                elif "429" in error_msg: st.warning("⏳ 詠唱太快囉！Google API 每分鐘限 15 次，請稍等 1 分鐘。")
                elif "404" in error_msg: st.error("🚫 施法引擎暫不可用！請從左側選單切換另一個模型再試。")
                elif "503" in error_msg: st.warning("🐌 魔力網絡塞車中！請稍候片刻再試。")
                elif "api_key" in error_msg or "400" in error_msg: st.error("🔑 API Key 無效！請檢查魔力來源輸入是否正確。")
                elif "json_error" in error_msg or "expecting value" in error_msg: st.error("🧩 咒語迴路異常！模型這次太有創意了，請直接再點擊一次按鈕重試。")
                else: st.error(f"⚠️ 發生未知錯誤：{str(e)}")

# ==========================================
# 7. UI 頁籤渲染 (包含一鍵試跑)
# ==========================================
if 'compiled_result' in st.session_state:
    result_data = st.session_state['compiled_result']
    
    # 💡 趣味文案：頁籤全面魔法化
    tabs = st.tabs(["✨ 究極咒語 (優化後)", "🧪 天使與惡魔的低語", "📊 戰鬥力分數卡", "📝 施法日誌", "📦 打包帶走", "🚀 真實召喚結果"])

    with tabs[0]:
        st.markdown("### 結構化拆解")
        opt_data = result_data.get("optimized_prompt", {})
        key_mapping = {"Role": "角色與人設", "Context": "背景脈絡", "Task": "核心任務", "Success_Criteria": "驗收標準", "Output_Format": "輸出格式", "Constraints": "絕對邊界", "Tone": "風格與語氣", "Examples": "參考範例", "Steps": "執行步驟"}
        for key, value in opt_data.items():
            if value and value != "null":
                st.markdown(f"**【{key_mapping.get(key, key)}】**\n> {value}")

    with tabs[1]:
        st.markdown("### 惡魔火烤與特教老師的指導")
        for i, diag in enumerate(result_data.get("diagnostics", []), 1):
            with st.expander(f"診斷重點 {i}", expanded=True):
                st.markdown(f"**{diag.get('roast', '')}**")
                st.markdown(f"*{diag.get('guide', '')}*")

    with tabs[2]:
        score = result_data.get("scorecard", {}).get("score", 0)
        st.metric(label="原指令戰鬥力", value=f"{score} / 100")
        st.progress(score / 100)
        st.info(result_data.get("scorecard", {}).get("evaluation", ""))

    with tabs[3]:
        st.write(result_data.get("summary", ""))

    with tabs[4]:
        st.code(result_data.get("markdown_export", ""), language="markdown")

    with tabs[5]:
        st.markdown("### 🏃 即刻驗證召喚效果")
        st.info("點擊下方按鈕，系統將直接拿這段「究極咒語」去執行最終任務（支援動態渲染 Mermaid 流程圖！）。")
        
        if st.button("🚀 立即執行究極咒語", type="secondary"):
            with st.spinner("AI 正在根據咒語召喚結果，請稍候..."):
                try:
                    final_prompt = result_data.get("markdown_export", "")
                    
                    # 🛡️ 執行期終極防呆 (嚴格單行字串)
                    execute_prompt = final_prompt + "\n\n【系統最後防呆指令】：請直接輸出最終的 Markdown 內容與 ```mermaid 程式碼，絕對不要把你的回覆包裝在 JSON 格式裡面！"
                    
                    genai.configure(api_key=api_key)
                    execution_model = genai.GenerativeModel(model_name=actual_model_name)
                    exec_response = execution_model.generate_content(execute_prompt)
                    st.session_state['execution_result'] = exec_response.text
                except Exception as ex:
                    st.error(f"召喚失敗：{str(ex)}")

        if 'execution_result' in st.session_state:
            st.divider()
            st.markdown("#### 📝 最終執行產出：")
            st.markdown(st.session_state['execution_result'])
            st.download_button("📥 下載召喚結果", data=st.session_state['execution_result'], file_name="ai_result.txt")
