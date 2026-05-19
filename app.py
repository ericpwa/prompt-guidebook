import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 0. 系統初始化與 Supabase 連線設定
# ==========================================
st.set_page_config(page_title="咒語魔法書 Prompt Guidebook", page_icon="✨", layout="wide")

# 嘗試連線 Supabase (防呆機制：若未設定 Secrets 則顯示警告但不崩潰)
supabase_connected = False
try:
    from supabase import create_client, Client
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_connected = True
except Exception as e:
    pass

# ==========================================
# 1. 頁面與基本設定
# ==========================================
st.title("✨ 咒語魔法書 Prompt Guidebook")
st.markdown("將模糊的自然語言，一鍵轉譯為高精準度、無雜訊、具備結構化防呆機制的AI指令提示詞。")

# ==========================================
# 2. 側邊欄：SaaS 會員登入、API Key 與模型設定
# ==========================================
with st.sidebar:
    st.header("🧙‍♂️ 法師身份認證 (SaaS 版)")
    if supabase_connected:
        if 'user' not in st.session_state:
            st.info("登入後解鎖「魔法迴廊」，系統將為您自動備份專屬咒語！")
            email = st.text_input("輸入 Email 獲取魔法驗證碼 (免密碼登入)")
            
            if st.button("📧 發送驗證碼", use_container_width=True):
                if email:
                    try:
                        supabase.auth.sign_in_with_otp({"email": email})
                        st.session_state['otp_sent'] = True
                        st.session_state['auth_email'] = email
                        st.success("✨ 驗證碼已發送至信箱！(請留意垃圾信件匣)")
                    except Exception as e:
                        st.error(f"發送失敗：{str(e)}")
                else:
                    st.warning("請先輸入 Email。")

            if st.session_state.get('otp_sent', False):
                otp = st.text_input("輸入信件中的 6 位數驗證碼", type="password")
                if st.button("🔓 驗證並登入", type="primary", use_container_width=True):
                    try:
                        res = supabase.auth.verify_otp({"email": st.session_state['auth_email'], "token": otp, "type": "email"})
                        st.session_state['user'] = res.user
                        st.success("登入成功！魔法迴廊已開啟。")
                        st.rerun()
                    except Exception as e:
                        st.error("驗證失敗，請檢查驗證碼是否正確或過期。")
        else:
            st.success(f"✅ 已登入法師：\n{st.session_state['user'].email}")
            if st.button("🚪 登出", use_container_width=True):
                supabase.auth.sign_out()
                del st.session_state['user']
                if 'otp_sent' in st.session_state:
                    del st.session_state['otp_sent']
                st.rerun()
    else:
        st.error("⚠️ 系統偵測不到 Supabase 金鑰，請確認是否已在 Streamlit Secrets 中設定！")

    st.divider()

    st.header("⚙️ 魔法書後端設定")
    api_key = st.text_input("🔑 輸入你的魔力來源 (Google Gemini API Key)", type="password")
    st.markdown("[👉 點我前往取得免費 API Key (Google AI Studio)](https://aistudio.google.com/app/apikey)")
    
    with st.expander("🦠 草履蟲指南：取得魔力來源"):
        st.markdown("""
        **只要 30 秒，超無腦 5 步驟：**
        1. 點擊上方的 **「👉 點我前往...」** 連結。
        2. 勾選同意條款，並用你的 **Google 帳號登入**。
        3. 在畫面左上方，點擊藍色大按鈕 **「Get API key」**。
        4. 點擊 **「Create API key」** (系統會自動幫你建專案)。
        5. **複製**畫面上出現的那串 `AIza...` 開頭的長長亂碼，貼回左側的「魔力來源」框框中，大功告成！
        """)
    
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
        "📊 簡易 結構化表格 (適合比較、數據)",
        "🗺️ 簡易 流程圖/心智圖 (Mermaid 視覺圖表)"
    ],
    horizontal=True
)

