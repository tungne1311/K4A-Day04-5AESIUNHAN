"""
starter_v0/app.py — IT Helpdesk Agent — Streamlit Chat Interface

Author : Ninh Quang Minh (minhnq-chc) — Member 4: UI & Chat Experience Engineer
Reuses : run_model_tool_loop() from chat.py
Run    : streamlit run app.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ── Reuse existing backend modules ────────
from chat import (
    run_model_tool_loop,
    trim_history,
    now_iso,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

# ── Constants ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"
AVATAR_PATH = ROOT / "assets" / "vhelpdesk_avatar.jpg"

load_lab_env(ROOT)

# ═══════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Vhelpdesk Bot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
#  TRANSLATIONS (EN / VN)
# ═══════════════════════════════════════════════════════════════════════════
TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "main_title": "🤖 Vhelpdesk Bot",
        "main_subtitle": "Northstar Labs IT Support",
        "session_label": "Session",
        "config_title": "⚙️ Configuration",
        "model_label": "OpenAI Model",
        "advanced_settings": "Advanced Settings",
        "version_label": "Artifact Version",
        "history_label": "History Window",
        "history_help": "Recent turn-pairs kept in context",
        "max_rounds_label": "Max Tool Rounds",
        "provenance_title": "📊 System Provenance",
        "artifact_ver": "Version",
        "prompt_hash": "Prompt Hash",
        "tools_hash": "Tools Hash",
        "demo_toggle": "🧪 Demo Mode (no API key)",
        "reset_btn": "🔄 Reset Chat",
        "export_btn": "📥 Export Transcript",
        "turns_label": "Turns",
        "chat_placeholder": "Describe your IT issue (e.g. VPN down, check device LT-204)...",
        "processing": "Analyzing request and executing tools…",
        "waiting_user": "⏸️ Agent paused — awaiting your clarification or confirmation.",
        "max_rounds_hit": "⚠️ Max tool rounds reached. Check the transcript for details.",
        "provider_error": "Provider Error",
        "artifacts_missing": "Artifact files not found! Check the `artifacts/` directory.",
        "round_label": "Round",
        "args_label": "Arguments",
        "result_label": "Result",
        "error_label": "Error",
    },
    "vi": {
        "main_title": "🤖 Vhelpdesk Bot",
        "main_subtitle": "Northstar Labs IT Support",
        "session_label": "Phiên",
        "config_title": "⚙️ Cấu hình",
        "model_label": "Model (OpenAI)",
        "advanced_settings": "⚙️ Cài đặt nâng cao",
        "version_label": "Phiên bản Artifact",
        "history_label": "Cửa sổ lịch sử",
        "history_help": "Số cặp tin nhắn gần nhất giữ trong ngữ cảnh",
        "max_rounds_label": "Số vòng tool tối đa",
        "provenance_title": "📊 Thông tin hệ thống",
        "artifact_ver": "Phiên bản",
        "prompt_hash": "Hash Prompt",
        "tools_hash": "Hash Tools",
        "demo_toggle": "🧪 Chế độ Demo (không cần API key)",
        "reset_btn": "🔄 Làm mới chat",
        "export_btn": "📥 Xuất lịch sử (JSON)",
        "turns_label": "Lượt hội thoại",
        "chat_placeholder": "Mô tả vấn đề IT (VD: VPN lỗi, kiểm tra thiết bị LT-204)…",
        "processing": "Đang phân tích yêu cầu và thực thi tools…",
        "waiting_user": "⏸️ Vhelpdesk đang chờ — vui lòng bổ sung thông tin hoặc xác nhận.",
        "max_rounds_hit": "⚠️ Đã đạt số vòng tool tối đa. Kiểm tra transcript để biết chi tiết.",
        "provider_error": "Lỗi nhà cung cấp",
        "artifacts_missing": "Không tìm thấy file artifact! Kiểm tra thư mục `artifacts/`.",
        "round_label": "Vòng",
        "args_label": "Tham số",
        "result_label": "Kết quả",
        "error_label": "Lỗi",
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  LIQUID GLASSMORPHISM CSS
# ═══════════════════════════════════════════════════════════════════════════
GLASS_CSS = """
<style>
    /* Liquid Glassmorphism adaptable to Streamlit Light/Dark */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'SF Pro Display', 'Inter', -apple-system, sans-serif;
    }
    
    /* Subtle gradient base using Streamlit's native variables */
    .stApp {
        background: linear-gradient(135deg, var(--background-color) 0%, var(--secondary-background-color) 100%) !important;
    }
    
    /* Sidebar Glass */
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
        background-image: linear-gradient(180deg, rgba(128,128,128,0.08) 0%, rgba(128,128,128,0.02) 100%) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(128,128,128,0.15) !important;
    }
    
    /* Chat Message Glass */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        background-image: linear-gradient(135deg, rgba(128,128,128,0.1) 0%, rgba(128,128,128,0.02) 100%) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(128,128,128,0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.05) !important;
        padding: 0.75rem 1rem !important;
        border-radius: 20px !important;
        margin-bottom: 0.5rem !important;
    }
    
    [data-testid="stChatMessage"] img {
        border-radius: 50% !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    }
    
    /* Chat Input Glass */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        background-image: linear-gradient(135deg, rgba(128,128,128,0.15) 0%, rgba(128,128,128,0.05) 100%) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 24px !important;
        border: 1px solid rgba(128,128,128,0.25) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08) !important;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: transparent !important;
        background-image: linear-gradient(135deg, rgba(128,128,128,0.05) 0%, rgba(128,128,128,0.01) 100%) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(128,128,128,0.15) !important;
    }
    
    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background-color: transparent !important;
        background-image: linear-gradient(135deg, rgba(128,128,128,0.1) 0%, rgba(128,128,128,0.05) 100%) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(128,128,128,0.2) !important;
        border-radius: 12px !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-image: linear-gradient(135deg, rgba(128,128,128,0.2) 0%, rgba(128,128,128,0.1) 100%) !important;
        transform: translateY(-1px);
    }
    
    /* Selectboxes */
    .stSelectbox [data-baseweb="select"] > div {
        background-color: transparent !important;
        background-image: linear-gradient(135deg, rgba(128,128,128,0.08) 0%, rgba(128,128,128,0.02) 100%) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(128,128,128,0.2) !important;
    }
    
    /* Main Layout */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
        max-width: 768px !important;
    }
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════
#  MOCK DATA FOR DEMO MODE
# ═══════════════════════════════════════════════════════════════════════════
def _mock_round(
    round_num: int,
    calls: list[tuple[str, dict, dict]],
) -> dict[str, Any]:
    return {
        "round": round_num,
        "assistant_text": None,
        "tool_calls": [{"name": c[0], "args": c[1]} for c in calls],
        "tool_results": [
            {"tool": c[0], "args": c[1], "result": c[2]} for c in calls
        ],
    }

MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "default": {
        "status": "answered",
        "assistant_text": (
            "Chào bạn, tôi là **Vhelpdesk bot** thuộc Northstar Labs. "
            "Bạn có thể hỏi tôi về:\n\n"
            "- Trạng thái dịch vụ (VPN, Email, Wi-Fi…)\n"
            "- Kiểm tra thiết bị (cần mã tài sản, VD: LT-204)\n"
            "- Tra cứu tài khoản nhân viên\n"
            "- Tạo ticket hỗ trợ\n\n"
            "Tôi có thể giúp gì cho bạn hôm nay?"
        ),
        "rounds": [],
        "tool_events": [],
    },
    "service_status": {
        "status": "answered",
        "assistant_text": (
            "Dịch vụ **VPN** trên môi trường **production** hiện đang ở trạng "
            "thái **degraded** — có báo cáo về tình trạng mất kết nối ngắt quãng. "
            "Đề xuất kiểm tra lại kết nối sau 15 phút hoặc liên hệ team Infra."
        ),
        "rounds": [
            _mock_round(1, [(
                "check_service_status",
                {"service": "vpn", "environment": "production"},
                {"service": "vpn", "environment": "production", "status": "degraded", "checked_at": "2026-09-14T14:30:00"},
            )]),
        ],
        "tool_events": [],
    },
    "device_inspect": {
        "status": "answered",
        "assistant_text": (
            "Thiết bị **LT-204** ghi nhận lỗi **AUTH_TIMEOUT** trên kết nối VPN. "
            "Client version 5.2.1.\n\nĐề xuất kiểm tra certificate VPN hoặc đối chiếu trạng thái dịch vụ."
        ),
        "rounds": [
            _mock_round(1, [(
                "inspect_device",
                {"asset_id": "LT-204", "check": "vpn"},
                {"tool": "inspect_device", "asset_id": "LT-204", "diagnostics": {"vpn": "client 5.2.1; AUTH_TIMEOUT"}},
            )]),
        ],
        "tool_events": [],
    },
    "ticket_confirm": {
        "status": "waiting_for_user",
        "assistant_text": (
            "Tôi sẽ tạo ticket với thông tin sau:\n\n"
            "- **Tóm tắt:** Sự cố VPN trên LT-204\n"
            "- **Mức ưu tiên:** high\n"
            "- **Thiết bị:** LT-204\n\n"
            "⚠️ **Bạn xác nhận tạo ticket này không?**"
        ),
        "rounds": [
            _mock_round(1, [(
                "clarify",
                {"question": "Xác nhận tạo ticket?", "response_type": "yes_no"},
                {"awaiting_user": True, "question": "Xác nhận tạo ticket?"},
            )]),
        ],
        "tool_events": [],
    },
    "ticket_created": {
        "status": "answered",
        "assistant_text": "✅ Ticket **TK-20260914-001** đã được tạo thành công! Trạng thái hiện tại: open.",
        "rounds": [
            _mock_round(1, [(
                "create_ticket",
                {"summary": "VPN issue on LT-204", "priority": "high", "confirmed": True},
                {"status": "created", "ticket_id": "TK-20260914-001"},
            )]),
        ],
        "tool_events": [],
    },
    "clarify_asset": {
        "status": "waiting_for_user",
        "assistant_text": "Vui lòng cho Vhelpdesk biết **mã tài sản (asset ID)** của thiết bị (VD: LT-204, DT-031)?",
        "rounds": [
            _mock_round(1, [(
                "clarify",
                {"question": "Mã tài sản?", "response_type": "text"},
                {"awaiting_user": True, "question": "Mã tài sản?"},
            )]),
        ],
        "tool_events": [],
    },
}

