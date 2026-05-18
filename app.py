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
    st.header("⚙️ 系統設定")
    api_key = st.text_input("請輸入 Google Gemini API Key", type="password")
    st.markdown("[取得免費 API Key (Google AI Studio)](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.subheader("📡 模型雷達 (Model Radar)")
    
    MODEL_RADAR = {
        "Gemini 2.5 Flash 🥇 推薦：最新極速運算、邏輯編譯首選": "models/gemini-2.5-flash",
        "Gemini 2.0 Flash (經典穩定版)：高性價比、穩健輸出": "models/gemini-2.0-flash",
        "Gemini 2.0 Flash-Lite (極速版)：最低延遲反應": "models/gemini-2.0-flash-lite",
        "Gemini Flash Latest (最新滾動版)：動態更新端點": "models/gemini-flash-latest"
    }
    
    model_choice_label = st.selectbox("選擇 AI 編譯引擎", options=list(MODEL_RADAR.keys()), index=0)
    actual_model_name = MODEL_RADAR[model_choice_label]

# ==========================================
# 3. 核心大腦：Meta-Prompt (系統指令)
# ==========================================
META_PROMPT = """
# Role & Persona (角色與人設)
你是《咒語魔法書 Prompt Guidebook》的核心編譯引擎。你是一個「雙面人格」的頂尖提示詞大師：
1. 【火烤大師】：風格像單口喜劇演員，擅長用幽默、辛辣、荒謬誇飾的比喻，精準吐槽原始提示詞的缺陷與可能導致的 AI 災難。
2. 【特教老師】：吐槽完後，會立刻變回溫暖包容、充滿愛心耐心的導師，用白話文解釋「為什麼這樣改會更好」，並給予實用的觀念指導。（注意：語氣要像對待成年學生的溫柔引導，不可使用疊字或幼兒化的語氣）。

# Constraints & Rules (絕對邊界與規則) - ⚠️ 極度重要
1. 火烤邊界限制：只能吐槽「提示詞本身的結構、邏輯或語意模糊」，絕對禁止人身攻擊、貶低使用者的智商或職業。
2. 必須嚴格遵循【七大核心 + 兩項動態彈性】的次世代提示詞結構來重組優化版本的指令。

# Output Format (強制 JSON 輸出格式)
請嚴格依照以下 JSON Schema 輸出，不要輸出任何 Markdown 標記，只要純 JSON 字串：
{
  "optimized_prompt": {
    "Role": "...", "Context": "...", "Task": "...", "Success_Criteria": "...", 
    "Output_Format": "...", "Constraints": "...", "Tone": "...", 
    "Examples": "...", "Steps": "..."
  },
  "diagnostics": [{"roast": "...", "guide": "..."}],
  "scorecard": {"score": 60, "evaluation": "..."},
  "summary": "...",
  "markdown_export": "..."
}
"""

# ==========================================
# 4. 主畫面：使用者輸入區
# ==========================================
st.subheader("📝 輸入你的原始指令")
original_prompt = st.text_area(
    "請隨意輸入你的需求（支援片段式關鍵字或白話文），魔法書會自動幫你轉譯：",
    height=150, placeholder="例如：我來不及交報告，幫我寫一封文情並茂的信。"
)

# ==========================================
# 5. 編譯引擎執行邏輯
# ==========================================
if st.button("✨ 一鍵編譯與優化", type="primary"):
    if not api_key:
        st.error("請先在左側邊欄輸入 API Key！")
    elif not original_prompt:
        st.warning("請輸入原始指令！")
    else:
        # 重置試跑結果
        if 'execution_result' in st.session_state:
            del st.session_state['execution_result']
            
        display_engine_name = model_choice_label.split('🥇')[0].split('(')[0].strip()
        with st.spinner(f"魔法書編譯中（使用引擎：{display_engine_name}），請稍候..."):
            try:
                genai.configure(api_key=api_key)
                generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
                model = genai.GenerativeModel(model_name=actual_model_name, system_instruction=META_PROMPT, generation_config=generation_config)
                response = model.generate_content(original_prompt)
                
                raw_text = response.text.strip()
                start_idx, end_idx = raw_text.find('{'), raw_text.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = raw_text[start_idx:end_idx+1]
                else:
                    raise ValueError("JSON_ERROR")

                st.session_state['compiled_result'] = json.loads(clean_json_str)
                st.success("編譯完成！請查看下方各頁籤的報告。")
                st.balloons()
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg: st.error("🛑 當日免費額度已用盡！")
                elif "429" in error_msg: st.warning("⏳ 點擊太快囉！請等 1 分鐘。")
                elif "api_key" in error_msg: st.error("🔑 API Key 無效！")
                else: st.error(f"⚠️ 發生未知錯誤：{str(e)}")

# ==========================================
# 6. UI 頁籤渲染 (💡 升級：新增第 6 個試跑 Tab)
# ==========================================
if 'compiled_result' in st.session_state:
    result_data = st.session_state['compiled_result']
    
    tabs = st.tabs(["✨ 優化後 Prompt", "🧪 診斷報告", "📊 分數卡", "📝 修改摘要", "📦 Markdown 匯出", "🚀 一鍵試跑結果"])

    # [頁籤 1] 結構化拆解
    with tabs[0]:
        st.markdown("### 結構化拆解")
        opt_data = result_data.get("optimized_prompt", {})
        key_mapping = {"Role": "角色與人設", "Context": "背景脈絡", "Task": "核心任務", "Success_Criteria": "驗收標準", "Output_Format": "輸出格式", "Constraints": "絕對邊界", "Tone": "風格與語氣", "Examples": "參考範例", "Steps": "執行步驟"}
        for key, value in opt_data.items():
            if value and value != "null":
                st.markdown(f"**【{key_mapping.get(key, key)}】**\n> {value}")

    # [頁籤 2] 診斷報告
    with tabs[1]:
        st.markdown("### 惡魔與特教老師的指導")
        for i, diag in enumerate(result_data.get("diagnostics", []), 1):
            with st.expander(f"診斷重點 {i}", expanded=True):
                st.markdown(f"**{diag.get('roast', '')}**")
                st.markdown(f"*{diag.get('guide', '')}*")

    # [頁籤 3] 分數卡
    with tabs[2]:
        score = result_data.get("scorecard", {}).get("score", 0)
        st.metric(label="原指令分數", value=f"{score} / 100")
        st.progress(score / 100)
        st.info(result_data.get("scorecard", {}).get("evaluation", ""))

    # [頁籤 4] 修改摘要
    with tabs[3]:
        st.write(result_data.get("summary", ""))

    # [頁籤 5] Markdown 匯出
    with tabs[4]:
        st.code(result_data.get("markdown_export", ""), language="markdown")

    # [💡 頁籤 6] 🚀 一鍵試跑結果 (Direction 2 新功能)
    with tabs[5]:
        st.markdown("### 🏃 即刻驗證編譯效果")
        st.info("點擊下方按鈕，系統將直接拿這段「優化後的指令」去執行最終任務。")
        
        # 執行按鈕
        if st.button("🚀 立即執行優化後的指令", type="secondary"):
            with st.spinner("AI 正在根據優化後的指令生成結果，請稍候..."):
                try:
                    final_prompt = result_data.get("markdown_export", "")
                    genai.configure(api_key=api_key)
                    # 試跑不使用 JSON Mode，使用一般對話模式
                    execution_model = genai.GenerativeModel(model_name=actual_model_name)
                    exec_response = execution_model.generate_content(final_prompt)
                    st.session_state['execution_result'] = exec_response.text
                except Exception as ex:
                    st.error(f"試跑失敗：{str(ex)}")

        # 顯示試跑結果
        if 'execution_result' in st.session_state:
            st.divider()
            st.markdown("#### 📝 最終執行產出：")
            st.markdown(st.session_state['execution_result'])
            st.download_button("📥 下載執行結果", data=st.session_state['execution_result'], file_name="ai_result.txt")
