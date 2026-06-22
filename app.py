"""
app.py — Naseem Iron Store | Google Sheets Edition
Run: streamlit run app.py
"""

import datetime as dt
import pandas as pd
import streamlit as st
import sheets_db as db

st.set_page_config(
    page_title="Naseem Iron Store",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Segoe UI',Arial,sans-serif;}
.block-container{padding-top:1rem;padding-bottom:2rem;}
.banner{display:flex;align-items:center;gap:14px;background:linear-gradient(120deg,#0d1117,#1f2a38);border:1px solid #2a3a4a;border-radius:14px;padding:14px 22px;margin-bottom:1.4rem;box-shadow:0 4px 18px rgba(0,0,0,.45);}
.b-icon{width:42px;height:42px;background:#1f2e3d;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.b-title{font-size:1.6rem;font-weight:800;color:#f0f4f8;margin:0;}
.b-sub{font-size:.78rem;color:#6e8499;margin:0;}
.kcard{background:#141c26;border:1px solid #1f2e3d;border-radius:13px;padding:1rem 1.1rem;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,.3);}
.klbl{font-size:.78rem;color:#6e8499;margin-bottom:4px;}
.kval{font-size:1.7rem;font-weight:900;}
.green{color:#3ddc84;}.red{color:#ff6b6b;}.blue{color:#5b9bd5;}.white{color:#e8edf2;}
.sec{font-size:.95rem;font-weight:700;color:#6e8499;border-left:4px solid #5b9bd5;padding-left:10px;margin:1rem 0 .6rem;}
.panel{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:12px;}
.bar-r{display:flex;align-items:center;gap:7px;padding:4px 0;}
.bn{font-size:.82rem;color:#c8d6e0;min-width:120px;}
.bt{flex:1;height:7px;background:#1a2535;border-radius:4px;overflow:hidden;}
.bf{height:100%;border-radius:4px;}
.bv{font-size:.82rem;font-weight:700;min-width:80px;text-align:right;}
.pcard{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:10px 14px;margin-bottom:8px;}
.pname{font-size:1rem;font-weight:700;color:#dce6f0;}
.pph{font-size:.78rem;color:#4a6070;margin-top:2px;}
.pills{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;}
.pill{border-radius:16px;padding:3px 10px;font-size:.75rem;border:1px solid;}
.pc{color:#3ddc84;border-color:#1b3d29;background:#0e2019;}
.pd{color:#ff6b6b;border-color:#3d1b1b;background:#200e0e;}
.pb{color:#5b9bd5;border-color:#1b2f3d;background:#0e1a25;}
.pn{color:#93a8bb;border-color:#233040;background:#111a25;}
.lhead{display:grid;gap:6px;padding:6px 0;border-bottom:2px solid #1f2e3d;font-size:.78rem;color:#6e8499;font-weight:700;}
.lrow{display:grid;gap:6px;padding:7px 0;border-bottom:1px solid #111a25;font-size:.88rem;color:#c8d6e0;}
.lrow.cr{background:#0a1a0e;}.lrow.dr{background:#1a0a0a;}
.rtable{width:100%;border-collapse:collapse;}
.rtable th{background:#0d1520;color:#6e8499;font-weight:700;font-size:.78rem;padding:9px 8px;border-bottom:2px solid #1f2e3d;text-align:left;}
.rtable td{padding:9px 8px;border-bottom:1px solid #111a25;font-size:.88rem;color:#c8d6e0;}
.bcl{background:#1b3d29;color:#3ddc84;padding:2px 8px;border-radius:10px;font-size:.72rem;}
.bsu{background:#3d1b1b;color:#ff6b6b;padding:2px 8px;border-radius:10px;font-size:.72rem;}
.balcard{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:12px;text-align:center;margin-bottom:12px;}
@media(max-width:640px){.b-title{font-size:1.2rem;}.kval{font-size:1.3rem;}}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def pkr(v):
    try: v=float(v)
    except: v=0.0
    s="-" if v<0 else ""
    return f"{s}Rs.{abs(v):,.0f}"

def logo_svg():
    return('<svg width="28" height="28" viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">'
           '<rect width="56" height="56" rx="10" fill="#2a3a4a"/>'
           '<rect x="10" y="10" width="30" height="8" rx="2" fill="#e0e8f0"/>'
           '<rect x="10" y="10" width="8" height="30" rx="2" fill="#e0e8f0"/>'
           '<circle cx="37" cy="37" r="10" fill="none" stroke="#5b9bd5" stroke-width="5"/></svg>')

def go(page, pid=None, ptype=None):
    st.session_state.page  = page
    st.session_state.pid   = pid
    st.session_state.ptype = ptype

for k,v in [("page","dashboard"),("pid",None),("ptype",None)]:
    if k not in st.session_state:
        st.session_state[k]=v

# ── Banner ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <div class="b-icon">{logo_svg()}</div>
  <div>
    <p class="b-title">Naseem Iron Store</p>
    <p class="b-sub">نسیم آئرن اسٹور — Financial Dashboard (Google Sheets)</p>
  </div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔩 Navigation")
    for lbl,pg in [("🏠  Dashboard","dashboard"),("🧾  Clients","clients"),
                   ("📦  Suppliers","suppliers"),("📊  Reports","reports")]:
        if st.button(lbl, width="stretch"):
            go(pg); st.rerun()
    st.markdown("---")
    st.caption("☁️ Data saved in Google Sheets")
    st.caption("Data is never auto-deleted.")

# ── Loading helper ────────────────────────────────────────────────────────────
def with_spinner(fn, msg="Loading..."):
    with st.spinner(msg):
        return fn()

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    totals = with_spinner(db.get_dashboard_totals, "Loading dashboard...")

    c1,c2,c3,c4,c5 = st.columns(5)
    for col,lbl,val,cls in [
        (c1,"📥 Total Receivables", pkr(totals["total_receivables"]),"green"),
        (c2,"📤 Total Payables",    pkr(totals["total_payables"]),   "red"),
        (c3,"⚖️ Net Position",      pkr(totals["net_position"]),     "blue"),
        (c4,"👥 Clients",           str(totals["client_count"]),     "white"),
        (c5,"🏭 Suppliers",         str(totals["supplier_count"]),   "white"),
    ]:
        with col:
            st.markdown(f'<div class="kcard"><div class="klbl">{lbl}</div>'
                        f'<div class="kval {cls}">{val}</div></div>',
                        unsafe_allow_html=True)
    st.write("")
    l,r = st.columns(2)

    def bars(col, title, rows, color):
        with col:
            st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)
            if not rows:
                st.caption("No records yet.")
                return
            mx = max(max(x["balance"],0) for x in rows) or 1
            for x in rows:
                pct = max(min(x["balance"]/mx*100,100),0)
                st.markdown(
                    f'<div class="bar-r"><span class="bn">{x["name"]}</span>'
                    f'<div class="bt"><div class="bf" style="width:{pct}%;background:{color};"></div></div>'
                    f'<span class="bv" style="color:{color};">{pkr(x["balance"])}</span></div>',
                    unsafe_allow_html=True)

    bars(l,"🔝 Top Debtors (Receivables)", totals["top_clients"],   "#3ddc84")
    bars(r,"🔝 Top Payables (Suppliers)",  totals["top_suppliers"], "#ff6b6b")

    st.markdown("---")
    b1,b2 = st.columns(2)
    with b1:
        if st.button("➕ Add New Client", width="stretch"):
            go("clients"); st.rerun()
    with b2:
        if st.button("➕ Add New Supplier", width="stretch"):
            go("suppliers"); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PARTY LIST
# ═══════════════════════════════════════════════════════════════════════════════
def page_party_list(type_):
    is_client = type_=="client"
    title  = "Clients" if is_client else "Suppliers"
    icon   = "🧾" if is_client else "📦"
    st.subheader(f"{icon} {title}")

    with st.expander(f"➕ Add New {title[:-1]}"):
        with st.form(f"add_{type_}", clear_on_submit=True):
            name    = st.text_input("Name *")
            phone   = st.text_input("Phone")
            address = st.text_input("Address")
            if st.form_submit_button("Save"):
                if not name.strip():
                    st.warning("Please enter a name.")
                else:
                    with st.spinner("Saving..."):
                        db.add_party(name, type_, phone, address)
                    st.success(f"'{name}' added!")
                    st.rerun()

    search  = st.text_input("🔍 Search by name", key=f"s_{type_}")
    parties = with_spinner(lambda: db.get_all_parties(type_, search or None),
                           "Loading...")

    if not parties:
        st.info("No records yet. Add one above.")
        return

    for p in parties:
        summ = with_spinner(lambda pid=p["id"]: db.get_party_summary(pid), "")
        lc, bc = st.columns([5,1.3])
        with lc:
            st.markdown(f"""
<div class="pcard">
  <div class="pname">{p['name']}</div>
  {"<div class='pph'>📞 "+p['phone']+"</div>" if p.get('phone') else ""}
  <div class="pills">
    <span class="pill pn">🧾 Bill: {summ['last_invoice']}</span>
    <span class="pill pn">📅 {summ['last_date']}</span>
    <span class="pill pc">Credit: {pkr(summ['total_credit'])}</span>
    <span class="pill pd">Debit: {pkr(summ['total_debit'])}</span>
    <span class="pill pb">Balance: {pkr(summ['balance'])}</span>
  </div>
</div>""", unsafe_allow_html=True)
        with bc:
            st.write("")
            st.write("")
            if st.button("Ledger →", key=f"l_{type_}_{p['id']}", width="stretch"):
                go("ledger", pid=p["id"], ptype=type_)
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# LEDGER
# ═══════════════════════════════════════════════════════════════════════════════
def page_ledger(party_id, party_type):
    party = with_spinner(lambda: db.get_party_by_id(party_id), "")
    if not party:
        st.error("Record not found.")
        if st.button("← Back"):
            go("clients" if party_type=="client" else "suppliers"); st.rerun()
        return

    is_client = party_type=="client"
    if st.button("← Back to List"):
        go("clients" if is_client else "suppliers"); st.rerun()

    txns    = with_spinner(lambda: db.get_party_transactions(party_id), "Loading ledger...")
    balance = txns[-1]["balance"] if txns else 0.0

    bal_lbl = "Outstanding Balance" if is_client else "Amount Payable"
    bal_cls = "green" if is_client else "red"
    if balance < 0:
        bal_lbl = "Advance Paid"
        bal_cls = "blue"

    st.markdown(f"## {party['name']}")
    if party.get("phone"):
        st.caption(f"📞 {party['phone']}")

    st.markdown(
        f'<div class="balcard"><div style="font-size:.8rem;color:#6e8499;">{bal_lbl}</div>'
        f'<div class="kval {bal_cls}" style="font-size:1.8rem;">{pkr(balance)}</div></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="sec">➕ Add Entry</div>', unsafe_allow_html=True)
    with st.form(f"txn_{party_id}", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        with c1: txn_date   = st.date_input("Date", value=dt.date.today())
        with c2: invoice_no = st.text_input("Bill / Invoice No.")
        with c3: txn_type   = st.selectbox("Type",
                    ["Credit (Sale/Invoice)","Debit (Payment Received)"])
        amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0)
        notes  = st.text_input("Notes (optional)")

        if st.form_submit_button("✅ Save Entry", type="primary"):
            is_cr = txn_type.startswith("Credit")
            with st.spinner("Saving to Google Sheets..."):
                result = db.add_transaction(
                    party_id, txn_date, invoice_no,
                    credit=amount if is_cr else 0,
                    debit =amount if not is_cr else 0,
                    notes=notes)
            if result:
                st.success("✅ Entry saved to Google Sheets!")
                st.rerun()
            else:
                st.warning("Please enter amount > 0.")

    st.markdown('<div class="sec">📒 Ledger History</div>', unsafe_allow_html=True)
    if not txns:
        st.info("No transactions yet.")
        return

    cols = "80px 70px 1fr 1fr 1fr 1fr"
    st.markdown(
        f'<div class="lhead" style="grid-template-columns:{cols};">'
        f'<span>Date</span><span>Bill No.</span>'
        f'<span>Credit</span><span>Debit</span>'
        f'<span>Balance</span><span>Notes</span></div>',
        unsafe_allow_html=True)

    for t in txns:
        cr  = f'<span class="green" style="font-weight:700;">{pkr(t["credit"])}</span>' if t["credit"]>0 else "—"
        dr  = f'<span class="red" style="font-weight:700;">{pkr(t["debit"])}</span>'    if t["debit"]>0  else "—"
        cls = "cr" if t["credit"]>0 else "dr"
        inv = t.get("invoice_no") or "—"
        st.markdown(
            f'<div class="lrow {cls}" style="grid-template-columns:{cols};">'
            f'<span>{t["txn_date"]}</span>'
            f'<span style="color:#5b9bd5;">{inv}</span>'
            f'<span>{cr}</span><span>{dr}</span>'
            f'<span style="font-weight:700;">{pkr(t["balance"])}</span>'
            f'<span style="color:#4a6070;font-size:.8rem;">{t.get("notes","")}</span>'
            f'</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
def page_reports():
    st.subheader("📊 Reports")
    c1,c2 = st.columns(2)
    with c1:
        period = st.selectbox("Period",["monthly","weekly","all"],
            format_func=lambda x:{"monthly":"This Month","weekly":"This Week","all":"All Time"}[x])
    with c2:
        ft = st.selectbox("Party Type",["all","client","supplier"],
            format_func=lambda x:{"all":"All","client":"Clients Only","supplier":"Suppliers Only"}[x])

    data = with_spinner(
        lambda: db.get_report(period, None if ft=="all" else ft),
        "Generating report...")

    if not data:
        st.info("No transactions in this period.")
        return

    tot_cr  = sum(r["credit"]    for r in data)
    tot_dr  = sum(r["debit"]     for r in data)
    tot_txn = sum(r["txn_count"] for r in data)

    k1,k2,k3,k4 = st.columns(4)
    for col,lbl,val,cls in [
        (k1,"Total Credit (Sales)", pkr(tot_cr), "green"),
        (k2,"Total Debit (Payments)",pkr(tot_dr),"red"),
        (k3,"Net",pkr(tot_cr-tot_dr),"blue"),
        (k4,"Transactions",str(tot_txn),"white"),
    ]:
        with col:
            st.markdown(f'<div class="kcard"><div class="klbl">{lbl}</div>'
                        f'<div class="kval {cls}">{val}</div></div>',
                        unsafe_allow_html=True)

    st.markdown('<div class="sec">Party-wise Breakdown</div>', unsafe_allow_html=True)
    rows_html=""
    for r in data:
        badge = '<span class="bcl">Client</span>' if r["type"]=="client" else '<span class="bsu">Supplier</span>'
        rows_html += (f"<tr><td>{r['name']}</td><td>{badge}</td>"
                      f"<td class='green' style='font-weight:700;'>{pkr(r['credit'])}</td>"
                      f"<td class='red' style='font-weight:700;'>{pkr(r['debit'])}</td>"
                      f"<td style='font-weight:700;'>{pkr(r['balance'])}</td>"
                      f"<td style='color:#6e8499;'>{r['txn_count']}</td></tr>")

    st.markdown(f"""
<table class="rtable">
<thead><tr>
  <th>Party Name</th><th>Type</th>
  <th>Credit</th><th>Debit</th>
  <th>Balance</th><th>Transactions</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>""", unsafe_allow_html=True)

    st.write("")
    df = pd.DataFrame(data)[["name","type","credit","debit","balance","txn_count"]]
    df.columns = ["Name","Type","Credit","Debit","Balance","Transactions"]
    st.download_button("⬇️ Download Report (CSV)",
        data=df.to_csv(index=False),
        file_name=f"naseem_report_{period}_{dt.date.today()}.csv",
        mime="text/csv")

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
try:
    p = st.session_state.page
    if   p == "dashboard": page_dashboard()
    elif p == "clients":   page_party_list("client")
    elif p == "suppliers": page_party_list("supplier")
    elif p == "ledger":    page_ledger(st.session_state.pid, st.session_state.ptype)
    elif p == "reports":   page_reports()
    else:                  page_dashboard()
except Exception as e:
    st.error("An error occurred. Please check your Google Sheets credentials.")
    st.exception(e)
