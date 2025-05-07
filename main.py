import streamlit as st
import qrcode
import uuid
from datetime import datetime
import re
import os
import random
import time
from PIL import Image
import base64
from io import BytesIO
# Optional: Uncomment for SQLite logging
# import sqlite3

# Streamlit page configuration
st.set_page_config(page_title="Merchant UPI QR Code Generator", page_icon="💳")

# CSS for styling (green for Success, red for Failed)
st.markdown("""
    <style>
        .success { color: green; font-weight: bold; background-color: #d4edda; padding: 10px; border-radius: 5px; }
        .failed { color: red; font-weight: bold; background-color: #f8d7da; padding: 10px; border-radius: 5px; }
        .pending { color: black; font-weight: bold; }
        .error { color: red; }
    </style>
""", unsafe_allow_html=True)

def validate_upi_id(upi_id):
    """Validate UPI ID format (basic regex check)."""
    pattern = r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$'
    return bool(re.match(pattern, upi_id))

def log_transaction(upi_id, amount, tid, status=None):
    """Log transaction details to a file."""
    log_dir = os.path.dirname('transactions.log')
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    with open("transactions.log", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_str = f" | Status: {status}" if status else ""
        f.write(f"{timestamp} | UPI ID: {upi_id} | Amount: {amount} INR | TID: {tid}{status_str}\n")

# Optional: SQLite logging for persistent storage
# def log_transaction(upi_id, amount, tid, status=None):
#     """Log transaction details to SQLite database."""
#     conn = sqlite3.connect('transactions.db')
#     c = conn.cursor()
#     c.execute('CREATE TABLE IF NOT EXISTS transactions (timestamp TEXT, upi_id TEXT, amount REAL, tid TEXT, status TEXT)')
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     c.execute('INSERT INTO transactions VALUES (?, ?, ?, ?, ?)', (timestamp, upi_id, amount, tid, status))
#     conn.commit()
#     conn.close()

def generate_qr_code(upi_id, amount, tid):
    """Generate QR code and return as base64 string."""
    upi_url = f"upi://pay?pa={upi_id}&pn=Merchant&mc=0000&tid={tid}&am={amount:.2f}&cu=INR"
    qr = qrcode.make(upi_url)
    img_buffer = BytesIO()
    qr.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return img_base64

def check_status(tid):
    """Mock payment status check (simulates Success/Failed)."""
    status = random.choice(["Pending", "Success", "Failed"])
    if status != "Pending":
        log_transaction(None, None, tid, status=status)
    return status

# Streamlit app
st.title("Merchant UPI QR Code Generator")

# Form for UPI ID and amount
with st.form(key="qr_form"):
    upi_id = st.text_input("UPI ID (e.g., yourname@upi)", key="upi_id")
    amount = st.number_input("Amount (INR)", min_value=0.01, step=0.01, key="amount")
    submit_button = st.form_submit_button("Generate QR Code")

# Handle form submission
if submit_button:
    if not upi_id or not amount:
        st.markdown('<p class="error">UPI ID and amount are required.</p>', unsafe_allow_html=True)
    elif not validate_upi_id(upi_id):
        st.markdown('<p class="error">Invalid UPI ID format.</p>', unsafe_allow_html=True)
    elif amount <= 0:
        st.markdown('<p class="error">Amount must be a positive number.</p>', unsafe_allow_html=True)
    else:
        # Generate transaction ID
        tid = str(uuid.uuid4()).replace("-", "")[:12]
        
        # Store transaction details in session state
        st.session_state['transaction'] = {
            "upi_id": upi_id,
            "amount": amount,
            "tid": tid,
            "status": "Pending",
            "qr_image": generate_qr_code(upi_id, amount, tid)
        }
        
        # Log transaction
        log_transaction(upi_id, amount, tid)

# Display transaction details and QR code
if 'transaction' in st.session_state:
    trans = st.session_state['transaction']
    st.subheader("Transaction Details")
    st.write(f"**UPI ID**: {trans['upi_id']}")
    st.write(f"**Amount**: {trans['amount']} INR")
    st.write(f"**Transaction ID**: {trans['tid']}")
    
    # Display status with polling
    status_placeholder = st.empty()
    status = trans['status']
    
    if status == "Pending":
        # Simulate polling (check status every 5 seconds, up to 10 checks)
        for _ in range(10):
            status = check_status(trans['tid'])
            if status != "Pending":
                trans['status'] = status
                st.session_state['transaction'] = trans
                break
            time.sleep(5)
    
    # Display status with appropriate styling
    if status == "Success":
        status_placeholder.markdown('<p class="success">Status: Success</p>', unsafe_allow_html=True)
    elif status == "Failed":
        status_placeholder.markdown('<p class="failed">Status: Failed</p>', unsafe_allow_html=True)
    else:
        status_placeholder.markdown('<p class="pending">Status: Pending</p>', unsafe_allow_html=True)
    
    # Display QR code
    st.subheader("QR Code for Payment")
    st.image(f"data:image/png;base64,{trans['qr_image']}", caption=f"Scan with any UPI app to pay {trans['amount']} INR to {trans['upi_id']}")

# Optional: Display transaction log (for debugging)
if os.path.exists("transactions.log"):
    with open("transactions.log", "r") as f:
        st.text_area("Transaction Log (ephemeral, resets on restart)", f.read(), height=200)