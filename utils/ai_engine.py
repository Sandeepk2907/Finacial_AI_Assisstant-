from transformers import pipeline
import random
import re
from rapidfuzz import process, fuzz

# --- Load the QA pipeline (same model you used) ---
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

# --- Your BANKING_CONTEXT (unchanged) ---
# ----- Replace this dictionary in utils/ai_engine.py -----
BANKING_CONTEXT = {
    "atm": """Automated Teller Machine (ATM).\n
An ATM (Automated Teller Machine) is a self-service banking terminal that allows customers to withdraw cash, deposit money, check account balances, and transfer funds without visiting a branch.
\n
How to use / How it works:
Insert your debit/ATM card, enter your PIN, choose a transaction (withdraw/deposit/balance), follow on-screen prompts, and collect your card & receipt. For deposits, many ATMs accept cash or cheque envelopes.

Example:
Insert your debit card, enter PIN, choose 'Withdraw', select amount (e.g., ₹2000), and collect cash.

Tip:
Shield the keypad while entering your PIN, never share OTPs or PINs, and always take the receipt.
""",

    "debit card": """Debit Card.
A debit card is linked directly to your bank account and lets you pay for purchases or withdraw cash using funds already in your account.

How to use / How it works:
Use it at ATMs to withdraw cash or at shops/online by entering card details or using contactless payments. The spent amount is deducted immediately from your account.

Example:
Paying a grocery bill by swiping the debit card or using 'tap to pay'.

Tip:
Check daily limits and report lost cards immediately.
""",

    "credit card": """Credit Card.
A credit card lets you borrow money from the bank up to a preset limit and repay later. Interest is charged if the full amount is not paid by the due date.

How to use / How it works:
Use for purchases or cash advances. Pay the full balance or minimum due by the due date. Paying in full avoids interest.

Example:
Buying a phone on credit and paying the bank later when the bill arrives.

Tip:
Avoid carrying big balances to prevent high interest.
""",

    "loan": """Loan.
A loan is money you borrow from a bank or financial institution that you must repay with interest over a set period.

How to use / How it works:
Apply online or at a branch, submit identity & income proof, get approval, and then repay monthly EMIs.

Example:
Home loan repaid over 20 years through EMIs.

Tip:
Check interest rates, fees, and prepayment charges before taking a loan.
""",

    "types of loans": """Types of Loans.
Common loans include personal loans, home loans, vehicle loans, education loans, and business loans.

How to use / How it works:
Choose a loan based on your need, compare interest rates and tenures, and meet eligibility requirements.

Example:
Education loan for tuition, vehicle loan to buy a car.

Tip:
Secured loans usually have lower interest rates.
""",

    "fixed deposit": """Fixed Deposit (FD).
A fixed deposit lets you lock a lump sum for a fixed period to earn higher interest than a savings account.

How to use / How it works:
Deposit a lump sum, choose tenure, and receive principal + interest at maturity.

Example:
₹50,000 deposited for 1 year at 6.5% interest.

Tip:
Use FD laddering to balance liquidity and returns.
""",

    "recurring deposit": """Recurring Deposit (RD).
An RD allows you to save a fixed amount monthly and earn interest.

How to use / How it works:
Deposit a fixed sum every month for the chosen tenure.

Example:
Saving ₹1,000 monthly for 2 years.

Tip:
Ideal for planned expenses like festivals or education.
""",

    "savings account": """Savings Account.
A savings account is a bank account used to deposit money, withdraw funds, and earn modest interest.

How to use / How it works:
Open with KYC; deposit money; use debit card or online banking.

Example:
Keeping salary or emergency funds in a savings account.

Tip:
Maintain minimum balance and enable SMS alerts.
""",

    "current account": """Current Account.
A current account is for businesses and high-volume transactions; it usually doesn’t earn interest.

How to use / How it works:
Open with business documents; used by traders, firms, and companies.

Example:
A shop uses a current account to receive payments and pay suppliers.

Tip:
Choose accounts with low transaction fees.
""",

    "upi": """Unified Payments Interface (UPI).
UPI enables instant money transfers between bank accounts using a UPI ID or QR code.

How to use / How it works:
Install a UPI app, link bank account, set UPI PIN, and send/receive money.

Example:
Scanning a shop's QR code and confirming payment.

Tip:
Verify merchant name before confirming payments.
""",

    "net banking": """Net Banking.
Net banking allows online transactions like fund transfers, bill payments, and viewing statements.

How to use / How it works:
Register on bank website, log in, and perform online transactions.

Example:
Paying electricity bills via net banking.

Tip:
Enable two-factor authentication.
""",

    "mobile banking": """Mobile Banking.
Mobile banking enables banking via smartphone apps.

How to use / How it works:
Download bank app, register, and use for payments and transfers.

Example:
Checking account balance using mobile app.

Tip:
Use only official apps and keep them updated.
""",

    "interest": """Interest.
Interest is the cost of borrowing money or the reward for saving money.

How to use / How it works:
Loans have interest rates; deposits earn interest depending on compounding.

Example:
Savings account interest compounded quarterly.

Tip:
Compare effective annual rates (EAR).
""",

    "apply a loan": """How to Apply for a Bank Loan.
Applying for a loan means submitting documents and meeting eligibility criteria.

How to use / How it works:
Apply online or at a branch, provide KYC and income proof, wait for approval.

Example:
Personal loan with ID proof and salary slips.

Tip:
Maintain good credit history.
""",

    "credit score": """Credit Score.
A credit score represents your creditworthiness based on past borrowings.

How to use / How it works:
Banks check it when approving loans or credit cards.

Example:
A score above 750 improves approval chances.

Tip:
Pay EMIs on time to maintain score.
""",

    "insurance": """Insurance.
Insurance provides financial protection against losses in exchange for premium payments.

How to use / How it works:
Choose plan, compare coverage, submit documents, pay premium.

Example:
Health insurance covering hospital expenses.

Tip:
Read exclusions carefully.
""",

    "government schemes": """Government Schemes.
Schemes like Jan Dhan, PM Kisan, and Mudra support financial inclusion.

How to use / How it works:
Apply through official portals or banks.

Example:
Jan Dhan Yojana for zero-balance accounts.

Tip:
Verify details on official websites.
""",

    "banking security": """Banking Security.
Banking security protects accounts from fraud.

How to use / How it works:
Do not share PIN/OTP; use strong passwords; avoid suspicious links.

Example:
Never share OTP received unexpectedly.

Tip:
Enable transaction alerts.
""",

    "microfinance": """Microfinance.
Microfinance provides small loans to individuals without access to traditional banking.

How to use / How it works:
Apply through microfinance institutions or SHGs.

Example:
Loan for buying a sewing machine.

Tip:
Understand interest terms clearly.
""",

    "financial literacy": """Financial Literacy.
Financial literacy is understanding saving, budgeting, borrowing, and investing.

How to use / How it works:
Track expenses, prepare budgets, learn financial basics.

Example:
Setting aside money for an emergency fund.

Tip:
Start small but be consistent.
""",

    "digital payments": """Digital Payments.
Digital payments use mobile apps, cards, or online banking instead of cash.

How to use / How it works:
Use UPI, net banking, or cards.

Example:
Paying via QR code at a shop.

Tip:
Keep transaction IDs for disputes.
"""
}

