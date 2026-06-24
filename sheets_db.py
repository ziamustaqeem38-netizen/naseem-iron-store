
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


# ── Parties ───────────────────────────────────────────────────────────────────

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
        if str(r.get("status","active")).upper() == "DELETED":
            continue
        if type_ and r.get("type") != type_:
            continue
        if search and search.lower() not in r.get("name","").lower():
            continue
        out.append(r)
    return out


def get_party_by_id(party_id):
    ws   = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_records()
    for r in rows:
        if str(r.get("id")) == str(party_id):
            return r
    return None


def update_party(party_id, name, phone, address):
    """Edit party name / phone / address."""
    ws   = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if str(row[0]) == str(party_id):
            ws.update(f"B{i}:E{i}", [[
                name.strip(),
                row[2],               # keep type unchanged
                (phone or "").strip(),
                (address or "").strip()
            ]])
            return True
    return False


def delete_party(party_id):
    """Soft-delete: mark status=DELETED (row stays, data safe)."""
    ws   = get_sheet(PARTIES_SHEET)
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if str(row[0]) == str(party_id):
            col_g = 7          # column G = status
            ws.update_cell(i, col_g, "DELETED")
            return True
    return False


# ── Transactions ──────────────────────────────────────────────────────────────

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
        new_id, party_id, str(txn_date),
        (invoice_no or "").strip(),
        credit, debit, (notes or "").strip(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active"
    ])
    return new_id


def update_transaction(txn_id, txn_date, invoice_no, credit, debit, notes=""):
    """Edit an existing transaction."""
    try:
        credit = float(credit or 0)
        debit  = float(debit  or 0)
    except (TypeError, ValueError):
        return False
    ws   = get_sheet(TRANSACTIONS_SHEET)
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if str(row[0]) == str(txn_id):
            ws.update(f"C{i}:G{i}", [[
                str(txn_date),
                (invoice_no or "").strip(),
                credit, debit,
                (notes or "").strip()
            ]])
            return True
    return False


def delete_transaction(txn_id):
    """Soft-delete: zero credit/debit and mark DELETED."""
    ws   = get_sheet(TRANSACTIONS_SHEET)
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if str(row[0]) == str(txn_id):
            ws.update(f"E{i}:I{i}", [[0, 0, "DELETED", row[7] if len(row)>7 else "", "DELETED"]])
            return True
    return False


def get_party_transactions(party_id):
    ws   = get_sheet(TRANSACTIONS_SHEET)
    rows = ws.get_all_records()
    txns = []
    for r in rows:
        if str(r.get("party_id")) != str(party_id):
            continue
        if str(r.get("status","active")).upper() == "DELETED":
            continue
        txns.append(r)
    txns.sort(key=lambda x: (str(x.get("txn_date","")), int(x.get("id",0))))
    running = 0.0
    for t in txns:
        running += float(t.get("credit",0)) - float(t.get("debit",0))
        t["balance"] = running
    return txns


def get_all_transactions():
    ws = get_sheet(TRANSACTIONS_SHEET)
    return [r for r in ws.get_all_records()
            if str(r.get("status","active")).upper() != "DELETED"]


# ── Summaries ─────────────────────────────────────────────────────────────────

def get_party_summary(party_id):
    txns     = get_party_transactions(party_id)
    total_cr = sum(float(t.get("credit",0)) for t in txns)
    total_dr = sum(float(t.get("debit",0))  for t in txns)
    last_inv  = txns[-1].get("invoice_no","—") if txns else "—"
    last_date = txns[-1].get("txn_date","—")   if txns else "—"
    return {
        "total_credit": total_cr,
        "total_debit":  total_dr,
        "balance":      total_cr - total_dr,
        "last_invoice": last_inv  or "—",
        "last_date":    last_date or "—",
    }


def get_dashboard_totals():
    all_txns    = get_all_transactions()
    all_parties = get_all_parties()
    totals = {}
    for t in all_txns:
        pid = str(t.get("party_id",""))
        if pid not in totals:
            totals[pid] = {"credit":0,"debit":0}
        totals[pid]["credit"] += float(t.get("credit",0))
        totals[pid]["debit"]  += float(t.get("debit",0))

    clients   = [p for p in all_parties if p["type"]=="client"]
    suppliers = [p for p in all_parties if p["type"]=="supplier"]

    def bal(pid):
        d = totals.get(str(pid),{"credit":0,"debit":0})
        return d["credit"]-d["debit"]

    return {
        "total_receivables": sum(max(bal(c["id"]),0) for c in clients),
        "total_payables":    sum(max(bal(s["id"]),0) for s in suppliers),
        "net_position":      sum(max(bal(c["id"]),0) for c in clients)
                           - sum(max(bal(s["id"]),0) for s in suppliers),
        "client_count":      len(clients),
        "supplier_count":    len(suppliers),
        "top_clients":       sorted([{"name":c["name"],"balance":bal(c["id"])} for c in clients],
                                    key=lambda x:x["balance"],reverse=True)[:5],
        "top_suppliers":     sorted([{"name":s["name"],"balance":bal(s["id"])} for s in suppliers],
                                    key=lambda x:x["balance"],reverse=True)[:5],
    }


