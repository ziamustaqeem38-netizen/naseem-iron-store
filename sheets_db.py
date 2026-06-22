"""
sheets_db.py — Naseem Iron Store | Google Sheets Database Layer
Data is NEVER deleted. Only new rows are appended.
"""

import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet names (tabs)
PARTIES_SHEET    = "Parties"
TRANSACTIONS_SHEET = "Transactions"


@st.cache_resource
def get_client():
    """Connect to Google Sheets using credentials from Streamlit secrets."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_spreadsheet():
    client = get_client()
    return client.open(st.secrets["spreadsheet"]["name"])


def get_sheet(name):
    ss = get_spreadsheet()
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=1000, cols=20)
        # Add headers
        if name == PARTIES_SHEET:
            ws.append_row(["id","name","type","phone","address","created_at"])
        elif name == TRANSACTIONS_SHEET:
            ws.append_row(["id","party_id","txn_date","invoice_no",
                           "credit","debit","notes","created_at"])
        return ws


def _next_id(ws):
    """Get next auto-increment ID."""
    rows = ws.get_all_values()
    if len(rows) <= 1:
        return 1
    return len(rows)  # header + data rows = next id


# ── Parties ──────────────────────────────────────────────────────────────────

def add_party(name, type_, phone="", address=""):
    ws = get_sheet(PARTIES_SHEET)
    new_id = _next_id(ws)
    ws.append_row([
        new_id,
        name.strip(),
        type_,
        (phone or "").strip(),
        (address or "").strip(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])
    return new_id


def get_all_parties(type_=None, search=None):
    ws = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_records()
    parties = []
    for r in rows:
        if type_ and r.get("type") != type_:
            continue
        if search and search.lower() not in r.get("name","").lower():
            continue
        parties.append(r)
    return parties


def get_party_by_id(party_id):
    ws = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_records()
    for r in rows:
        if str(r.get("id")) == str(party_id):
            return r
    return None


# ── Transactions ─────────────────────────────────────────────────────────────

def add_transaction(party_id, txn_date, invoice_no, credit, debit, notes=""):
    try:
        credit = float(credit or 0)
        debit  = float(debit  or 0)
    except (TypeError, ValueError):
        return None
    if credit == 0 and debit == 0:
        return None
    ws = get_sheet(TRANSACTIONS_SHEET)
    new_id = _next_id(ws)
    ws.append_row([
        new_id,
        party_id,
        str(txn_date),
        (invoice_no or "").strip(),
        credit,
        debit,
        (notes or "").strip(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])
    return new_id


def get_party_transactions(party_id):
    ws = get_sheet(TRANSACTIONS_SHEET)
    rows = ws.get_all_records()
    txns = [r for r in rows if str(r.get("party_id")) == str(party_id)]
    txns.sort(key=lambda x: (str(x.get("txn_date","")), int(x.get("id",0))))
    running = 0.0
    for t in txns:
        running += float(t.get("credit",0)) - float(t.get("debit",0))
        t["balance"] = running
    return txns


def get_all_transactions():
    ws = get_sheet(TRANSACTIONS_SHEET)
    return ws.get_all_records()


# ── Computed summaries ────────────────────────────────────────────────────────

def get_party_summary(party_id):
    txns = get_party_transactions(party_id)
    total_cr = sum(float(t.get("credit",0)) for t in txns)
    total_dr = sum(float(t.get("debit",0))  for t in txns)
    balance  = total_cr - total_dr
    last_inv  = txns[-1].get("invoice_no","—") if txns else "—"
    last_date = txns[-1].get("txn_date","—")   if txns else "—"
    return {
        "total_credit": total_cr,
        "total_debit":  total_dr,
        "balance":      balance,
        "last_invoice": last_inv or "—",
        "last_date":    last_date or "—",
    }


def get_dashboard_totals():
    all_txns    = get_all_transactions()
    all_parties = get_all_parties()

    party_map = {str(p["id"]): p for p in all_parties}

    totals = {}
    for t in all_txns:
        pid = str(t.get("party_id",""))
        if pid not in totals:
            totals[pid] = {"credit": 0, "debit": 0}
        totals[pid]["credit"] += float(t.get("credit", 0))
        totals[pid]["debit"]  += float(t.get("debit",  0))

    clients   = [p for p in all_parties if p["type"] == "client"]
    suppliers = [p for p in all_parties if p["type"] == "supplier"]

    def bal(pid):
        d = totals.get(str(pid), {"credit":0,"debit":0})
        return d["credit"] - d["debit"]

    total_recv = sum(max(bal(c["id"]),0) for c in clients)
    total_pay  = sum(max(bal(s["id"]),0) for s in suppliers)

    top_clients = sorted(
        [{"name":c["name"],"balance":bal(c["id"])} for c in clients],
        key=lambda x: x["balance"], reverse=True
    )[:5]
    top_suppliers = sorted(
        [{"name":s["name"],"balance":bal(s["id"])} for s in suppliers],
        key=lambda x: x["balance"], reverse=True
    )[:5]

    return {
        "total_receivables": total_recv,
        "total_payables":    total_pay,
        "net_position":      total_recv - total_pay,
        "client_count":      len(clients),
        "supplier_count":    len(suppliers),
        "top_clients":       top_clients,
        "top_suppliers":     top_suppliers,
    }


def get_report(period="monthly", type_=None):
    import datetime as dt
    today = dt.date.today()
    if period == "weekly":
        cutoff = (today - dt.timedelta(days=7)).isoformat()
    elif period == "monthly":
        cutoff = today.replace(day=1).isoformat()
    else:
        cutoff = "0000-01-01"

    all_txns    = get_all_transactions()
    all_parties = get_all_parties(type_=type_)
    party_map   = {str(p["id"]): p for p in all_parties}

    summary = {}
    for t in all_txns:
        pid = str(t.get("party_id",""))
        if pid not in party_map:
            continue
        if str(t.get("txn_date","")) < cutoff:
            continue
        if pid not in summary:
            summary[pid] = {"credit":0,"debit":0,"txn_count":0,
                            "name": party_map[pid]["name"],
                            "type": party_map[pid]["type"]}
        summary[pid]["credit"]    += float(t.get("credit",0))
        summary[pid]["debit"]     += float(t.get("debit",0))
        summary[pid]["txn_count"] += 1

    result = []
    for pid, d in summary.items():
        d["balance"] = d["credit"] - d["debit"]
        result.append(d)
    return sorted(result, key=lambda x: x["balance"], reverse=True)
