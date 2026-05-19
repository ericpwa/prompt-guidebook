import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 0. 系統初始化與 Supabase 連線設定
# ==========================================
st.set_page_config(page_title="咒語魔法書 Prompt Guidebook", page_icon="✨", layout="wide")

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
# 2. 側邊欄：全新【標準帳密登入系統】
# ==========================================
with st.sidebar:
    st.header("👤 法師身份認證 (SaaS 版)")
    if supabase_connected:
        if 'user' not in st.session_state:
            st.info("登入或註冊後，解鎖「魔法迴廊」自動備份功能！")
            
            # 切換 登入 / 註冊 模式
            auth_mode = st.radio("選擇操作", ["🔓 登入", "📝 註冊新帳號"], horizontal=True)
            
            email = st.text_input("輸入 Email")
            password = st.text_input("輸入密碼 (至少 6 位數)", type="password")
            
            if st.button("🚀 確認送出", use_container_width=True, type="primary"):
                if not email or not password:
                    st.warning("請填寫 Email 與密碼！")
                elif len(password) < 6:
                    st.warning("密碼必須至少 6 個字元！")
                else:
                    with st.spinner("連線至雲端金庫中..."):
                        try:
                            if auth_mode == "📝 註冊新帳號":
                                # 執行註冊
                                res = supabase.auth.sign_up({"email": email, "password": password})
                                if res.user:
                                    st.session_state['user'] = res.user
                                    st.success("註冊並登入成功！魔法迴廊已開啟。")
                                    st.rerun()
                            else:
                                # 執行登入
                                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                                if res.user:
                                    st.session_state['user'] = res.user
                                    st.success("登入成功！魔法迴廊已開啟。")
                                    st.rerun()
                        except Exception as e:
                            err_msg = str(e)
                            if "already registered" in err_msg:
                                st.error("此 Email 已經註冊過囉，請切換至「登入」模式。")
                            elif "Invalid login credentials" in err_msg:
                                st.error("Email 或密碼錯誤，請重新確認！")
                            else:
                                st.error(f"發生錯誤：{err_msg}")
        else:
            st.success(f"✅ 已登入法師：\n{st.session_state['user'].email}")
            if st.button("🚪 登出帳號", use_container_width=True):
                if supabase_connected:
                    try:
                        supabase.auth.sign_out()
                    except:
                        pass
                del st.session_state['user']
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
        2. 勾選同意條款，並用 Google 帳號登入。
        3. 點擊藍色大按鈕 **「Get API key」** ➡️ **「Create API key」**。
        4. 複製 `AIza...` 開頭的亂碼，貼回上方框框中！
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
# Role & Persona
你是《咒語魔法書 Prompt Guidebook》的核心編譯引擎。你是一個「雙面人格」的頂尖提示詞大師：
1. 【火烤大師】：精準吐槽原始提示詞的缺陷與可能導致的 AI 災難。
2. 【特教老師】：吐槽完後，用白話文解釋「為什麼這樣改會更好」，並給予指導。

