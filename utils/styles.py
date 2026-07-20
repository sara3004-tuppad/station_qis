import streamlit as st


def inject_mobile_css():
    st.markdown(
        """
        <style>
        /* ── Viewport & base ───────────────────────────────────────────── */
        html, body, [data-testid="stAppViewContainer"] {
            max-width: 100%;
            overflow-x: hidden;
        }

        /* ── Main content padding ──────────────────────────────────────── */
        .block-container {
            padding: 1rem 1rem 2rem 1rem !important;
            max-width: 860px !important;
            margin: 0 auto !important;
        }

        /* ── Headings scale down on small screens ──────────────────────── */
        h1 { font-size: clamp(1.3rem, 5vw, 2rem) !important; }
        h2 { font-size: clamp(1.1rem, 4vw, 1.5rem) !important; }
        h3 { font-size: clamp(1rem, 3.5vw, 1.25rem) !important; }

        /* ── Inputs: larger touch targets ──────────────────────────────── */
        input, textarea, select,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input {
            font-size: 16px !important;   /* prevents iOS auto-zoom */
            min-height: 44px !important;
        }

        /* ── Selectbox & multiselect ───────────────────────────────────── */
        [data-testid="stSelectbox"] > div,
        [data-testid="stMultiSelect"] > div {
            min-height: 44px !important;
        }

        /* ── Buttons: full width on mobile, comfortable height ─────────── */
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stButton"] button {
            min-height: 48px !important;
            font-size: 1rem !important;
        }
        @media (max-width: 640px) {
            [data-testid="stFormSubmitButton"] button,
            [data-testid="stButton"] button {
                width: 100% !important;
            }
        }

        /* ── File uploader ─────────────────────────────────────────────── */
        [data-testid="stFileUploader"] {
            width: 100% !important;
        }
        [data-testid="stFileUploader"] section {
            padding: 1.2rem !important;
        }

        /* ── Columns: stack vertically below 640px ─────────────────────── */
        @media (max-width: 640px) {
            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
        }

        /* ── Tables: horizontal scroll on overflow ──────────────────────── */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
            width: 100% !important;
            display: block !important;
        }
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            width: 100% !important;
        }

        /* ── Sidebar: comfortable touch targets ────────────────────────── */
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stTextInput {
            margin-bottom: 0.75rem !important;
        }
        [data-testid="stSidebar"] label {
            font-size: 1rem !important;
        }

        /* ── Expander ──────────────────────────────────────────────────── */
        [data-testid="stExpander"] summary {
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
        }

        /* ── Info / success / warning banners ──────────────────────────── */
        [data-testid="stAlert"] {
            font-size: 0.95rem !important;
            padding: 0.75rem 1rem !important;
        }

        /* ── Form label spacing ─────────────────────────────────────────── */
        [data-testid="stForm"] label {
            font-size: 0.95rem !important;
            margin-bottom: 2px !important;
        }

        /* ── Divider breathing room ─────────────────────────────────────── */
        hr { margin: 1.5rem 0 !important; }

        /* ── Scrollable table wrapper ───────────────────────────────────── */
        .table-scroll {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            width: 100%;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
