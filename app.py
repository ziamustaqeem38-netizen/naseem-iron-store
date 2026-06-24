"""
app.py — Naseem Iron Store | Google Sheets Edition
Features: Date Filter, Daily Cash, Monthly Chart, Transaction Search, Edit/Delete
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

st.markdown("""
<style>
html,body,[class*="css"]{font-family:'Segoe UI',Arial,sans-serif;}
.block-container{padding-top:1rem;padding-bottom:2rem;}
.banner{display:flex;align-items:center;gap:14px;
  background:linear-gradient(120deg,#0d1117,#1f2a38);
  border:1px solid #2a3a4a;border-radius:14px;
  padding:14px 22px;margin-bottom:1.4rem;
  box-shadow:0 4px 18px rgba(0,0,0,.45);}
.b-icon{width:42px;height:42px;background:#1f2e3d;border-radius:10px;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.b-title{font-size:clamp(1rem,4vw,1.6rem);font-weight:800;color:#f0f4f8;margin:0;white-space:nowrap;}
.b-sub{font-size:.75rem;color:#6e8499;margin:0;}
.kcard{background:#141c26;border:1px solid #1f2e3d;border-radius:13px;
  padding:.9rem 1rem;text-align:center;}
.klbl{font-size:.75rem;color:#6e8499;margin-bottom:4px;}
.kval{font-size:1.5rem;font-weight:900;}
.green{color:#3ddc84;}.red{color:#ff6b6b;}
.blue{color:#5b9bd5;}.white{color:#e8edf2;}.orange{color:#f0a500;}
.sec{font-size:.92rem;font-weight:700;color:#6e8499;
  border-left:4px solid #5b9bd5;padding-left:10px;margin:1rem 0 .6rem;}
.panel{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;padding:12px;}
.bar-r{display:flex;align-items:center;gap:7px;padding:4px 0;}
.bn{font-size:.8rem;color:#c8d6e0;min-width:110px;}
.bt{flex:1;height:7px;background:#1a2535;border-radius:4px;overflow:hidden;}
.bf{height:100%;border-radius:4px;}
.bv{font-size:.8rem;font-weight:700;min-width:75px;text-align:right;}
.pcard{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;
  padding:10px 14px;margin-bottom:8px;}
.pname{font-size:1rem;font-weight:700;color:#dce6f0;}
.pph{font-size:.78rem;color:#4a6070;margin-top:2px;}
.pills{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;}
.pill{border-radius:16px;padding:3px 10px;font-size:.73rem;border:1px solid;}
.pc{color:#3ddc84;border-color:#1b3d29;background:#0e2019;}
.pd{color:#ff6b6b;border-color:#3d1b1b;background:#200e0e;}
.pb{color:#5b9bd5;border-color:#1b2f3d;background:#0e1a25;}
.pn{color:#93a8bb;border-color:#233040;background:#111a25;}
.lhead{display:grid;gap:5px;padding:6px 0;
  border-bottom:2px solid #1f2e3d;font-size:.75rem;color:#6e8499;font-weight:700;}
.lrow{display:grid;gap:5px;padding:6px 0;
  border-bottom:1px solid #111a25;font-size:.85rem;color:#c8d6e0;}
.lrow.cr{background:#0a1a0e;}.lrow.dr{background:#1a0a0a;}
.rtable{width:100%;border-collapse:collapse;}
.rtable th{background:#0d1520;color:#6e8499;font-weight:700;font-size:.75rem;
  padding:8px 6px;border-bottom:2px solid #1f2e3d;text-align:left;}
.rtable td{padding:8px 6px;border-bottom:1px solid #111a25;font-size:.85rem;color:#c8d6e0;}
.bcl{background:#1b3d29;color:#3ddc84;padding:2px 8px;border-radius:10px;font-size:.7rem;}
.bsu{background:#3d1b1b;color:#ff6b6b;padding:2px 8px;border-radius:10px;font-size:.7rem;}
.balcard{background:#141c26;border:1px solid #1f2e3d;border-radius:12px;
  padding:12px;text-align:center;margin-bottom:12px;}
.alert-card{background:#1a1500;border:1px solid #3d3000;border-radius:10px;
  padding:10px 14px;margin-bottom:7px;}
.edit-box{background:#0d1825;border:1px solid #1b2f3d;border-radius:10px;padding:12px;margin-top:6px;}
@media(max-width:640px){.kval{font-size:1.1rem;}}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def pkr(v):
    try: v = float(v)
    except: v = 0.0
    s = "-" if v < 0 else ""
    return f"{s}Rs.{abs(v):,.0f}"

def logo():
    return (
        '<svg width="28" height="28" viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="56" height="56" rx="10" fill="#2a3a4a"/>'
        '<rect x="10" y="10" width="30" height="8" rx="2" fill="#e0e8f0"/>'
        '<rect x="10" y="10" width="8" height="30" rx="2" fill="#e0e8f0"/>'
        '<circle cx="37" cy="37" r="10" fill="none" stroke="#5b9bd5" stroke-width="5"/></svg>'
    )

def go(page, pid=None, ptype=None):
    st.session_state.page  = page
    st.session_state.pid   = pid
    st.session_state.ptype = ptype
    st.session_state.editing_txn   = None
    st.session_state.editing_party = None

for k, v in [("page","dashboard"),("pid",None),("ptype",None),
              ("editing_txn",None),("editing_party",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

def spin(fn, msg="Loading..."):
    with st.spinner(msg):
        return fn()

# ── Banner ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <div class="b-icon">{logo()}</div>
  <div style="min-width:0;flex:1;">
    <p class="b-title">Naseem Iron Store</p>
    <p class="b-sub">نسیم آئرن اسٹور — Financial Dashboard</p>
  </div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔩 Navigation")
    nav_items = [
        ("🏠  Dashboard",       "dashboard"),
        ("🧾  Clients",         "clients"),
        ("📦  Suppliers",       "suppliers"),
        ("💰  Daily Cash",      "daily_cash"),
        ("📊  Reports",         "reports"),
        ("🔍  Search",          "search"),
    ]
    for lbl, pg in nav_items:
        if st.button(lbl, width="stretch"):
            go(pg); st.rerun()
    st.markdown("---")
    st.caption("☁️ Data saved in Google Sheets")
    st.caption("Data is never auto-deleted.")

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    totals = spin(db.get_dashboard_totals, "Loading dashboard...")

    # KPI cards
    c1,c2,c3,c4,c5 = st.columns(5)
    for col,lbl,val,cls in [
        (c1,"📥 Receivables",  pkr(totals["total_receivables"]), "green"),
        (c2,"📤 Payables",     pkr(totals["total_payables"]),    "red"),
        (c3,"⚖️ Net Position", pkr(totals["net_position"]),      "blue"),
        (c4,"👥 Clients",      str(totals["client_count"]),      "white"),
        (c5,"🏭 Suppliers",    str(totals["supplier_count"]),    "white"),
    ]:
        with col:
            st.markdown(
                f'<div class="kcard"><div class="klbl">{lbl}</div>'
                f'<div class="kval {cls}">{val}</div></div>',
                unsafe_allow_html=True)

    st.write("")

    # Overdue alerts
    overdue = spin(db.get_overdue_clients, "")
    if overdue:
        st.markdown('<div class="sec">🔔 Overdue Clients (no payment in 30+ days)</div>',
                    unsafe_allow_html=True)
        for o in overdue:
            st.markdown(
                f'<div class="alert-card">'
                f'<span style="color:#f0a500;font-weight:700;">{o["name"]}</span>'
                f' — Balance: <span class="green">{pkr(o["balance"])}</span>'
                f' — Last payment: <span style="color:#6e8499;">{o["last_date"]}</span>'
                f'</div>', unsafe_allow_html=True)

    st.write("")
    l, r = st.columns(2)

    def bars(col, title, rows, color):
        with col:
            st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)
            if not rows:
                st.caption("No records yet.")
                return
            mx = max(max(x["balance"],0) for x in rows) or 1
            for x in rows:
                pct = max(min(x["balance"]/mx*100, 100), 0)
                st.markdown(
                    f'<div class="bar-r"><span class="bn">{x["name"]}</span>'
                    f'<div class="bt"><div class="bf" style="width:{pct}%;background:{color};"></div></div>'
                    f'<span class="bv" style="color:{color};">{pkr(x["balance"])}</span></div>',
                    unsafe_allow_html=True)

    bars(l, "🔝 Top Debtors",   totals["top_clients"],   "#3ddc84")
    bars(r, "🔝 Top Payables",  totals["top_suppliers"], "#ff6b6b")

    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("➕ Add New Client",   width="stretch"): go("clients");   st.rerun()
    with b2:
        if st.button("➕ Add New Supplier", width="stretch"): go("suppliers"); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PARTY LIST
# ═══════════════════════════════════════════════════════════════════════════════
def page_party_list(type_):
    is_client = type_ == "client"
    title = "Clients" if is_client else "Suppliers"
    icon  = "🧾" if is_client else "📦"
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
                    st.success(f"'{name}' added!"); st.rerun()

    search  = st.text_input("🔍 Search by name", key=f"s_{type_}")
    parties = spin(lambda: db.get_all_parties(type_, search or None), "Loading...")

    if not parties:
        st.info("No records yet. Add one above.")
        return

    for p in parties:
        summ = spin(lambda pid=p["id"]: db.get_party_summary(pid), "")
        lc, bc = st.columns([5, 1.3])
        with lc:
            st.markdown(f"""
<div class="pcard">
  <div class="pname">{p['name']}</div>
  {"<div class='pph'>📞 "+str(p['phone'])+"</div>" if p.get('phone') else ""}
  <div class="pills">
    <span class="pill pn">🧾 {summ['last_invoice']}</span>
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
                go("ledger", pid=p["id"], ptype=type_); st.rerun()

        with st.expander(f"✏️ Edit / 🗑️ Delete / 🏦 Opening Balance — {p['name']}"):
            tab_e, tab_d, tab_ob = st.tabs(["✏️ Edit", "🗑️ Delete", "🏦 Opening Balance"])
            with tab_e:
                with st.form(f"ep_{p['id']}", clear_on_submit=False):
                    nn = st.text_input("Name",    value=str(p.get("name","")))
                    np = st.text_input("Phone",   value=str(p.get("phone","")))
                    na = st.text_input("Address", value=str(p.get("address","")))
                    if st.form_submit_button("💾 Save Changes"):
                        with st.spinner("Updating..."):
                            ok = db.update_party(p["id"], nn, np, na)
                        if ok: st.success("✅ Updated!"); st.rerun()
                        else:  st.error("Could not update.")
            with tab_d:
                st.warning(f"Remove **{p['name']}** from list? (data stays in Sheets)")
                if st.button(f"🗑️ Delete {p['name']}", key=f"dp_{p['id']}", type="primary"):
                    with st.spinner("Deleting..."):
                        db.delete_party(p["id"])
                    st.success("Deleted!"); st.rerun()

            with tab_ob:
                st.info("پرانا باقی حساب یہاں ڈالیں — یہ پہلی entry ہوگی")
                with st.form(f"ob_list_{p['id']}", clear_on_submit=True):
                    obl1, obl2 = st.columns(2)
                    with obl1:
                        obl_date = st.date_input("Date", value=dt.date.today(), key=f"obld_{p['id']}")
                        obl_type = st.selectbox("Balance Type",
                            ["Receivable (Client owes us)", "Payable (We owe supplier)"],
                            key=f"oblt_{p['id']}")
                    with obl2:
                        obl_amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0, key=f"obla_{p['id']}")
                        obl_notes  = st.text_input("Notes", value="Opening Balance", key=f"obln_{p['id']}")
                    if st.form_submit_button("✅ Save Opening Balance"):
                        btype = "receivable" if obl_type.startswith("Receivable") else "payable"
                        with st.spinner("Saving..."):
                            result = db.add_opening_balance(p["id"], obl_amount, btype, obl_date.isoformat(), obl_notes)
                        if result: st.success(f"✅ Opening Balance saved for {p['name']}!"); st.rerun()
                        else:      st.warning("Please enter amount > 0.")

# ═══════════════════════════════════════════════════════════════════════════════
# LEDGER
# ═══════════════════════════════════════════════════════════════════════════════
def page_ledger(party_id, party_type):
    party = spin(lambda: db.get_party_by_id(party_id), "")
    if not party:
        st.error("Record not found.")
        if st.button("← Back"):
            go("clients" if party_type=="client" else "suppliers"); st.rerun()
        return

    is_client = party_type == "client"
    if st.button("← Back to List"):
        go("clients" if is_client else "suppliers"); st.rerun()

    all_txns = spin(lambda: db.get_party_transactions(party_id), "Loading ledger...")
    balance  = all_txns[-1]["balance"] if all_txns else 0.0
    bal_lbl  = "Outstanding Balance" if is_client else "Amount Payable"
    bal_cls  = "green" if is_client else "red"
    if balance < 0: bal_lbl = "Advance Paid"; bal_cls = "blue"

    st.markdown(f"## {party['name']}")
    if party.get("phone"): st.caption(f"📞 {party['phone']}")

    st.markdown(
        f'<div class="balcard">'
        f'<div style="font-size:.8rem;color:#6e8499;">{bal_lbl}</div>'
        f'<div class="kval {bal_cls}" style="font-size:1.8rem;">{pkr(balance)}</div>'
        f'</div>', unsafe_allow_html=True)

    # ── Opening Balance ──
    st.markdown('<div class="sec">🏦 Opening Balance (پرانا حساب)</div>', unsafe_allow_html=True)
    with st.expander("➕ Add Opening Balance — پرانا باقی حساب یہاں ڈالیں"):
        with st.form(f"ob_{party_id}", clear_on_submit=True):
            ob1, ob2, ob3 = st.columns(3)
            with ob1:
                ob_date = st.date_input("Date", value=dt.date.today(), key=f"obdate_{party_id}")
            with ob2:
                ob_type = st.selectbox(
                    "Balance Type",
                    ["Receivable (Client owes us)", "Payable (We owe supplier)"],
                    key=f"obtype_{party_id}",
                    help="Receivable = client ka humara paise dena hai | Payable = hum supplier ko dene hain"
                )
            with ob3:
                ob_amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0, key=f"obamt_{party_id}")
            ob_notes = st.text_input("Notes", value="Opening Balance", key=f"obnotes_{party_id}")
            if st.form_submit_button("✅ Save Opening Balance", type="primary"):
                btype = "receivable" if ob_type.startswith("Receivable") else "payable"
                with st.spinner("Saving..."):
                    result = db.add_opening_balance(
                        party_id, ob_amount, btype,
                        ob_date.isoformat(), ob_notes)
                if result: st.success("✅ Opening Balance saved!"); st.rerun()
                else:      st.warning("Please enter amount > 0.")

    # ── Add Entry ──
    st.markdown('<div class="sec">➕ Add New Entry</div>', unsafe_allow_html=True)
    with st.form(f"txn_{party_id}", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: txn_date   = st.date_input("Date", value=dt.date.today())
        with c2: invoice_no = st.text_input("Bill / Invoice No.")
        with c3: txn_type   = st.selectbox("Type",
                    ["Credit (Sale/Invoice)", "Debit (Payment Received)"])
        amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0)
        notes  = st.text_input("Notes (optional)")
        if st.form_submit_button("✅ Save Entry", type="primary"):
            is_cr = txn_type.startswith("Credit")
            with st.spinner("Saving..."):
                result = db.add_transaction(
                    party_id, txn_date, invoice_no,
                    credit=amount if is_cr else 0,
                    debit =amount if not is_cr else 0,
                    notes=notes)
            if result: st.success("✅ Saved to Google Sheets!"); st.rerun()
            else:      st.warning("Please enter amount > 0.")

    # ── Date Filter ──
    st.markdown('<div class="sec">📒 Ledger History</div>', unsafe_allow_html=True)

    if not all_txns:
        st.info("No transactions yet.")
        return

    f1, f2, f3 = st.columns(3)
    with f1:
        filter_type = st.selectbox("Filter",
            ["All Time","This Month","This Week","Custom Range"],
            key=f"ftype_{party_id}")
    with f2:
        search_bill = st.text_input("🔍 Search Bill No.", key=f"sbill_{party_id}")

    # Apply date filter
    today = dt.date.today()
    if filter_type == "This Month":
        cutoff = today.replace(day=1).isoformat()
        txns = [t for t in all_txns if str(t.get("txn_date","")) >= cutoff]
    elif filter_type == "This Week":
        cutoff = (today - dt.timedelta(days=7)).isoformat()
        txns = [t for t in all_txns if str(t.get("txn_date","")) >= cutoff]
    elif filter_type == "Custom Range":
        with f3:
            col_a, col_b = st.columns(2)
            with col_a: d_from = st.date_input("From", value=today.replace(day=1), key=f"df_{party_id}")
            with col_b: d_to   = st.date_input("To",   value=today,               key=f"dt_{party_id}")
        txns = [t for t in all_txns
                if d_from.isoformat() <= str(t.get("txn_date","")) <= d_to.isoformat()]
    else:
        txns = all_txns

    # Apply bill search
    if search_bill.strip():
        txns = [t for t in txns if search_bill.strip().lower() in str(t.get("invoice_no","")).lower()]

    # Period totals
    period_cr  = sum(float(t.get("credit",0)) for t in txns)
    period_dr  = sum(float(t.get("debit",0))  for t in txns)
    pa, pb, pc = st.columns(3)
    with pa: st.markdown(f'<div class="kcard"><div class="klbl">Period Credit</div><div class="kval green">{pkr(period_cr)}</div></div>', unsafe_allow_html=True)
    with pb: st.markdown(f'<div class="kcard"><div class="klbl">Period Debit</div><div class="kval red">{pkr(period_dr)}</div></div>',   unsafe_allow_html=True)
    with pc: st.markdown(f'<div class="kcard"><div class="klbl">Entries</div><div class="kval white">{len(txns)}</div></div>',            unsafe_allow_html=True)

    if not txns:
        st.info("No entries found for selected filter.")
        return

    st.write("")
    cols = "75px 65px 85px 85px 80px 1fr"
    st.markdown(
        f'<div class="lhead" style="grid-template-columns:{cols};">'
        f'<span>Date</span><span>Bill No.</span>'
        f'<span>Credit</span><span>Debit</span>'
        f'<span>Balance</span><span>Notes</span></div>',
        unsafe_allow_html=True)

    for t in txns:
        cr  = f'<span class="green" style="font-weight:700;">{pkr(t["credit"])}</span>' if float(t.get("credit",0))>0 else "—"
        dr  = f'<span class="red"   style="font-weight:700;">{pkr(t["debit"])}</span>'  if float(t.get("debit",0))>0  else "—"
        cls = "cr" if float(t.get("credit",0))>0 else "dr"
        inv = t.get("invoice_no") or "—"
        st.markdown(
            f'<div class="lrow {cls}" style="grid-template-columns:{cols};">'
            f'<span>{t["txn_date"]}</span>'
            f'<span style="color:#5b9bd5;">{inv}</span>'
            f'<span>{cr}</span><span>{dr}</span>'
            f'<span style="font-weight:700;">{pkr(t["balance"])}</span>'
            f'<span style="color:#4a6070;font-size:.8rem;">{t.get("notes","")}</span>'
            f'</div>', unsafe_allow_html=True)

        ea, da = st.columns([1,1])
        with ea:
            if st.button("✏️ Edit", key=f"e_{t['id']}"):
                st.session_state.editing_txn = t["id"]; st.rerun()
        with da:
            if st.button("🗑️ Del", key=f"d_{t['id']}"):
                with st.spinner("Deleting..."):
                    db.delete_transaction(t["id"])
                st.success("Deleted!"); st.rerun()

        if st.session_state.editing_txn == t["id"]:
            st.markdown('<div class="edit-box">', unsafe_allow_html=True)
            st.markdown(f"**✏️ Edit Entry #{t['id']}**")
            with st.form(f"etxn_{t['id']}", clear_on_submit=False):
                ec1,ec2,ec3 = st.columns(3)
                with ec1:
                    try:    def_date = dt.date.fromisoformat(str(t["txn_date"]))
                    except: def_date = dt.date.today()
                    new_date = st.date_input("Date", value=def_date)
                with ec2:
                    new_inv = st.text_input("Bill No.", value=str(t.get("invoice_no","")))
                with ec3:
                    cur_cr  = float(t.get("credit",0))
                    cur_type = "Credit (Sale/Invoice)" if cur_cr>0 else "Debit (Payment Received)"
                    new_type = st.selectbox("Type",
                        ["Credit (Sale/Invoice)","Debit (Payment Received)"],
                        index=0 if cur_cr>0 else 1)
                cur_amt  = cur_cr if cur_cr>0 else float(t.get("debit",0))
                new_amt  = st.number_input("Amount (PKR)", value=float(cur_amt), min_value=0.0, step=100.0)
                new_note = st.text_input("Notes", value=str(t.get("notes","")))
                sc1, sc2 = st.columns(2)
                with sc1:
                    if st.form_submit_button("💾 Save", type="primary"):
                        is_cr = new_type.startswith("Credit")
                        with st.spinner("Updating..."):
                            ok = db.update_transaction(
                                t["id"], new_date, new_inv,
                                credit=new_amt if is_cr else 0,
                                debit =new_amt if not is_cr else 0,
                                notes=new_note)
                        if ok:
                            st.session_state.editing_txn = None
                            st.success("✅ Updated!"); st.rerun()
                        else: st.error("Could not update.")
                with sc2:
                    if st.form_submit_button("✖️ Cancel"):
                        st.session_state.editing_txn = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DAILY CASH REPORT
# ═══════════════════════════════════════════════════════════════════════════════
def page_daily_cash():
    st.subheader("💰 Daily Cash Report")

    col1, col2 = st.columns(2)
    with col1:
        sel_date = st.date_input("Select Date", value=dt.date.today())

    data = spin(lambda: db.get_daily_cash(sel_date.isoformat()), "Loading...")

    k1,k2,k3 = st.columns(3)
    with k1: st.markdown(f'<div class="kcard"><div class="klbl">📥 Total Received</div><div class="kval green">{pkr(data["total_credit"])}</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kcard"><div class="klbl">📤 Total Paid</div><div class="kval red">{pkr(data["total_debit"])}</div></div>',     unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kcard"><div class="klbl">💰 Net Cash</div><div class="kval blue">{pkr(data["net"])}</div></div>',               unsafe_allow_html=True)

    if data["transactions"]:
        st.markdown('<div class="sec">Transactions of the Day</div>', unsafe_allow_html=True)
        cols = "1fr 70px 90px 90px 1fr"
        st.markdown(
            f'<div class="lhead" style="grid-template-columns:{cols};">'
            f'<span>Party</span><span>Bill No.</span>'
            f'<span>Credit</span><span>Debit</span><span>Notes</span></div>',
            unsafe_allow_html=True)
        for t in data["transactions"]:
            cr = f'<span class="green">{pkr(t["credit"])}</span>' if float(t.get("credit",0))>0 else "—"
            dr = f'<span class="red">{pkr(t["debit"])}</span>'   if float(t.get("debit",0))>0  else "—"
            cls = "cr" if float(t.get("credit",0))>0 else "dr"
            st.markdown(
                f'<div class="lrow {cls}" style="grid-template-columns:{cols};">'
                f'<span style="font-weight:700;">{t.get("party_name","—")}</span>'
                f'<span style="color:#5b9bd5;">{t.get("invoice_no","—") or "—"}</span>'
                f'<span>{cr}</span><span>{dr}</span>'
                f'<span style="color:#4a6070;font-size:.8rem;">{t.get("notes","")}</span>'
                f'</div>', unsafe_allow_html=True)
    else:
        st.info(f"No transactions on {sel_date}.")

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS + MONTHLY CHART
# ═══════════════════════════════════════════════════════════════════════════════
def page_reports():
    st.subheader("📊 Reports")
    tab1, tab2 = st.tabs(["📋 Party-wise Report", "📈 Monthly Chart"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            period = st.selectbox("Period", ["monthly","weekly","all"],
                format_func=lambda x:{"monthly":"This Month","weekly":"This Week","all":"All Time"}[x])
        with c2:
            ft = st.selectbox("Party Type", ["all","client","supplier"],
                format_func=lambda x:{"all":"All","client":"Clients","supplier":"Suppliers"}[x])

        data = spin(lambda: db.get_report(period, None if ft=="all" else ft), "Loading...")
        if not data:
            st.info("No transactions in this period."); return

        tot_cr = sum(r["credit"]    for r in data)
        tot_dr = sum(r["debit"]     for r in data)
        tot_tx = sum(r["txn_count"] for r in data)

        k1,k2,k3,k4 = st.columns(4)
        for col,lbl,val,cls in [
            (k1,"Total Credit",  pkr(tot_cr),        "green"),
            (k2,"Total Debit",   pkr(tot_dr),         "red"),
            (k3,"Net",           pkr(tot_cr-tot_dr),  "blue"),
            (k4,"Transactions",  str(tot_tx),          "white"),
        ]:
            with col:
                st.markdown(f'<div class="kcard"><div class="klbl">{lbl}</div>'
                            f'<div class="kval {cls}">{val}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">Party-wise Breakdown</div>', unsafe_allow_html=True)
        rows_html = ""
        for r in data:
            badge = '<span class="bcl">Client</span>' if r["type"]=="client" else '<span class="bsu">Supplier</span>'
            rows_html += (
                f"<tr><td>{r['name']}</td><td>{badge}</td>"
                f"<td class='green' style='font-weight:700;'>{pkr(r['credit'])}</td>"
                f"<td class='red'   style='font-weight:700;'>{pkr(r['debit'])}</td>"
                f"<td style='font-weight:700;'>{pkr(r['balance'])}</td>"
                f"<td style='color:#6e8499;'>{r['txn_count']}</td></tr>"
            )
        st.markdown(f"""
<table class="rtable">
<thead><tr><th>Party</th><th>Type</th><th>Credit</th><th>Debit</th><th>Balance</th><th>Txns</th></tr></thead>
<tbody>{rows_html}</tbody></table>""", unsafe_allow_html=True)

        st.write("")
        df = pd.DataFrame(data)[["name","type","credit","debit","balance","txn_count"]]
        df.columns = ["Name","Type","Credit","Debit","Balance","Transactions"]
        st.download_button("⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name=f"naseem_{period}_{dt.date.today()}.csv",
            mime="text/csv")

    with tab2:
        st.markdown('<div class="sec">📈 Monthly Credit vs Debit (Last 6 Months)</div>',
                    unsafe_allow_html=True)
        chart_data = spin(db.get_monthly_chart_data, "Loading chart...")
        if not chart_data:
            st.info("Not enough data for chart yet.")
            return

        df_chart = pd.DataFrame(chart_data)
        df_chart = df_chart.set_index("month")
        st.bar_chart(df_chart[["credit","debit"]], color=["#3ddc84","#ff6b6b"])

        st.markdown('<div class="sec">Monthly Summary Table</div>', unsafe_allow_html=True)
        rows_html = ""
        for row in chart_data:
            rows_html += (
                f"<tr><td>{row['month']}</td>"
                f"<td class='green' style='font-weight:700;'>{pkr(row['credit'])}</td>"
                f"<td class='red'   style='font-weight:700;'>{pkr(row['debit'])}</td>"
                f"<td style='font-weight:700;'>{pkr(row['credit']-row['debit'])}</td>"
                f"<td style='color:#6e8499;'>{row['count']}</td></tr>"
            )
        st.markdown(f"""
<table class="rtable">
<thead><tr><th>Month</th><th>Credit</th><th>Debit</th><th>Net</th><th>Txns</th></tr></thead>
<tbody>{rows_html}</tbody></table>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TRANSACTION SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
def page_search():
    st.subheader("🔍 Transaction Search")

    c1, c2 = st.columns(2)
    with c1: query    = st.text_input("Search by Bill No. or Notes")
    with c2: s_type   = st.selectbox("Type", ["All","Credit Only","Debit Only"])

    if not query.strip():
        st.info("Enter bill number or notes to search.")
        return

    results = spin(lambda: db.search_transactions(
        query, None if s_type=="All" else s_type.split()[0].lower()
    ), "Searching...")

    if not results:
        st.warning("No results found.")
        return

    st.caption(f"{len(results)} result(s) found")
    cols = "1fr 75px 70px 90px 90px 1fr"
    st.markdown(
        f'<div class="lhead" style="grid-template-columns:{cols};">'
        f'<span>Party</span><span>Date</span><span>Bill No.</span>'
        f'<span>Credit</span><span>Debit</span><span>Notes</span></div>',
        unsafe_allow_html=True)
    for t in results:
        cr  = f'<span class="green">{pkr(t["credit"])}</span>' if float(t.get("credit",0))>0 else "—"
        dr  = f'<span class="red">{pkr(t["debit"])}</span>'   if float(t.get("debit",0))>0  else "—"
        cls = "cr" if float(t.get("credit",0))>0 else "dr"
        st.markdown(
            f'<div class="lrow {cls}" style="grid-template-columns:{cols};">'
            f'<span style="font-weight:700;">{t.get("party_name","—")}</span>'
            f'<span>{t.get("txn_date","")}</span>'
            f'<span style="color:#5b9bd5;">{t.get("invoice_no","—") or "—"}</span>'
            f'<span>{cr}</span><span>{dr}</span>'
            f'<span style="color:#4a6070;font-size:.8rem;">{t.get("notes","")}</span>'
            f'</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
try:
    p = st.session_state.page
    if   p == "dashboard":  page_dashboard()
    elif p == "clients":    page_party_list("client")
    elif p == "suppliers":  page_party_list("supplier")
    elif p == "ledger":     page_ledger(st.session_state.pid, st.session_state.ptype)
    elif p == "daily_cash": page_daily_cash()
    elif p == "reports":    page_reports()
    elif p == "search":     page_search()
    else:                   page_dashboard()
except Exception as e:
    st.error("An error occurred. Please try again.")
    st.exception(e)
