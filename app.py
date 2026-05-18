import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 頁面與基本設定
# ==========================================
st.set_page_config(page_title="咒語魔法書 Prompt Guidebook", page_icon="🪄", layout="wide")
st.title("🪄 咒語魔法書 Prompt Guidebook")
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
    
    # 穩定性修正：絕對路徑路由，確保符合 API 權限
    MODEL_RADAR = {
        "Gemini 2.5 Flash 🥇 推薦：最新極速運算、邏輯編譯首選": "models/gemini-2.5-flash",
        "Gemini 2.0 Flash (經典穩定版)：高性價比、穩健輸出": "models/gemini-2.0-flash",
        "Gemini 2.0 Flash-Lite (極速版)：最低延遲反應": "models/gemini-2.0-flash-lite",
        "Gemini Flash Latest (最新滾動版)：動態更新端點": "models/gemini-flash-latest"
    }
    
    # 渲染下拉選單
    model_choice_label = st.selectbox(
        "選擇 AI 編譯引擎",
        options=list(MODEL_RADAR.keys()),
        index=0  # 預設選中 2.5 Flash
    )
    
    # 取得對應的實際 API 模型絕對路徑
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
1. 火烤邊界限制：只能吐槽「提示詞本身的結構、邏輯或語意模糊」，絕對禁止人身攻擊、貶低使用者的智商或職業。吐槽重點在於「AI 看到這句話會有多困惑/產出多好笑的結果」。
2. 必須嚴格遵循【七大核心 + 兩項動態彈性】的次世代提示詞結構來重組優化版本的指令。

# Output Format (強制 JSON 輸出格式)
請嚴格依照以下 JSON Schema 輸出，以利前端介面直接解析。絕對不要輸出任何 Markdown 標記（如 ```json）或其他文字，只要純 JSON 字串：

{
  "optimized_prompt": {
    "Role": "為任務設定的專家角色，具備應有的專業知識和思考模式",
    "Context": "任務發生的時空背景與前因後果",
    "Task": "明確的動作指令與目標",
    "Success_Criteria": "產出物必須達到的任務目標或品質",
    "Output_Format": "具體的輸出格式或排版要求（表格、Markdown、字數等）",
    "Constraints": "不能做的事、不能用的詞、風險邊界、防呆機制",
    "Tone": "文字的溫度與專業度設定",
    "Examples": "參考範例（若無則填 null）",
    "Steps": "執行步驟（除非必要，否則填 null 讓模型自行發揮）"
  },
  "diagnostics": [
    {
      "roast": "🔥 惡魔火烤：[用單口喜劇的誇飾語氣吐槽這個缺點]",
      "guide": "👼 天使指路：[用特教老師的溫柔語氣給予正確觀念與解法]"
    }
  ],
  "scorecard": {
    "score": 60, 
    "evaluation": "🎭 總評：[一句辛辣的玩笑話] + [一句溫暖的鼓勵]"
  },
  "summary": "簡述本次編譯幫原指令加上了哪些結構與防呆機制",
  "markdown_export": "將優化後的各個欄位，組合成可以直接複製貼上的純文字 Markdown 格式，加上層級標題（如 ### 角色與人設 等）。"
}
"""

# ==========================================
# 4. 主畫面：使用者輸入區
# ==========================================
st.subheader("📝 輸入你的原始指令")
original_prompt = st.text_area(
    "請隨意輸入你的需求（支援片段式關鍵字或白話文），魔法書會自動幫你轉譯：",
    height=150,
    placeholder="例如：我來不及交報告，幫我寫一封文情並茂的信。"
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
        display_engine_name = model_choice_label.split('🥇')[0].split('(')[0].strip()
        with st.spinner(f"魔法書編譯中（使用引擎：{display_engine_name}），請稍候..."):
            try:
                genai.configure(api_key=api_key)
                
                generation_config = genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
                
                model = genai.GenerativeModel(
                    model_name=actual_model_name,
                    system_instruction=META_PROMPT,
                    generation_config=generation_config
                )

                response = model.generate_content(original_prompt)
                
                # 防彈機制：JSON 字串清理
                raw_text = response.text.strip()
                start_idx = raw_text.find('{')
                end_idx = raw_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = raw_text[start_idx:end_idx+1]
                else:
                    raise ValueError("JSON_ERROR")

                result_data = json.loads(clean_json_str)
                st.session_state['compiled_result'] = result_data
                
                # 🎈 UX 優化：成功後飄出慶祝氣球！
                st.success("編譯完成！請查看下方各頁籤的報告。")
                st.balloons()
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    st.warning("⏳ **點擊太快囉！** Google API 免費版每分鐘有 15 次的呼叫限制。請喝口水，**稍等 1 分鐘後再點擊一次**。")
                elif "404" in error_msg:
                    st.error("🚫 **模型暫不可用！** 您選擇的 AI 模型端點目前被 Google 關閉或您的 API Key 無法存取。請從左側選單**切換另一個模型**再試一次。")
                elif "JSON_ERROR" in error_msg or "Expecting value" in error_msg:
                    st.error("🧩 **AI 回傳格式異常！** 模型這次太有創意，忘記遵守 JSON 格式了。這偶爾會發生，請**直接再點擊一次按鈕**重新編譯即可。")
                else:
                    st.error(f"⚠️ 發生未知錯誤：{error_msg}")

# ==========================================
# 6. UI 頁籤渲染 (Tab 顯示區)
# ==========================================
if 'compiled_result' in st.session_state:
    result_data = st.session_state['compiled_result']
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🪄 優化後 Prompt", 
        "🧪 診斷報告", 
        "📊 分數卡", 
        "📝 修改摘要", 
        "📦 Markdown 匯出"
    ])

    with tab1:
        st.markdown("### 結構化拆解")
        opt_data = result_data.get("optimized_prompt", {})
        
        key_mapping = {
            "Role": "角色與人設", "Context": "背景脈絡", "Task": "核心任務",
            "Success_Criteria": "驗收標準", "Output_Format": "輸出格式",
            "Constraints": "絕對邊界", "Tone": "風格與語氣", 
            "Examples": "參考範例", "Steps": "執行步驟"
        }
        
        for key, value in opt_data.items():
            if value:
                display_name = key_mapping.get(key, key)
                st.markdown(f"**【{display_name}】**\n> {value}")

    with tab2:
        st.markdown("### 惡魔與特教老師的指導")
        diagnostics = result_data.get("diagnostics", [])
        for i, diag in enumerate(diagnostics, 1):
            with st.expander(f"診斷重點 {i}", expanded=True):
                st.markdown(f"**{diag.get('roast', '')}**")
                st.markdown(f"*{diag.get('guide', '')}*")

    with tab3:
        score = result_data.get("scorecard", {}).get("score", 0)
        eval_text = result_data.get("scorecard", {}).get("evaluation", "")
        
        st.metric(label="原指令分數", value=f"{score} / 100")
        st.progress(score / 100)
        st.info(eval_text)

    with tab4:
        st.markdown("### 系統執行動作")
        st.write(result_data.get("summary", ""))

    with tab5:
        st.markdown("### 最終交付成品")
        markdown_text = result_data.get("markdown_export", "")
        st.code(markdown_text, language="markdown")