def get_mock_response(user_text: str) -> dict[str, Any]:
    text = user_text.lower()
    if any(kw in text for kw in ["xác nhận", "confirm", "có"]):
        return MOCK_RESPONSES["ticket_created"]
    if any(kw in text for kw in ["tạo ticket", "create ticket"]):
        return MOCK_RESPONSES["ticket_confirm"]
    if any(kw in text for kw in ["máy mình", "laptop của"]):
        return MOCK_RESPONSES["clarify_asset"]
    if "vpn" in text and ("trạng thái" in text or "status" in text or "lỗi" in text):
        return MOCK_RESPONSES["service_status"]
    if re.search(r"[a-z]{2}-\d{3}", text, re.IGNORECASE):
        return MOCK_RESPONSES["device_inspect"]
    return MOCK_RESPONSES["default"]

# ═══════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def parse_assistant_text(text: str) -> str:
    """If the agent returns raw JSON, extract the 'reply' or 'message' field."""
    if not text:
        return ""
    try:
        # In case there's markdown code block around the JSON
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data.get("reply", data.get("message", text))
    except Exception:
        pass
    return text

def render_tool_traces(turn_data: dict[str, Any], T: dict[str, str]) -> None:
    for round_data in turn_data.get("rounds", []):
        round_idx = round_data.get("round", "?")
        for tr in round_data.get("tool_results", []):
            tool_name = tr.get("tool", "unknown")
            tool_args = tr.get("args", {})
            tool_result = tr.get("result", {})
            is_error = isinstance(tool_result, dict) and "error" in tool_result
            icon = "❌" if is_error else "🔧"
            label = f"{icon} {T['round_label']} {round_idx} · `{tool_name}`"
            with st.expander(label, expanded=False):
                st.markdown(f"**{T['args_label']}:**")
                st.json(tool_args)
                if is_error:
                    st.error(f"{tool_result.get('error', 'error')}: {tool_result.get('message', '')}")
                else:
                    st.markdown(f"**{T['result_label']}:**")
                    st.json(tool_result)

def render_status_badge(status: str, T: dict[str, str]) -> None:
    if status == "waiting_for_user":
        st.info(T["waiting_user"])
    elif status == "max_tool_rounds":
        st.warning(T["max_rounds_hit"])
    elif status == "provider_error":
        st.error(T["provider_error"])

# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════
if "turns" not in st.session_state:
    st.session_state.turns = []
    st.session_state.history = []
    st.session_state.created_at = now_iso()
    st.session_state.transcript_id = f"ui_{datetime.now().strftime('%Y%m%dT%H%M%S')}"

# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR (COMPACT LAYOUT)
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    lang_map = {"Tiếng Việt": "vi", "English": "en"}
    lang_display = st.selectbox("🌐 Ngôn ngữ / Language", list(lang_map.keys()), index=0)
    lang = lang_map[lang_display]
    T = TRANSLATIONS[lang]
    st.divider()

    st.subheader(T["config_title"])
    model_name = st.selectbox(T["model_label"], ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"], index=0)
    
    with st.expander(T["advanced_settings"]):
        version_label = st.selectbox(T["version_label"], ["v0", "v1", "v2", "v3"], index=0)
        history_window = st.slider(T["history_label"], 1, 10, 5, help=T["history_help"])
        max_rounds = st.slider(T["max_rounds_label"], 1, 8, 4)

    # Spacing
    st.write("")
    demo_mode = st.toggle(T["demo_toggle"], value=False)
    
    # Spacing
    st.write("")
    
    art_ver = None
    if SYSTEM_PROMPT_PATH.exists() and TOOLS_PATH.exists():
        art_ver = build_artifact_version(version_label, SYSTEM_PROMPT_PATH, TOOLS_PATH)
        
    transcript_data = {
        "transcript_id": st.session_state.transcript_id,
        **(artifact_version_dict(art_ver) if art_ver else {}),
        "provider": "openai",
        "model": model_name,
        "history_window": history_window,
        "max_tool_rounds": max_rounds,
        "created_at": st.session_state.created_at,
        "updated_at": now_iso(),
        "turns": st.session_state.turns,
        "demo_mode": demo_mode,
    }
    
    st.download_button(
        label=T["export_btn"],
        data=json.dumps(transcript_data, ensure_ascii=False, indent=2, default=str),
        file_name=f"{st.session_state.transcript_id}.transcript.json",
        mime="application/json",
        use_container_width=True,
    )
    
    if st.button(T["reset_btn"], use_container_width=True):
        st.session_state.turns = []
        st.session_state.history = []
        st.session_state.transcript_id = f"ui_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        st.session_state.created_at = now_iso()
        st.rerun()

    # Move Provenance to the very bottom
    st.markdown("<div style='margin-top: 50vh;'></div>", unsafe_allow_html=True)
    st.divider()
    if art_ver:
        st.caption(f"**{T['provenance_title']}**")
        st.caption(f"{T['artifact_ver']}: `{art_ver.artifact_version}`")
        st.caption(f"{T['prompt_hash']}: `{art_ver.prompt_hash[:8]}…`")
    else:
        st.error(T["artifacts_missing"])

# ═══════════════════════════════════════════════════════════════════════════
#  INJECT THEME CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(GLASS_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ═══════════════════════════════════════════════════════════════════════════
st.title(T["main_title"])
st.caption(f"{T['main_subtitle']} | {T['session_label']}: `{st.session_state.transcript_id}`")

def get_avatar(role: str) -> str | None:
    if role == "assistant" and AVATAR_PATH.exists():
        return str(AVATAR_PATH)
    return None

for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant", avatar=get_avatar("assistant")):
        render_tool_traces(turn, T)
        display_text = parse_assistant_text(turn.get("assistant_text", ""))
        st.markdown(display_text)
        render_status_badge(turn.get("status", "answered"), T)

if user_input := st.chat_input(T["chat_placeholder"]):
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=get_avatar("assistant")):
        try:
            if demo_mode:
                result = get_mock_response(user_input)
            else:
                system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
                declarations = load_tool_declarations(TOOLS_PATH)
                openai_tools = to_openai_tools(declarations)
                
                # Hardcoded to openai as requested
                provider = make_provider("openai")

                messages = [
                    {"role": "system", "content": system_prompt},
                    *trim_history(st.session_state.history, history_window),
                    {"role": "user", "content": user_input},
                ]

                with st.spinner(T["processing"]):
                    result = run_model_tool_loop(
                        provider=provider,
                        messages=messages,
                        tools=openai_tools,
                        model=model_name,
                        max_tool_rounds=max_rounds,
                    )
        except Exception as exc:
            result = {
                "status": "provider_error",
                "assistant_text": f"**{T['provider_error']}**: `{type(exc).__name__}` — {exc}",
                "rounds": [],
                "tool_events": [],
            }

        render_tool_traces(result, T)
        display_text = parse_assistant_text(result.get("assistant_text", ""))
        st.markdown(display_text)
        render_status_badge(result.get("status", "answered"), T)

    turn_record = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_input,
        **result,
        "ended_at": now_iso(),
    }
    st.session_state.turns.append(turn_record)
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": result.get("assistant_text", "") or ""})

    if not TRANSCRIPTS_DIR.exists():
        TRANSCRIPTS_DIR.mkdir(parents=True)
    transcript_path = TRANSCRIPTS_DIR / f"{st.session_state.transcript_id}.transcript.json"
    write_transcript(transcript_path, transcript_data)

    st.rerun()

