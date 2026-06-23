"""
sheets_db.py â€” Naseem Iron Store | Google Sheets Database Layer
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

PARTIES_SHEET      = "Parties"
TRANSACTIONS_SHEET = "Transactions"


@st.cache_resource
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_spreadsheet():
    return get_client().open(st.secrets["spreadsheet"]["name"])


def get_sheet(name):
    ss = get_spreadsheet()
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=20)
        if name == PARTIES_SHEET:
            ws.append_row(["id","name","type","phone","address","created_at","status"])
        elif name == TRANSACTIONS_SHEET:
            ws.append_row(["id","party_id","txn_date","invoice_no",
                           "credit","debit","notes","created_at","status"])
        return ws


def _next_id(ws):
    rows = ws.get_all_values()
    return max(len(rows), 1)


# â”€â”€ Parties â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def add_party(name, type_, phone="", address=""):
    ws = get_sheet(PARTIES_SHEET)
    new_id = _next_id(ws)
    ws.append_row([
        new_id, name.strip(), type_,
        (phone or "").strip(), (address or "").strip(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active"
    ])
    return new_id


def get_all_parties(type_=None, search=None):
    ws   = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_records()
    out  = []
    for r in rows:
        if str(r.get("status","active")).upper
