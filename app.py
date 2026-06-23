import datetime as dt
import pandas as pd
import streamlit as st
import sheets_db as db

st.set_page_config(page_title="Naseem Iron Store",page_icon="ðŸ”©",layout="wide",initial_sidebar_state="expanded")

CSS = ("html,body,[class*='css']{font-family:'Segoe UI',Arial,sans-serif;}"
       ".block-container{padding-top:1rem;padding-bottom:2rem;}"
       ".banner{display:flex;align-items:center;gap:14px;background:linear-gradient(120deg,#0d1117,#1f2a38);"
       "border:1px solid #2a3a4a;border-radius:14px;padding:14px 22px;margin-bottom:1.4rem;"
       "box-shadow:0 4px 18px rgba(0,0,0,.45);}"
       ".b-title{font-size:1.5rem;font-weight:800;color:#f0f4f8;margin:0;}"
       ".b-sub{font-size:.78rem;color:#6e8499;margin:0;}"
       ".b-icon{width:42px;height:42px;background:#1f2e3d;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}"
       ".kcard{background:#141c26;border:1px solid #1f2e3d;border-radius:13px;padding:1rem 1.1rem;text-align:center;}"
       ".klbl{font-size:.78rem;color:#6e8499;margin-bottom:4px;}"
       ".kval{font-size:1.7rem;font-weight:900;}"
       ".green{color:#3ddc84;}.red{color:#ff6b6b;}.blue{color:#5b9bd5;}.white{color:#e8edf2;}"
       ".sec{font-size:.95rem;font-weight:700;color:#6e8499;border-left:4px solid #5b9bd5;padding-left:10px;margin:1rem 0 .6rem;}"
       ".panel{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:12px;}"
       ".bar-r{display:flex;align-items:center;gap:7px;padding:4px 0;}"
       ".bn{font-size:.82rem;color:#c8d6e0;min-width:120px;}"
       ".bt{flex:1;height:7px;background:#1a2535;border-radius:4px;overflow:hidden;}"
       ".bf{height:100%;border-radius:4px;}"
       ".bv{font-size:.82rem;font-weight:700;min-width:80px;text-align:right;}"
       ".pcard{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:10px 14px;margin-bottom:8px;}"
       ".pname{font-size:1rem;font-weight:700;color:#dce6f0;}"
       ".pph{font-size:.78rem;color:#4a
