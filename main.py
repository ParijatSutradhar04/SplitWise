import streamlit as st

st.set_page_config(page_title="Group Expense Splitter", page_icon="💸")

st.title("💸 Group Trip Expense Splitter")

st.markdown("""
Enter each expense below:
- **Who paid**: Name of the person who paid.
- **Amount**: Amount paid.
- **For what**: Description of the expense.
- **Except**: People who didn't participate in this expense (comma separated).
""")

# Session state initialization
if "transactions" not in st.session_state:
    st.session_state.transactions = [
        {"person": "", "amount": 0.0, "item": "", "except": ""}
    ]

def add_transaction():
    st.session_state.transactions.append({"person": "", "amount": 0.0, "item": "", "except": ""})

# --- UI Form ---
with st.form("expense_form"):
    known_names = sorted({txn["person"] for txn in st.session_state.transactions if txn["person"]})

    for i, txn in enumerate(st.session_state.transactions):
        cols = st.columns([2, 1.5, 2, 2])
        txn["person"] = cols[0].text_input("Who paid", value=txn["person"], key=f"person_{i}")
        txn["amount"] = cols[1].number_input("Amount", min_value=0.0, value=float(txn["amount"]), key=f"amount_{i}")
        txn["item"] = cols[2].text_input("For what", value=txn["item"], key=f"item_{i}")
        txn["except"] = cols[3].text_input("Except (comma-separated)", value=txn["except"], key=f"except_{i}")

    submitted = st.form_submit_button("Calculate Expenses")
    st.form_submit_button("➕ Add More Transactions", on_click=add_transaction)

# --- Core Logic ---
def get_participants(expenses):
    names = set()
    for txn in expenses:
        names.add(txn["person"])
        if txn["except"]:
            excluded = [name.strip() for name in txn["except"].split(",")]
            names.update(excluded)
    return sorted(list(names))

def calculate_expenses(expenses, all_participants):
    paid_amounts = {name: 0 for name in all_participants}
    owed_amounts = {name: 0 for name in all_participants}

    for txn in expenses:
        payer = txn["person"]
        amount = float(txn["amount"])
        excluded_people = [name.strip() for name in txn["except"].split(",") if name.strip()]
        involved = [p for p in all_participants if p not in excluded_people]

        if not involved:
            continue  # avoid division by zero

        split = amount / len(involved)

        paid_amounts[payer] += amount
        for person in involved:
            owed_amounts[person] += split

    net_balances = {person: paid_amounts[person] - owed_amounts[person] for person in all_participants}
    return net_balances

def settle_payments(net_balances):
    debtors = {p: -b for p, b in net_balances.items() if b < -0.01}
    creditors = {p: b for p, b in net_balances.items() if b > 0.01}

    payments = []
    debtors_list = sorted(debtors.items(), key=lambda x: x[1], reverse=True)
    creditors_list = sorted(creditors.items(), key=lambda x: x[1], reverse=True)

    d, c = 0, 0
    while d < len(debtors_list) and c < len(creditors_list):
        debtor, debt_amt = debtors_list[d]
        creditor, credit_amt = creditors_list[c]
        transfer = min(debt_amt, credit_amt)

        payments.append(f"💰 {debtor} pays {creditor}: ₹{transfer:.2f}")
        debtors_list[d] = (debtor, debt_amt - transfer)
        creditors_list[c] = (creditor, credit_amt - transfer)

        if debtors_list[d][1] < 0.01:
            d += 1
        if creditors_list[c][1] < 0.01:
            c += 1

    return payments

# --- Output Display ---
if submitted:
    expenses = st.session_state.transactions

    for txn in expenses:
        if not txn["person"] or txn["amount"] is None:
            st.error("Each transaction must have a person and amount.")
            st.stop()

    all_participants = get_participants(expenses)
    net_balances = calculate_expenses(expenses, all_participants)
    payments = settle_payments(net_balances)

    st.subheader("👥 Participants")
    st.write(", ".join(all_participants))

    st.subheader("💼 Net Balances")
    for name in all_participants:
        st.write(f"**{name}**: ₹{net_balances[name]:.2f}")

    st.subheader("🔁 Payment Summary (Min Transactions)")
    if payments:
        for payment in payments:
            st.write(payment)
        st.success(f"Total transactions required: {len(payments)}")
    else:
        st.write("✅ Everyone is settled up!")

    st.subheader("🧾 Transaction Breakdown")
    for txn in expenses:
        excluded = f" (except {txn['except']})" if txn["except"] else ""
        st.write(f"{txn['person']} paid ₹{txn['amount']} for {txn['item']}{excluded}")