# 🧠 Dynamic Visual Judgment - ⚠️ 極度重要
仔細分析使用者傳入的【使用者期望的視覺呈現】與【原始需求】：
- 若使用者指定「表格」或「流程圖/心智圖」，你必須在優化後的 `Output_Format` 中，嚴格規定產出該格式。若為圖表，強制要求產出「複雜、高細節的 Mermaid 視覺圖表」。鐵血規定：
  1. 使用多樣化節點形狀。
  2. 箭頭加上說明文字。
  3. 使用 `style` 或 `classDef` 塗上色彩。
  4. 開頭標示為 ```mermaid 。
  5. 【防呆死線】：嚴格規定直接輸出 Markdown，絕對禁止包裝成 JSON。
- 若選擇「純文字」但你判定適合視覺化，主動加入 Mermaid 產圖指令，並在診斷報告中說明。

# Constraints & Rules
嚴格遵循【七大核心 + 兩項動態彈性】提示詞結構。

# Output Format (強制 JSON 輸出)
請嚴格依照以下 JSON Schema 輸出純 JSON 字串：
{
  "optimized_prompt": {
    "Role": "...", "Context": "...", "Task": "...", "Success_Criteria": "...", 
    "Output_Format": "具體格式要求", "Constraints": "...", "Tone": "...", 
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
        set_template("我正在用 [填入:Python/JavaScript] 開發，這段程式碼一直報錯 [填入:錯誤訊息]。請幫我找出根本原因，並提供修改後的完整程式碼。")
with col4:
    if st.button("🧠 企劃發想", use_container_width=True): 
        set_template("我是 [填入:行銷/專案經理]，請幫我發想 3 個關於 [填入:節慶行銷/新功能推廣] 的創新提案，需包含目標、執行步驟與預期效益。")

# ==========================================
# 5. 主畫面：使用者輸入區
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
# 6. 編譯引擎執行邏輯
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
                
                # 🛡️ SaaS 資料庫儲存機制
                if supabase_connected and 'user' in st.session_state:
                    try:
                        db_payload = {
                            "user_id": st.session_state['user'].id,
                            "prompt_data": compiled_json
                        }
                        supabase.table("prompt_history").insert(db_payload).execute()
                    except Exception as db_err:
                        st.toast(f"⚠️ 雲端備份失敗 ({str(db_err)})")

                st.success("✨ 咒語編譯完成！")
                st.balloons()
            except Exception as e:
                error_msg = str(e).lower()
                if "quota" in error_msg: st.error("🛑 當日魔力額度已用盡！")
                elif "api_key" in error_msg or "400" in error_msg: st.error("🔑 API Key 無效！")
                elif "json_error" in error_msg: st.error("🧩 模型迴路異常，請重試。")
                else: st.error(f"⚠️ 發生未知錯誤：{str(e)}")

# ==========================================
# 7. UI 頁籤渲染
# ==========================================
if 'compiled_result' in st.session_state or ('user' in st.session_state):
    
    if 'compiled_result' in st.session_state:
        tabs = st.tabs(["✨ 究極咒語", "🧪 惡魔低語", "📊 戰鬥力分數卡", "📝 施法日誌", "📦 無腦打包", "🚀 真實召喚", "🗂️ 我的魔法迴廊"])
        result_data = st.session_state['compiled_result']
        
        with tabs[0]:
            st.markdown("### 結構化拆解")
            opt_data = result_data.get("optimized_prompt", {})
            for key, value in opt_data.items():
                if value and value != "null":
                    st.markdown(f"**【{key}】**\n> {value}")

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
                with st.spinner("AI 正在召喚，請稍候..."):
                    try:
                        final_prompt = result_data.get("markdown_export", "")
                        execute_prompt = final_prompt + "\n\n【防呆】：直接輸出 Markdown 與 ```mermaid 程式碼，絕對不要包裝在 JSON 裡！"
                        genai.configure(api_key=api_key)
                        execution_model = genai.GenerativeModel(model_name=actual_model_name)
                        exec_response = execution_model.generate_content(execute_prompt)
                        st.session_state['execution_result'] = exec_response.text
                    except Exception as ex:
                        st.error(f"召喚失敗：{str(ex)}")

            if 'execution_result' in st.session_state:
                st.divider()
                st.markdown(st.session_state['execution_result'])
                
        history_tab = tabs[6]
    else:
        history_tab = st.tabs(["🗂️ 我的魔法迴廊"])[0]

    with history_tab:
        st.markdown("### 🗂️ 我的專屬魔法迴廊")
        st.caption("雲端金庫內建 2 天自動銷毀機制。")
        
        if not supabase_connected:
            st.warning("系統未連線至資料庫，無法讀取紀錄。")
        elif 'user' not in st.session_state:
            st.info("👈 請先於左側面板註冊或登入，解鎖個人專屬歷史紀錄！")
        else:
            if st.button("🔄 刷新迴廊"):
                st.rerun()
                
            try:
                history = supabase.table("prompt_history").select("*").order("created_at", desc=True).execute()
                if not history.data:
                    st.info("目前迴廊空空如也，快去詠唱你的第一個咒語吧！")
                else:
                    for record in history.data:
                        created_time = record['created_at'][:16].replace('T', ' ')
                        p_data = record['prompt_data']
                        task_name = p_data.get('optimized_prompt', {}).get('Task', '未命名任務')
                        with st.expander(f"🕰️ {created_time} | {task_name[:30]}...", expanded=False):
                            st.code(p_data.get('markdown_export', '無匯出資料'), language='markdown')
            except Exception as e:
                st.error(f"讀取紀錄失敗：{str(e)}")
