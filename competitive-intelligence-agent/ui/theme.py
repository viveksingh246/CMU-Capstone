"""Design system — warm enterprise palette (gold / dark brown / cream / white)."""

DESIGN_REFERENCES = (
    "Gartner peer benchmarks · CB Insights market maps · AlphaSense research workspace"
)


def inject_global_styles() -> None:
  import streamlit as st

  st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,600&display=swap');

    :root {
      --ci-brown: #3D2914;
      --ci-brown-mid: #5C3D1E;
      --ci-brown-light: #7A6552;
      --ci-gold: #C8920A;
      --ci-gold-bright: #D4A017;
      --ci-gold-soft: #FFF8E7;
      --ci-amber: #F5B041;
      --ci-cream: #FAF6F0;
      --ci-cream-dark: #F5EDE0;
      --ci-surface: #FAF6F0;
      --ci-card: #FFFFFF;
      --ci-border: #E8DCC8;
      --ci-muted: #7A6552;
      --ci-text: #2C1810;
      --ci-success: #5D7A4A;
      --ci-warn: #D97706;
      --ci-danger: #A63D2F;
      --ci-radius: 10px;
      --ci-shadow: 0 1px 2px rgba(61, 41, 20, 0.06), 0 8px 24px rgba(61, 41, 20, 0.08);
      --ci-banner-height: 56px;
      /* Legacy aliases used across components */
      --ci-navy: var(--ci-brown);
      --ci-navy-mid: var(--ci-brown-mid);
      --ci-blue: var(--ci-gold);
      --ci-blue-soft: var(--ci-gold-soft);
      --ci-sky: var(--ci-amber);
    }

    html, body {
      height: auto !important;
      overflow-y: auto !important;
    }
    .stApp {
      background: linear-gradient(180deg, var(--ci-cream-dark) 0%, var(--ci-cream) 120px, var(--ci-cream) 100%);
      height: auto !important;
      min-height: 100vh !important;
      overflow-x: hidden !important;
      overflow-y: auto !important;
    }

    /* Hide default Streamlit header; custom sticky banner replaces it */
    header[data-testid="stHeader"] {
      display: none !important;
      height: 0 !important;
      min-height: 0 !important;
    }

    /* Banner offset — apply only to main pane so sidebar stays flush under title */
    [data-testid="stAppViewContainer"] {
      padding-top: 0 !important;
      margin-top: 0 !important;
      height: auto !important;
      min-height: 100vh !important;
      max-height: none !important;
      overflow: visible !important;
    }
    [data-testid="stAppViewContainer"] > section {
      margin-top: 0 !important;
      padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] {
      top: var(--ci-banner-height) !important;
      height: calc(100vh - var(--ci-banner-height)) !important;
      z-index: 999900 !important;
      margin-top: 0 !important;
      padding-top: 0 !important;
      overflow-y: auto !important;
      border-top: none !important;
    }
    [data-testid="stSidebarHeader"] {
      display: none !important;
      background: transparent !important;
      height: 0 !important;
      min-height: 0 !important;
      padding: 0 !important;
      margin: 0 !important;
      overflow: hidden !important;
    }
    [data-testid="stSidebarCollapseButton"] {
      position: fixed !important;
      top: calc(var(--ci-banner-height) * 0.5 - 0.75rem) !important;
      left: 0.35rem !important;
      z-index: 1000000 !important;
      color: #F5EDE0 !important;
      background: rgba(61, 41, 20, 0.35) !important;
      border-radius: 6px !important;
    }
    section[data-testid="stMain"] {
      padding-top: var(--ci-banner-height) !important;
      margin-top: 0 !important;
      height: auto !important;
      min-height: calc(100vh - var(--ci-banner-height)) !important;
      max-height: none !important;
      overflow: visible !important;
    }
    section[data-testid="stMain"] > div {
      height: auto !important;
      max-height: none !important;
      overflow: visible !important;
    }
    [data-testid="stMainBlockContainer"] {
      height: auto !important;
      max-height: none !important;
      overflow: visible !important;
    }
    section[data-testid="stMain"] .block-container {
      padding-top: 0.35rem !important;
      padding-bottom: 3rem !important;
      margin-top: 0 !important;
      height: auto !important;
      max-height: none !important;
      overflow: visible !important;
    }
    [data-testid="stMain"] [data-testid="stVerticalBlock"] {
      gap: 0.35rem !important;
    }

    /* Fixed top project banner */
    .ci-sticky-banner {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: var(--ci-banner-height);
      z-index: 999999;
      background: linear-gradient(135deg, #3D2914 0%, #5C3D1E 55%, #4A3318 100%);
      border-bottom: 2px solid rgba(212, 160, 23, 0.45);
      box-shadow: 0 4px 18px rgba(61, 41, 20, 0.22);
    }
    .ci-sticky-banner-inner {
      height: 100%;
      width: 100%;
      max-width: none;
      margin: 0;
      padding: 0 1rem 0 0.65rem;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 0.65rem;
      box-sizing: border-box;
    }
    .ci-sticky-brand {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      min-width: 0;
      flex: 0 1 auto;
      justify-content: flex-start;
      text-align: left;
    }
    .ci-logo-banner {
      width: 36px;
      height: 36px;
      flex-shrink: 0;
      padding: 0;
      background: transparent;
      box-shadow: none;
    }
    .ci-logo-svg {
      width: 100%;
      height: 100%;
      display: block;
      filter: drop-shadow(0 3px 8px rgba(61, 41, 20, 0.28));
    }
    .ci-sticky-titles {
      min-width: 0;
      text-align: left;
    }
    .ci-sticky-product-title {
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 0.95rem;
      font-weight: 700;
      font-style: normal;
      margin: 0;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: #7A1010;
      background: #FFFFFF;
      display: inline-block;
      padding: 0.15rem 0.5rem;
      line-height: 1.2;
      border-radius: 4px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
      text-align: left;
    }
    .ci-sticky-product-sub {
      font-size: 0.58rem;
      color: #E8DCC8;
      margin: 0.06rem 0 0;
      line-height: 1.1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: left;
    }
    .ci-sticky-badges {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 0.3rem;
      flex-shrink: 0;
      margin-left: auto;
    }
    .ci-sticky-badges .ci-badge {
      margin-left: 0;
    }
    @media (max-width: 900px) {
      :root { --ci-banner-height: 68px; }
      .ci-sticky-banner-inner {
        padding: 0 0.75rem 0 0.5rem;
        align-items: center;
      }
      .ci-sticky-product-sub { display: none; }
      .ci-sticky-product-title {
        font-size: 0.78rem;
        white-space: normal;
      }
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.ci-sticky-banner),
    [data-testid="stMain"] [data-testid="element-container"]:has(.ci-sticky-banner) {
      height: 0 !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: visible !important;
    }

    html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

    .block-container {
      padding: 0.35rem 1.25rem 3rem !important;
      max-width: 100% !important;
    }

    /* Sidebar — dark brown configuration console; seamless under banner */
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #3D2914 0%, #5C3D1E 100%) !important;
      border-right: none !important;
    }
    /* Left column under banner uses same tone so no cream seam appears */
    .stApp::before {
      content: "";
      position: fixed;
      top: 0;
      left: 0;
      width: var(--sidebar-width, 21rem);
      height: var(--ci-banner-height);
      background: linear-gradient(135deg, #3D2914 0%, #5C3D1E 55%, #4A3318 100%);
      border-bottom: 2px solid rgba(212, 160, 23, 0.45);
      z-index: 999998;
      pointer-events: none;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .ci-sidebar-section {
      color: #F5EDE0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stTextArea label,
    [data-testid="stSidebar"] .stMultiSelect label {
      color: #E8DCC8 !important;
      font-size: 0.68rem !important;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600 !important;
    }

    /* Sidebar inputs — white fields on dark brown (high contrast) */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
      background-color: #FFFFFF !important;
      color: #2C1810 !important;
      -webkit-text-fill-color: #2C1810 !important;
      caret-color: #2C1810 !important;
      border: 1px solid #E8DCC8 !important;
      border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="textarea"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="base-input"] {
      background-color: #FFFFFF !important;
      border: 1px solid #E8DCC8 !important;
      border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="textarea"] textarea {
      color: #2C1810 !important;
      -webkit-text-fill-color: #2C1810 !important;
      background-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
      color: #7A6552 !important;
      -webkit-text-fill-color: #7A6552 !important;
      opacity: 1 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tag"] {
      background-color: #FFF8E7 !important;
      color: #5C3D1E !important;
      border: 1px solid #E8C872 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tag"] span {
      color: #5C3D1E !important;
    }
    /* Sidebar checkbox labels — Pre-approve, Historical diff, Change alerts */
    [data-testid="stSidebar"] [data-testid="stCheckbox"] {
      color: #FFF8F0 !important;
    }
    [data-testid="stSidebar"] .stCheckbox label {
      color: #FFF8F0 !important;
    }
    [data-testid="stSidebar"] .stCheckbox label span,
    [data-testid="stSidebar"] .stCheckbox label p,
    [data-testid="stSidebar"] .stCheckbox label div,
    [data-testid="stSidebar"] .stCheckbox [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] .stCheckbox [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stCheckbox [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] .stCheckbox [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stCheckbox [data-testid="stMarkdownContainer"] span {
      color: #FFF8F0 !important;
      -webkit-text-fill-color: #FFF8F0 !important;
    }
    [data-testid="stSidebar"] .stCheckbox label:hover {
      color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stCheckbox label:hover span,
    [data-testid="stSidebar"] .stCheckbox label:hover p,
    [data-testid="stSidebar"] .stCheckbox label:hover [data-testid="stWidgetLabel"] {
      color: #FFFFFF !important;
      -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg {
      fill: #7A6552 !important;
    }

    [data-testid="stSidebar"] hr { border-color: rgba(255, 248, 231, 0.18) !important; margin: 1rem 0 !important; }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"],
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    [data-testid="stSidebar"] .block-container {
      padding-top: 0 !important;
      margin-top: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
      gap: 0.45rem !important;
      padding-top: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {
      margin-top: 0 !important;
      padding-top: 0 !important;
    }
    [data-testid="stSidebar"] .ci-sidebar-section {
      margin-top: 0.2rem !important;
      margin-bottom: 0.25rem !important;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #C8920A, #F5B041) !important;
      color: #2C1810 !important;
      border: none !important;
      font-weight: 600 !important;
    }

    /* Top command bar */
    .ci-topbar {
      background: linear-gradient(135deg, var(--ci-brown) 0%, var(--ci-brown-mid) 100%);
      border-radius: var(--ci-radius);
      padding: 1.25rem 1.5rem;
      margin: 0.5rem 0 1.25rem;
      box-shadow: var(--ci-shadow);
      color: #FFF8F0;
      border: 1px solid rgba(232, 200, 114, 0.2);
    }
    .ci-brand { display: flex; align-items: center; gap: 0.75rem; }
    .ci-logo {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      padding: 0;
      background: transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: none;
    }
    .ci-product-title {
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 1.72rem;
      font-weight: 700;
      font-style: normal;
      margin: 0;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: #7A1010;
      background: #FFFFFF;
      display: inline-block;
      padding: 0.25rem 0.65rem;
      line-height: 1.3;
      border-radius: 4px;
    }
    .ci-product-sub { font-size: 0.8rem; color: #E8DCC8; margin: 0.15rem 0 0; }
    .ci-ref-line { font-size: 0.65rem; color: #C4A882; margin-top: 0.35rem; letter-spacing: 0.04em; text-transform: uppercase; }

    .ci-badge {
      display: inline-flex; align-items: center; gap: 0.25rem;
      font-size: 0.62rem; font-weight: 600; padding: 0.2rem 0.55rem;
      border-radius: 999px; margin-left: 0.35rem; letter-spacing: 0.06em;
      text-transform: uppercase; vertical-align: middle;
    }
    .ci-badge-ok { background: rgba(93, 122, 74, 0.2); color: #B8D4A8; border: 1px solid rgba(93, 122, 74, 0.4); }
    .ci-badge-warn { background: rgba(245, 176, 65, 0.2); color: #FDE68A; border: 1px solid rgba(245, 176, 65, 0.4); }
    .ci-badge-err { background: rgba(166, 61, 47, 0.2); color: #FCA5A5; border: 1px solid rgba(166, 61, 47, 0.4); }

    /* Scope strip */
    .ci-scope-card {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
      box-shadow: var(--ci-shadow);
    }
    .ci-scope-label { font-size: 0.65rem; font-weight: 600; color: var(--ci-muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem; }
    .ci-scope-title { font-size: 1.05rem; font-weight: 600; color: var(--ci-text); margin: 0; }
    .ci-chip-row { margin-top: 0.6rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .ci-chip {
      display: inline-block; font-size: 0.72rem; font-weight: 500;
      padding: 0.25rem 0.65rem; border-radius: 999px;
      background: var(--ci-gold-soft); color: #5C3D1E; border: 1px solid #E8C872;
    }
    .ci-chip-muted { background: var(--ci-cream-dark); color: #5C3D1E; border-color: var(--ci-border); }
    .ci-meta { font-size: 0.75rem; color: var(--ci-muted); margin-top: 0.5rem; }

    /* KPI cards */
    .ci-kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.65rem; margin: 0 0 1rem; }
    @media (max-width: 1100px) { .ci-kpi-grid { grid-template-columns: repeat(3, 1fr); } }
    .ci-kpi {
      background: var(--ci-card); border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius); padding: 0.85rem 1rem;
      box-shadow: var(--ci-shadow); position: relative; overflow: hidden;
    }
    .ci-kpi::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--ci-gold), var(--ci-amber));
    }
    .ci-kpi-label { font-size: 0.65rem; font-weight: 600; color: var(--ci-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .ci-kpi-value { font-size: 1.35rem; font-weight: 700; color: var(--ci-text); margin-top: 0.15rem; }

    /* Report document panel */
    .ci-report-panel {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-left: 4px solid var(--ci-gold);
      border-radius: var(--ci-radius);
      padding: 1.5rem 1.75rem;
      box-shadow: var(--ci-shadow);
      margin-bottom: 1rem;
    }
    .ci-report-header {
      font-family: 'Source Serif 4', Georgia, serif;
      font-size: 1.1rem; font-weight: 600; color: var(--ci-brown);
      margin: 0 0 0.75rem; padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--ci-border);
    }

    /* Review banner */
    .ci-review-banner {
      background: linear-gradient(90deg, #FFF8E7, #FEF3C7);
      border: 1px solid #E8C872;
      border-radius: var(--ci-radius);
      padding: 1rem 1.25rem;
      margin-bottom: 1rem;
    }
    .ci-review-title { font-weight: 600; color: #5C3D1E; font-size: 0.9rem; margin: 0; }
    .ci-review-sub { font-size: 0.78rem; color: #7A6552; margin: 0.25rem 0 0; }

    /* Empty state */
    .ci-empty {
      text-align: center; padding: 3rem 2rem;
      background: var(--ci-card); border: 1px dashed var(--ci-border);
      border-radius: var(--ci-radius); margin: 1rem 0;
    }
    .ci-empty h3 { font-family: 'Source Serif 4', Georgia, serif; color: var(--ci-brown); margin: 0 0 0.5rem; }
    .ci-empty p { color: var(--ci-muted); font-size: 0.85rem; max-width: 520px; margin: 0 auto; line-height: 1.6; }
    .ci-steps { display: flex; justify-content: center; gap: 1.5rem; margin-top: 1.5rem; flex-wrap: wrap; }
    .ci-step { text-align: left; max-width: 160px; }
    .ci-step-num {
      width: 28px; height: 28px; border-radius: 50%;
      background: var(--ci-gold-soft); color: var(--ci-gold);
      font-weight: 700; font-size: 0.8rem;
      display: flex; align-items: center; justify-content: center; margin-bottom: 0.4rem;
    }
    .ci-step-title { font-size: 0.78rem; font-weight: 600; color: var(--ci-text); }
    .ci-step-desc { font-size: 0.7rem; color: var(--ci-muted); margin-top: 0.15rem; }

    /* Section headers */
    .ci-section {
      font-size: 0.7rem; font-weight: 700; color: var(--ci-muted);
      text-transform: uppercase; letter-spacing: 0.1em;
      margin: 1.25rem 0 0.65rem; padding-bottom: 0.35rem;
      border-bottom: 2px solid var(--ci-border);
    }

    /* Sidebar section labels */
    .ci-sidebar-section {
      font-size: 0.62rem; font-weight: 700; color: #C4A882 !important;
      text-transform: uppercase; letter-spacing: 0.12em;
      margin: 0.5rem 0 0.35rem;
    }
    .ci-sidebar-checkbox-label {
      font-size: 0.82rem !important;
      font-weight: 500 !important;
      color: #FFF8F0 !important;
      margin: 0 0 0.15rem !important;
      line-height: 1.3 !important;
    }
    .ci-sidebar-checkbox-inline {
      margin: 0 !important;
      padding: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="column"] [data-testid="stCheckbox"] {
      margin-bottom: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="column"] [data-testid="stCheckbox"] > label {
      min-height: 1.1rem !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="column"] [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] {
      display: none !important;
    }
    [data-testid="stSidebar"] .ci-sidebar-checkbox-label + div [data-testid="stCheckbox"],
    [data-testid="stSidebar"] .ci-sidebar-checkbox-label + div .stCheckbox {
      margin-top: -0.1rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
      gap: 0; background: transparent; border-bottom: 2px solid var(--ci-border);
    }
    .stTabs [data-baseweb="tab"] {
      font-size: 0.78rem; font-weight: 600; color: var(--ci-muted);
      padding: 0.65rem 1.1rem; border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
      color: var(--ci-gold) !important;
      background: var(--ci-card) !important;
      border: 1px solid var(--ci-border) !important;
      border-bottom-color: var(--ci-card) !important;
    }

    /* Metrics override */
    [data-testid="stMetric"] {
      background: var(--ci-card) !important;
      border: 1px solid var(--ci-border) !important;
      border-radius: var(--ci-radius) !important;
      padding: 0.75rem !important;
      box-shadow: var(--ci-shadow) !important;
    }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ci-muted) !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; font-weight: 700 !important; color: var(--ci-brown) !important; }

    /* Chart cards */
    .ci-chart-card {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      padding: 0.5rem 0.75rem 0;
      box-shadow: var(--ci-shadow);
      margin-bottom: 0.75rem;
    }

    /* Memory table */
    .ci-run-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.65rem 0; border-bottom: 1px solid var(--ci-border);
      font-size: 0.8rem;
    }
    .ci-run-id { font-weight: 600; color: var(--ci-gold); }
    .ci-run-date { color: var(--ci-muted); font-size: 0.72rem; }

    /* About capability cards */
    .ci-cap-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
    @media (max-width: 900px) { .ci-cap-grid { grid-template-columns: 1fr; } }
    .ci-cap-card {
      background: var(--ci-card); border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius); padding: 1rem 1.1rem;
      box-shadow: var(--ci-shadow);
    }
    .ci-cap-title { font-weight: 600; font-size: 0.85rem; color: var(--ci-brown); margin: 0 0 0.35rem; }
    .ci-cap-desc { font-size: 0.75rem; color: var(--ci-muted); margin: 0; line-height: 1.5; }

    div[data-testid="stExpander"] {
      background: var(--ci-card) !important;
      border: 1px solid var(--ci-border) !important;
      border-radius: var(--ci-radius) !important;
      box-shadow: var(--ci-shadow) !important;
    }

    /* Pipeline progress tracker — horizontal phase rail */
    .ci-pipeline-panel {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      padding: 0.85rem 1rem 1rem;
      box-shadow: var(--ci-shadow);
      margin: 0.5rem 0 0.85rem;
      width: 100%;
      box-sizing: border-box;
    }
    [data-testid="stVerticalBlockBorderWrapper"] .ci-pipeline-title,
    [data-testid="stVerticalBlockBorderWrapper"] .ci-pipeline-running,
    [data-testid="stVerticalBlockBorderWrapper"] .ci-h-phase,
    [data-testid="stVerticalBlockBorderWrapper"] .ci-h-current {
      margin-bottom: 0;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.ci-pipeline-title) {
      width: 100% !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.ci-pipeline-title) .ci-pipeline-title {
      margin-bottom: 0.65rem;
    }
    .ci-pipeline-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.25rem;
      flex-wrap: wrap;
    }
    .ci-pipeline-title {
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--ci-muted);
      margin: 0;
    }
    .ci-pipeline-running {
      display: inline-flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.45rem;
      font-size: 0.72rem;
      color: var(--ci-gold);
      font-weight: 600;
      margin: 0;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      width: 100%;
    }
    .ci-pipeline-running-dot {
      width: 0.55rem;
      height: 0.55rem;
      border-radius: 50%;
      background: var(--ci-gold);
      animation: ci-dot-blink 1.1s ease-in-out infinite;
      flex-shrink: 0;
    }
    .ci-h-progress-bar {
      width: 100%;
      height: 4px;
      background: var(--ci-border);
      border-radius: 999px;
      overflow: hidden;
      margin: 0.1rem 0 0.75rem;
    }
    .ci-h-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--ci-success), var(--ci-gold));
      border-radius: 999px;
      transition: width 0.35s ease;
    }
    .ci-h-phases {
      display: flex;
      justify-content: space-between;
      gap: 0.5rem;
      width: 100%;
    }
    .ci-h-phase {
      flex: 1 1 0;
      min-width: 0;
      text-align: center;
      padding: 0 0.1rem;
      box-sizing: border-box;
    }
    .ci-h-dot-wrap {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 1.35rem;
      margin-bottom: 0.2rem;
    }
    .ci-h-dot {
      display: inline-block;
      width: 0.9rem;
      height: 0.9rem;
      border-radius: 50%;
      background: var(--ci-card);
      border: 2px solid var(--ci-border);
      box-sizing: border-box;
      flex-shrink: 0;
    }
    .ci-h-phase-complete .ci-h-dot {
      background: var(--ci-success);
      border-color: var(--ci-success);
    }
    .ci-h-phase-active .ci-h-dot {
      background: var(--ci-gold);
      border-color: var(--ci-gold-bright);
      animation: ci-dot-blink 1.1s ease-in-out infinite;
    }
    @keyframes ci-dot-blink {
      0%, 100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 0 4px rgba(200, 146, 10, 0.28);
      }
      50% {
        opacity: 0.55;
        transform: scale(0.92);
        box-shadow: 0 0 0 9px rgba(200, 146, 10, 0.08);
      }
    }
    .ci-h-phase-num {
      font-size: 0.58rem;
      font-weight: 700;
      color: var(--ci-muted);
      margin: 0;
      line-height: 1;
      white-space: nowrap;
      letter-spacing: 0;
      text-transform: none;
    }
    .ci-h-phase-title {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--ci-text);
      margin: 0.15rem 0 0;
      line-height: 1.15;
      word-break: keep-all;
      overflow-wrap: normal;
    }
    .ci-h-phase-active .ci-h-phase-num,
    .ci-h-phase-active .ci-h-phase-title {
      color: var(--ci-gold);
    }
    .ci-h-phase-pending .ci-h-phase-title {
      color: var(--ci-muted);
    }
    .ci-h-current {
      margin-top: 0.85rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: var(--ci-gold-soft);
      border: 1px solid #E8C872;
      font-size: 0.78rem;
      line-height: 1.45;
      color: var(--ci-brown-mid);
      width: 100%;
      box-sizing: border-box;
    }
    .ci-h-current-top {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 0.35rem 0.55rem;
    }
    .ci-h-current-label {
      font-size: 0.62rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--ci-gold);
      flex-shrink: 0;
    }
    .ci-h-current-step {
      font-weight: 600;
      color: var(--ci-text);
      flex: 1 1 auto;
      min-width: 0;
    }
    .ci-h-current-detail {
      color: var(--ci-muted);
      font-size: 0.74rem;
      margin: 0.4rem 0 0;
      line-height: 1.4;
      width: 100%;
    }

    /* Legacy rail/track (replaced by progress bar + columns) */
    .ci-h-rail,
    .ci-h-track {
      display: none;
    }

    /* Legacy vertical step list (unused) */
    .ci-pipeline-step {
      display: none;
    }

    .stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #B8860B, #D4A017) !important;
      color: #2C1810 !important;
      border: none !important;
      font-weight: 600 !important;
      border-radius: 8px !important;
      box-shadow: 0 4px 14px rgba(200, 146, 10, 0.3) !important;
    }
    .stButton > button[kind="secondary"] {
      border-radius: 8px !important;
      border: 1px solid var(--ci-border) !important;
      font-weight: 500 !important;
      color: var(--ci-brown) !important;
      background: var(--ci-card) !important;
    }

    /* Engagement header */
    .ci-engagement-header {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-left: 4px solid var(--ci-gold);
      border-radius: var(--ci-radius);
      padding: 1rem 1.25rem;
      margin: 0 0 1rem;
      box-shadow: var(--ci-shadow);
    }
    .ci-engagement-label {
      font-size: 0.62rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--ci-muted);
      margin: 0 0 0.35rem;
    }
    .ci-engagement-title {
      font-family: 'Source Serif 4', Georgia, serif;
      font-size: 1.45rem;
      font-weight: 600;
      color: var(--ci-brown);
      margin: 0;
      line-height: 1.25;
    }
    .ci-engagement-sub {
      font-size: 0.9rem;
      color: var(--ci-text);
      margin: 0.35rem 0 0;
    }
    .ci-engagement-meta {
      font-size: 0.75rem;
      color: var(--ci-muted);
      margin: 0.45rem 0 0;
    }

    /* Phase rail */
    .ci-phase-rail {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.5rem;
      margin: 0 0 1rem;
    }
    @media (max-width: 900px) { .ci-phase-rail { grid-template-columns: 1fr; } }
    .ci-phase-rail-item {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      padding: 0.65rem 0.75rem;
      box-shadow: var(--ci-shadow);
    }
    .ci-phase-num {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--ci-cream-dark);
      color: var(--ci-brown);
      font-size: 0.68rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 0.35rem;
    }
    .ci-phase-title {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--ci-text);
      line-height: 1.35;
    }
    .ci-phase-complete { border-color: #C4D4B8; }
    .ci-phase-complete .ci-phase-num { background: #E8F0E4; color: var(--ci-success); }
    .ci-phase-active { border-color: var(--ci-gold); box-shadow: 0 0 0 2px rgba(200, 146, 10, 0.15); }
    .ci-phase-active .ci-phase-num { background: var(--ci-gold-soft); color: var(--ci-gold); }
    .ci-phase-pending { opacity: 0.72; }

    /* Activity feed */
    .ci-activity-feed {
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      box-shadow: var(--ci-shadow);
      max-height: 420px;
      overflow-y: auto;
    }
    .ci-feed-row {
      padding: 0.7rem 0.9rem;
      border-bottom: 1px solid var(--ci-border);
    }
    .ci-feed-row:last-child { border-bottom: none; }
    .ci-feed-head {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 0.25rem;
    }
    .ci-feed-agent {
      font-size: 0.62rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--ci-gold);
    }
    .ci-feed-ts {
      font-size: 0.62rem;
      color: var(--ci-muted);
    }
    .ci-feed-badge {
      font-size: 0.58rem;
      font-weight: 600;
      padding: 0.12rem 0.45rem;
      border-radius: 999px;
      margin-left: auto;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .ci-feed-badge-ok { background: #E8F0E4; color: var(--ci-success); }
    .ci-feed-badge-active { background: var(--ci-gold-soft); color: #8B6914; }
    .ci-feed-badge-warn { background: #FFF8E7; color: var(--ci-warn); }
    .ci-feed-badge-err { background: #FCEAE8; color: var(--ci-danger); }
    .ci-feed-badge-info { background: var(--ci-cream-dark); color: var(--ci-brown); }
    .ci-feed-title {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--ci-text);
      margin: 0;
      line-height: 1.35;
    }
    .ci-feed-detail {
      font-size: 0.72rem;
      color: var(--ci-muted);
      margin: 0.2rem 0 0;
      line-height: 1.45;
    }

    /* Comparison tables */
    .ci-data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.78rem;
      margin: 0.35rem 0 1rem;
      background: var(--ci-card);
      border: 1px solid var(--ci-border);
      border-radius: var(--ci-radius);
      overflow: hidden;
      box-shadow: var(--ci-shadow);
    }
    .ci-data-table th {
      background: var(--ci-cream-dark);
      color: var(--ci-brown);
      font-weight: 600;
      text-align: left;
      padding: 0.55rem 0.75rem;
      border-bottom: 1px solid var(--ci-border);
    }
    .ci-data-table td {
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid var(--ci-border);
      color: var(--ci-text);
      vertical-align: top;
    }
    .ci-data-table tr:last-child td { border-bottom: none; }

    div[data-testid="stRadio"] > div {
      gap: 0.35rem !important;
      flex-wrap: wrap !important;
    }
    div[data-testid="stRadio"] label {
      background: var(--ci-card) !important;
      border: 1px solid var(--ci-border) !important;
      border-radius: 999px !important;
      padding: 0.25rem 0.7rem !important;
      font-size: 0.72rem !important;
      font-weight: 600 !important;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
  )
