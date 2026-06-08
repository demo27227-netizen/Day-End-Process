import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Day End Process - Allocation",
    layout="wide"
)

st.title("Day End Process - Allocation")

# ================= FILE UPLOAD =================

allocation_file = st.file_uploader(
    "Upload Allocation File",
    type=["csv", "xls", "xlsx"]
)

client_file = st.file_uploader(
    "Upload Client / NetClosing File",
    type=["csv", "xls", "xlsx"]
)

remove_clients = ["11858", "J1", "J2", "OWN"]

# ================= PROCESS =================

if st.button("Process Files"):

    if allocation_file is None or client_file is None:
        st.error("Please upload both files.")
        st.stop()

    # ================= READ FIRST FILE =================
    # Allocation File

    try:

        if allocation_file.name.lower().endswith(".csv"):
            df1 = pd.read_csv(
                allocation_file,
                low_memory=False
            )
        else:
            df1 = pd.read_excel(
                allocation_file
            )

        df1 = df1[
            [
                "Client Code",
                "Allocated Cash/Cash Equivalent Collateral"
            ]
        ]

    except Exception as e:

        st.error(f"Allocation File Error:\n{e}")
        st.stop()

    # ================= CLEAN FIRST FILE =================

    df1["Client Code"] = (
        df1["Client Code"]
        .astype(str)
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"[^A-Za-z0-9]", "", regex=True)
    )

    df1 = df1[
        (df1["Client Code"] != "")
        &
        (df1["Client Code"] != "0")
    ]

    df1 = df1[
        ~df1["Client Code"].isin(remove_clients)
    ]

    df1["Allocated Cash/Cash Equivalent Collateral"] = (
        pd.to_numeric(
            df1["Allocated Cash/Cash Equivalent Collateral"],
            errors="coerce"
        )
        .round(2)
    )

    pivot1 = df1.groupby(
        "Client Code",
        as_index=False
    ).agg({
        "Allocated Cash/Cash Equivalent Collateral": "sum"
    })

    # ================= READ SECOND FILE =================
    # Client / NetClosing File

    try:

        if client_file.name.lower().endswith(".csv"):
            df2 = pd.read_csv(
                client_file,
                low_memory=False
            )
        else:
            df2 = pd.read_excel(
                client_file
            )

        df2 = df2[
            [
                "Client",
                "NetClosing (C)"
            ]
        ]

    except Exception as e:

        st.error(f"Client File Error:\n{e}")
        st.stop()

    # ================= CLEAN SECOND FILE =================

    df2["Client"] = (
        df2["Client"]
        .astype(str)
        .str.strip()
        .str.replace(r"[\[\]]", "", regex=True)
        .str.replace(r"[^A-Za-z0-9]", "", regex=True)
    )

    df2 = df2[
        (df2["Client"] != "")
        &
        (df2["Client"] != "0")
    ]

    df2 = df2[
        ~df2["Client"].isin(remove_clients)
    ]

    df2["NetClosing (C)"] = (
        pd.to_numeric(
            df2["NetClosing (C)"],
            errors="coerce"
        )
        .round(2)
    )

    pivot2 = df2.groupby(
        "Client",
        as_index=False
    ).agg({
        "NetClosing (C)": "sum"
    })

    # ================= MERGE =================

    final_df = pd.merge(
        pivot1,
        pivot2,
        left_on="Client Code",
        right_on="Client",
        how="left"
    )

    final_df = final_df[
        [
            "Client Code",
            "Allocated Cash/Cash Equivalent Collateral",
            "NetClosing (C)"
        ]
    ]

    # ================= RENAME =================

    final_df.columns = [
        "Row Labels",
        "Credit Code",
        "Allocation"
    ]

    final_df["Credit Code"] = pd.to_numeric(
        final_df["Credit Code"],
        errors="coerce"
    ).round(2)

    final_df["Allocation"] = pd.to_numeric(
        final_df["Allocation"],
        errors="coerce"
    ).round(2)

    # ================= T/F =================

    def calculate_tf(row):

        allocation = row["Allocation"]
        credit = row["Credit Code"]

        if pd.isna(allocation) or pd.isna(credit):
            return "#N/A"

        return abs(allocation - credit) < 1e-9

    final_df["T/F"] = final_df.apply(
        calculate_tf,
        axis=1
    )

    # ================= DIFF =================

    def calculate_diff(row):

        allocation = row["Allocation"]
        credit = row["Credit Code"]

        if pd.isna(allocation) or pd.isna(credit):
            return "#N/A"

        diff = allocation - credit

        return (
            0
            if abs(diff) < 1e-9
            else round(diff, 2)
        )

    final_df["DIFF"] = final_df.apply(
        calculate_diff,
        axis=1
    )

    final_df = final_df.sort_values(
        by="Row Labels"
    )

    # ================= DISPLAY COPY =================

    display_df = final_df.copy()

    display_df["Credit Code"] = (
        display_df["Credit Code"]
        .apply(
            lambda x: "#N/A"
            if pd.isna(x)
            else round(x, 2)
        )
    )

    display_df["Allocation"] = (
        display_df["Allocation"]
        .apply(
            lambda x: "#N/A"
            if pd.isna(x)
            else round(x, 2)
        )
    )

    # ================= DISPLAY =================

    st.success(
        "Processing Completed Successfully"
    )

    st.dataframe(
        display_df,
        use_container_width=True
    )

    # ================= DOWNLOAD =================

    csv_data = display_df.to_csv(
        index=False
    ).encode("utf-8")

    file_name = (
        f"Day_End_Process_Allocation_"
        f"{datetime.now().strftime('%d-%m-%Y')}.csv"
    )

    st.download_button(
        label="Download Output CSV",
        data=csv_data,
        file_name=file_name,
        mime="text/csv"
    )