def get_report(period="monthly", type_=None):
    import datetime as dt
    today = dt.date.today()
    cutoff = {"weekly":(today-dt.timedelta(days=7)).isoformat(),
              "monthly":today.replace(day=1).isoformat()}.get(period,"0000-01-01")

    all_txns    = get_all_transactions()
    all_parties = get_all_parties(type_=type_)
    party_map   = {str(p["id"]):p for p in all_parties}
    summary     = {}
    for t in all_txns:
        pid = str(t.get("party_id",""))
        if pid not in party_map or str(t.get("txn_date","")) < cutoff:
            continue
        if pid not in summary:
            summary[pid] = {"credit":0,"debit":0,"txn_count":0,
                            "name":party_map[pid]["name"],
                            "type":party_map[pid]["type"]}
        summary[pid]["credit"]    += float(t.get("credit",0))
        summary[pid]["debit"]     += float(t.get("debit",0))
        summary[pid]["txn_count"] += 1
    result = [dict(d, balance=d["credit"]-d["debit"]) for d in summary.values()]
    return sorted(result, key=lambda x:x["balance"], reverse=True)


# ── Daily Cash ────────────────────────────────────────────────────────────────

def get_daily_cash(date_str):
    all_txns    = get_all_transactions()
    all_parties = get_all_parties()
    party_map   = {str(p["id"]): p["name"] for p in all_parties}

    day_txns = [t for t in all_txns if str(t.get("txn_date","")) == date_str]
    for t in day_txns:
        t["party_name"] = party_map.get(str(t.get("party_id","")), "—")

    total_cr = sum(float(t.get("credit",0)) for t in day_txns)
    total_dr = sum(float(t.get("debit",0))  for t in day_txns)
    return {
        "total_credit":  total_cr,
        "total_debit":   total_dr,
        "net":           total_cr - total_dr,
        "transactions":  day_txns,
    }


# ── Monthly Chart ─────────────────────────────────────────────────────────────

def get_monthly_chart_data():
    import datetime as dt
    all_txns = get_all_transactions()
    monthly  = {}
    for t in all_txns:
        d = str(t.get("txn_date",""))
        if len(d) < 7:
            continue
        month = d[:7]   # "2026-06"
        if month not in monthly:
            monthly[month] = {"credit":0,"debit":0,"count":0}
        monthly[month]["credit"] += float(t.get("credit",0))
        monthly[month]["debit"]  += float(t.get("debit",0))
        monthly[month]["count"]  += 1

    result = []
    for m in sorted(monthly.keys())[-6:]:
        result.append({
            "month":  m,
            "credit": monthly[m]["credit"],
            "debit":  monthly[m]["debit"],
            "count":  monthly[m]["count"],
        })
    return result


# ── Search Transactions ───────────────────────────────────────────────────────

def search_transactions(query, txn_type=None):
    all_txns    = get_all_transactions()
    all_parties = get_all_parties()
    party_map   = {str(p["id"]): p["name"] for p in all_parties}
    query       = query.strip().lower()
    results     = []
    for t in all_txns:
        inv   = str(t.get("invoice_no","")).lower()
        notes = str(t.get("notes","")).lower()
        if query not in inv and query not in notes:
            continue
        if txn_type == "credit" and float(t.get("credit",0)) <= 0:
            continue
        if txn_type == "debit"  and float(t.get("debit",0))  <= 0:
            continue
        t["party_name"] = party_map.get(str(t.get("party_id","")), "—")
        results.append(t)
    return results


# ── Overdue Clients ───────────────────────────────────────────────────────────

def get_overdue_clients():
    import datetime as dt
    today      = dt.date.today()
    cutoff     = (today - dt.timedelta(days=30)).isoformat()
    clients    = get_all_parties("client")
    overdue    = []
    for c in clients:
        txns = get_party_transactions(c["id"])
        if not txns:
            continue
        balance = txns[-1]["balance"] if txns else 0
        if balance <= 0:
            continue
        last_payment = None
        for t in reversed(txns):
            if float(t.get("debit",0)) > 0:
                last_payment = str(t.get("txn_date",""))
                break
        if last_payment is None or last_payment < cutoff:
            overdue.append({
                "name":      c["name"],
                "balance":   balance,
                "last_date": last_payment or "Never",
            })
    return overdue


# ── Opening Balance ───────────────────────────────────────────────────────────

def add_opening_balance(party_id, amount, balance_type, date_str, notes="Opening Balance"):
    """
    balance_type: 'receivable' (client owes us) or 'payable' (we owe supplier)
    receivable = Credit entry
    payable    = Debit entry (we owe them)
    """
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    is_credit = balance_type == "receivable"
    return add_transaction(
        party_id   = party_id,
        txn_date   = date_str,
        invoice_no = "OB",
        credit     = amount if is_credit else 0,
        debit      = amount if not is_credit else 0,
        notes      = notes or "Opening Balance",
    )
