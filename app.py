# app.py
import streamlit as st
import uuid
from datetime import datetime
from PIL import Image
from vision import count_products_in_image

# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
def init_session_state():
    """Initialize session state variables if not already present."""
    if "products" not in st.session_state:
        st.session_state.products = []
    if "bins" not in st.session_state:
        st.session_state.bins = []
    if "counts" not in st.session_state:
        st.session_state.counts = []

# ------------------------------------------------------------------------------
# Data Manipulation Functions
# ------------------------------------------------------------------------------
def add_product(sku: str, name: str, category: str, strain: str) -> None:
    """Add a new product to the inventory."""
    product = {
        "id": uuid.uuid4().hex,
        "sku": sku,
        "name": name,
        "category": category,
        "unitType": "",
        "strain": strain,
        "thcContent": "",
        "cbdContent": "",
        "currentBin": None,
    }
    st.session_state.products.append(product)

def add_bin(code: str, location: str, capacity: int) -> None:
    """Add a new storage bin."""
    bin_obj = {
        "id": uuid.uuid4().hex,
        "code": code,
        "location": location,
        "capacity": capacity,
        "currentCount": 0,
        "products": [],
    }
    st.session_state.bins.append(bin_obj)

def assign_product_to_bin(product_id: str, new_bin_id: str or None) -> None:
    """
    Assign (or unassign) a product to a bin.
    If the product is already assigned to another bin, remove it from the old bin.
    """
    product = next((p for p in st.session_state.products if p["id"] == product_id), None)
    if product is None:
        st.error("Product not found.")
        return

    old_bin_id = product.get("currentBin")
    if old_bin_id and old_bin_id != new_bin_id:
        old_bin = next((b for b in st.session_state.bins if b["id"] == old_bin_id), None)
        if old_bin and product_id in old_bin["products"]:
            old_bin["products"].remove(product_id)
            old_bin["currentCount"] = max(0, old_bin["currentCount"] - 1)

    if new_bin_id:
        new_bin = next((b for b in st.session_state.bins if b["id"] == new_bin_id), None)
        if new_bin:
            new_bin["products"].append(product_id)
            new_bin["currentCount"] += 1
        product["currentBin"] = new_bin_id
    else:
        product["currentBin"] = None

def create_inventory_count(bin_id: str) -> None:
    """
    Create a new inventory count record for a given bin.
    """
    bin_obj = next((b for b in st.session_state.bins if b["id"] == bin_id), None)
    if not bin_obj:
        st.error("Bin not found.")
        return

    count = {
        "id": uuid.uuid4().hex,
        "binId": bin_id,
        "expectedCount": bin_obj["currentCount"],
        "actualCount": 0,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }
    st.session_state.counts.append(count)
    st.success(f"Inventory count started for bin {bin_obj['code']}.")

def update_inventory_count(bin_id: str, actual_count: int) -> None:
    """
    Update the latest pending inventory count for a bin with the actual count from YOLO.
    """
    pending_counts = [c for c in st.session_state.counts if c["binId"] == bin_id and c["status"] == "pending"]
    if not pending_counts:
        st.error("No pending inventory count for this bin. Please start a count first.")
        return
    count_record = pending_counts[-1]
    count_record["actualCount"] = actual_count
    if actual_count == count_record["expectedCount"]:
        count_record["status"] = "completed"
    else:
        count_record["status"] = "discrepancy"
    st.success(f"Inventory count updated: Actual={actual_count}, Expected={count_record['expectedCount']}.")