# ==========================================
# 6. 編譯引擎執行邏輯 (加入資料庫寫入機制)
# ==========================================
if st.button("✨ 詠唱！一鍵編譯與優化", type="primary"):
    if not api_key:
        st.error("請先在左側邊欄輸入 API Key（注入魔力）！")
    elif not original_prompt:
        st.warning("請輸入你的原始指令！")
    else:
        if 'execution_result' in st.session_state:
            del st.session_state['execution_result']
            
        combined_prompt = f"【使用者原始需求】\n{original_prompt}\n\n【使用者期望的視覺呈現】\n{visual_choice}"
            
        display_engine_name = model_choice_label.split('🥇')[0].split('(')[0].strip()
        with st.spinner(f"魔法書正在詠唱轉譯中（使用引擎：{display_engine_name}），請稍候..."):
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

                compiled_json = json.loads(clean_json_str)
                st.session_state['compiled_result'] = compiled_json
                
                # 🛡️ SaaS 資料庫儲存機制 (僅針對已登入使用者)
                if supabase_connected and 'user' in st.session_state:
                    try:
                        db_payload = {
                            "user_id": st.session_state['user'].id,
                            "prompt_data": compiled_json
                        }
                        supabase.table("prompt_history").insert(db_payload).execute()
                    except Exception as db_err:
                        st.toast(f"⚠️ 雲端備份失敗，但不影響當前結果顯示。({str(db_err)})")

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
# 7. UI 頁籤渲染 (新增第 7 個頁籤：魔法迴廊)
# ==========================================
if 'compiled_result' in st.session_state or ('user' in st.session_state):
    
    # 動態決定 Tabs 數量 (有當次結果才顯示前 6 個 Tabs)
    if 'compiled_result' in st.session_state:
        tabs = st.tabs(["✨ 究極咒語", "🧪 惡魔低語", "📊 分數卡", "📝 施法日誌", "📦 無腦打包", "🚀 真實召喚", "🗂️ 我的魔法迴廊"])
        result_data = st.session_state['compiled_result']
        
        with tabs[0]:
            st.markdown("### 結構化拆解")
            opt_data = result_data.get("optimized_prompt", {})
            key_mapping = {"Role": "角色", "Context": "脈絡", "Task": "任務", "Success_Criteria": "驗收標準", "Output_Format": "輸出格式", "Constraints": "邊界", "Tone": "語氣", "Examples": "範例", "Steps": "步驟"}
            for key, value in opt_data.items():
                if value and value != "null":
                    st.markdown(f"**【{key_mapping.get(key, key)}】**\n> {value}")

        with tabs[1]:
            st.markdown("### 天使與惡魔的指導")
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
            if st.button("🚀 立即執行究極咒語", type="secondary"):
                with st.spinner("AI 正在根據咒語召喚結果，請稍候..."):
                    try:
                        final_prompt = result_data.get("markdown_export", "")
                        execute_prompt = final_prompt + "\n\n【系統防呆】：請直接輸出 Markdown 與 ```mermaid 程式碼，絕對不要包裝在 JSON 裡面！"
                        genai.configure(api_key=api_key)
                        execution_model = genai.GenerativeModel(model_name=actual_model_name)
                        exec_response = execution_model.generate_content(execute_prompt)
                        st.session_state['execution_result'] = exec_response.text
                    except Exception as ex:
                        st.error(f"召喚失敗：{str(ex)}")

            if 'execution_result' in st.session_state:
                st.divider()
                st.markdown(st.session_state['execution_result'])
                
        # 第 7 頁籤分配給魔法迴廊
        history_tab = tabs[6]
    else:
        # 若無當次結果，只顯示魔法迴廊
        history_tab = st.tabs(["🗂️ 我的魔法迴廊"])[0]

    # --- 歷史紀錄渲染邏輯 ---
    with history_tab:
        st.markdown("### 🗂️ 我的專屬魔法迴廊")
        st.caption("雲端金庫內建 2 天自動銷毀機制，確保隱私不留痕。")
        
        if not supabase_connected:
            st.warning("系統未連線至資料庫，無法讀取紀錄。")
        elif 'user' not in st.session_state:
            st.info("請先於左側面板輸入 Email 登入，即可解鎖您的個人歷史紀錄庫！")
        else:
            if st.button("🔄 刷新迴廊"):
                st.rerun()
                
            try:
                # 由於 RLS 防護，使用者只會 select 到屬於自己的資料
                history = supabase.table("prompt_history").select("*").order("created_at", desc=True).execute()
                
                if not history.data:
                    st.info("目前迴廊空空如也，快去詠唱你的第一個咒語吧！")
                else:
                    for record in history.data:
                        # 擷取時間與任務名稱作為標題
                        created_time = record['created_at'][:16].replace('T', ' ')
                        p_data = record['prompt_data']
                        task_name = p_data.get('optimized_prompt', {}).get('Task', '未命名任務')
                        
                        with st.expander(f"🕰️ {created_time} | {task_name[:30]}...", expanded=False):
                            st.code(p_data.get('markdown_export', '無匯出資料'), language='markdown')
            except Exception as e:
                st.error(f"讀取紀錄失敗：{str(e)}")
