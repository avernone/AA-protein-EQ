import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# --- Streamlit page configuration ---
st.set_page_config(page_title="UniProt E/Q Ratio Ranking", page_icon="🧬", layout="wide")

st.title("🧬 UniProt E/Q Ratio Ranking App")

st.write("""
Enter **one or more UniProt Accession Codes (AC)** separated by commas.  
The app will calculate the **E/Q ratio** (glutamic acid / glutamine) for each protein,  
then rank and visualize them from lowest to highest ratio.

Example: `P69905, P68871, P02042`
""")

# --- User input ---
ac_input = st.text_input("UniProt AC list:", "")

if ac_input:
    ac_list = [x.strip() for x in ac_input.split(",") if x.strip()]
    ratio_results = {}

    # --- Function to compute ratio E/Q ---
    def compute_eq_ratio(seq):
        e = seq.count("E")
        q = seq.count("Q")
        return e / q if q != 0 else None

    # --- Process each protein ---
    for ac in ac_list:
        url = f"https://rest.uniprot.org/uniprotkb/{ac}.fasta"
        response = requests.get(url)

        if response.status_code == 200 and ">" in response.text:
            lines = response.text.splitlines()
            sequence = "".join([l.strip() for l in lines if not l.startswith(">")])
            ratio = compute_eq_ratio(sequence)
            ratio_results[ac] = ratio
        else:
            ratio_results[ac] = None
            st.warning(f"⚠️ Invalid UniProt code or sequence not found: {ac}")

    # --- Create DataFrame ---
    df = pd.DataFrame(list(ratio_results.items()), columns=["Protein (AC)", "E/Q ratio"])
    df = df.dropna().sort_values(by="E/Q ratio", ascending=True)

    # --- Display table ---
    st.subheader("E/Q Ratio Table (sorted ascending)")
    st.dataframe(df)

    # --- Bar plot ---
    st.subheader("Bar Plot of Proteins Sorted by E/Q Ratio")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df["Protein (AC)"], df["E/Q ratio"], color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("E/Q ratio (E / Q)")
    plt.xlabel("Protein (UniProt AC)")
    plt.tight_layout()
    st.pyplot(fig)

    # --- Optional: download results ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV Results",
        data=csv,
        file_name="eq_ratio_ranking.csv",
        mime="text/csv"
    )