# ------------------------------------------------------------------------------
# UI Rendering Functions
# ------------------------------------------------------------------------------
def render_products_tab():
    st.header("Products")
    with st.form("add_product_form", clear_on_submit=True):
        sku = st.text_input("SKU")
        name = st.text_input("Name")
        category = st.selectbox("Category", options=["flower", "edibles", "concentrates"])
        strain = st.text_input("Strain Type")
        submitted = st.form_submit_button("Add Product")
        if submitted:
            if not sku or not name:
                st.error("SKU and Name are required.")
            else:
                add_product(sku, name, category, strain)
                st.success("Product added!")
    st.subheader("Product List")
    if st.session_state.products:
        for product in st.session_state.products:
            with st.expander(f"{product['name']} (SKU: {product['sku']})"):
                st.write(f"**Category:** {product['category']}")
                st.write(f"**Strain:** {product['strain']}")
                current_bin = product.get("currentBin")
                if current_bin:
                    bin_obj = next((b for b in st.session_state.bins if b["id"] == current_bin), None)
                    if bin_obj:
                        st.write(f"**Assigned Bin:** {bin_obj['code']} ({bin_obj['location']})")
                    else:
                        st.write("**Assigned Bin:** Unknown")
                else:
                    st.write("**Assigned Bin:** Unassigned")
                with st.form(key=f"assign_form_{product['id']}", clear_on_submit=True):
                    bin_options = [("Unassigned", None)]
                    for b in st.session_state.bins:
                        bin_options.append((f"{b['code']} ({b['location']})", b["id"]))
                    initial_index = 0
                    if current_bin:
                        for i, (_, bin_id) in enumerate(bin_options):
                            if bin_id == current_bin:
                                initial_index = i
                                break
                    selected = st.selectbox(
                        "Assign to Bin",
                        options=bin_options,
                        format_func=lambda x: x[0],
                        index=initial_index,
                    )
                    if st.form_submit_button("Assign"):
                        assign_product_to_bin(product["id"], selected[1])
                        st.success("Product assignment updated!")
    else:
        st.info("No products added yet.")

def render_bins_tab():
    st.header("Storage Bins")
    with st.form("add_bin_form", clear_on_submit=True):
        code = st.text_input("Bin Code")
        location = st.text_input("Location")
        capacity = st.number_input("Capacity", min_value=1, value=100, step=1)
        submitted = st.form_submit_button("Add Storage Bin")
        if submitted:
            if not code or not location:
                st.error("Bin Code and Location are required.")
            else:
                add_bin(code, location, capacity)
                st.success("Storage bin added!")
    st.subheader("Storage Bins List")
    if st.session_state.bins:
        for bin_obj in st.session_state.bins:
            with st.expander(f"{bin_obj['code']} ({bin_obj['location']})"):
                st.write(f"**Capacity:** {bin_obj['currentCount']} / {bin_obj['capacity']}")
                st.write(f"**Number of Products:** {len(bin_obj['products'])}")
                if st.button("Start Count", key=f"start_count_{bin_obj['id']}"):
                    create_inventory_count(bin_obj["id"])
                st.markdown("#### Image-Based Inventory Count")
                uploaded_file = st.file_uploader("Upload bin image for count", type=["jpg", "jpeg", "png"], key=f"upload_{bin_obj['id']}")
                if uploaded_file is not None:
                    st.info("Processing image...")
                    actual_count, processed_image = count_products_in_image(uploaded_file.read())
                    st.image(processed_image, caption=f"Detected count: {actual_count}", use_column_width=True)
                    if st.button("Update Count", key=f"update_count_{bin_obj['id']}"):
                        update_inventory_count(bin_obj["id"], actual_count)
    else:
        st.info("No storage bins added yet.")

def render_inventory_tab():
    st.header("Inventory Counts")
    if st.session_state.counts:
        for count in st.session_state.counts:
            bin_obj = next((b for b in st.session_state.bins if b["id"] == count["binId"]), None)
            bin_display = bin_obj["code"] if bin_obj else "Unknown"
            st.write(f"**Bin:** {bin_display}")
            st.write(f"**Expected Count:** {count['expectedCount']}")
            st.write(f"**Actual Count:** {count['actualCount']}")
            st.write(f"**Status:** {count['status']}")
            timestamp = datetime.fromisoformat(count["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"**Timestamp:** {timestamp}")
            st.markdown("---")
    else:
        st.info("No inventory counts available.")

# ------------------------------------------------------------------------------
# Main Application
# ------------------------------------------------------------------------------
def main():
    st.title("Cannabis Inventory Management System")
    init_session_state()
    tabs = st.tabs(["Products", "Storage Bins", "Inventory Counts"])
    with tabs[0]:
        render_products_tab()
    with tabs[1]:
        render_bins_tab()
    with tabs[2]:
        render_inventory_tab()

if __name__ == "__main__":
    main()