# ----- end BANKING_CONTEXT -----
def format_entry(value):
    """
    Accepts either:
      - dict with keys 'title','definition','how_to_use','example','tips'
      - list of strings (old style)
    Returns a nicely formatted multi-paragraph string.
    """
    if isinstance(value, dict):
        parts = []
        if value.get("title"):
            parts.append(f"{value['title']}.")
        if value.get("definition"):
            parts.append(f"{value['definition']}")
        if value.get("how_to_use"):
            parts.append(f"How to use / How it works: {value['how_to_use']}")
        if value.get("example"):
            parts.append(f"{value['example']}")
        if value.get("tips"):
            parts.append(f"Tip: {value['tips']}")
        # join with two newlines for clear paragraphs
        return "\n\n".join(parts)
    elif isinstance(value, (list, tuple)):
        # old-style: choose the longer string(s) and combine them
        # prefer longer strings and join up to 2 items
        sorted_items = sorted(value, key=lambda s: len(s), reverse=True)
        chosen = sorted_items[:2]  # combine two longest
        return "\n\n".join(chosen)
    else:
        return str(value)

# --- Helper: clean text for matching ---
def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or "").strip().lower())

# --- Main improved get_answer ---
def get_answer(query: str) -> str:
    """
    Improved keyword matching:
      1) whole-word / phrase exact match (prefers longer phrases)
      2) fuzzy match with RapidFuzz (prefers higher score and longer/specific keys)
      3) fallback to QA pipeline if no confident match

    Returns formatted KB entry via format_entry(...) when a KB key is selected.
    """
    if not query or not query.strip():
        return "Please ask a question about banking or finance."

    q = normalize(query)

    # 1) Exact whole-word / phrase match (prioritize longest match)
    exact_matches = []
    for key in BANKING_CONTEXT.keys():
        key_norm = normalize(key)
        # build whole-word/phrase regex (escape meta chars)
        pattern = r'\b' + re.escape(key_norm) + r'\b'
        if re.search(pattern, q):
            exact_matches.append(key)

    if exact_matches:
        # choose the longest (most specific) exact match
        best_key = max(exact_matches, key=lambda k: len(k))
        matched_value = BANKING_CONTEXT[best_key]
        return format_entry(matched_value)

    # 2) Fuzzy matching with RapidFuzz
    choices = list(BANKING_CONTEXT.keys())
    try:
        results = process.extract(q, choices, scorer=fuzz.WRatio, limit=3)
    except Exception:
        results = []

    if results:
        # results entries look like: (key, score, idx)
        best_key, best_score, _ = results[0]
        second_score = results[1][1] if len(results) > 1 else 0
        second_key = results[1][0] if len(results) > 1 else None

        # high-confidence match
        if best_score >= 85:
            return format_entry(BANKING_CONTEXT[best_key])

        # medium confidence: prefer the longer/more specific neighbor if scores are close
        if best_score >= 60:
            if second_key and abs(best_score - second_score) <= 8 and len(second_key) > len(best_key):
                return format_entry(BANKING_CONTEXT[second_key])
            return format_entry(BANKING_CONTEXT[best_key])

    # 3) Fallback to QA pipeline on whole KB (useful if KB doesn't match)
    try:
        # Flatten the KB into a single context string
        parts = []
        for v in BANKING_CONTEXT.values():
            if isinstance(v, dict):
                # join dict values (title, definition, how_to_use, example, tips)
                parts.append(" ".join([str(x) for x in v.values() if x]))
            elif isinstance(v, (list, tuple)):
                parts.append(" ".join([str(x) for x in v if x]))
            else:
                parts.append(str(v))
        context_text = " ".join(parts)

        res = qa_pipeline(question=query, context=context_text)
        ans = res.get("answer", "").strip()
        if ans:
            return ans
    except Exception:
        pass

    # final fallback
    return (
        "I'm not sure I have the exact answer for that, but I can tell you about "
        "banking topics like debit cards, credit cards, UPI, loans, insurance, or fixed deposits. "
        "Please ask about one of these!"
    )