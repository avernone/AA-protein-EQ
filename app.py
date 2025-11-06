import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# --- Streamlit page configuration ---
st.set_page_config(page_title="UniProt E/Q Ratio Ranking", page_icon="🧬", layout="wide")

st.title("🧬 UniProt E/Q Ratio Ranking App")

st.write("""
Enter **one or more UniProt Accession Codes (AC)** separated by commas.  
The app will calculate the **E/Q ratio** (glutamic acid / glutamine) for each protein,  
and show detailed UniProt information.

Example: `P69905, P68871, P02042`
""")

# --- Link alla tabella amminoacidi ---
with st.expander("📘 Amino Acid Reference Table (click to view)"):
    aa_data = [
        ["Alanine", "Ala", "A"],
        ["Arginine", "Arg", "R"],
        ["Asparagine", "Asn", "N"],
        ["Aspartic acid", "Asp", "D"],
        ["Cysteine", "Cys", "C"],
        ["Glutamine", "Gln", "Q"],
        ["Glutamic acid", "Glu", "E"],
        ["Glycine", "Gly", "G"],
        ["Histidine", "His", "H"],
        ["Isoleucine", "Ile", "I"],
        ["Leucine", "Leu", "L"],
        ["Lysine", "Lys", "K"],
        ["Methionine", "Met", "M"],
        ["Phenylalanine", "Phe", "F"],
        ["Proline", "Pro", "P"],
        ["Serine", "Ser", "S"],
        ["Threonine", "Thr", "T"],
        ["Tryptophan", "Trp", "W"],
        ["Tyrosine", "Tyr", "Y"],
        ["Valine", "Val", "V"]
    ]
    aa_df = pd.DataFrame(aa_data, columns=["Full Name", "3-letter", "1-letter"])
    st.dataframe(aa_df, hide_index=True, use_container_width=True)

# --- User input ---
ac_input = st.text_input("UniProt AC list:", "")

if ac_input:
    ac_list = [x.strip() for x in ac_input.split(",") if x.strip()]
    ratio_results = []

    # --- Function to compute amino acid stats ---
    def analyze_sequence(seq):
        e = seq.count("E")
        q = seq.count("Q")
        total = len(seq)
        ratio = e / q if q != 0 else None
        perc_e = (e / total) * 100 if total > 0 else None
        perc_q = (q / total) * 100 if total > 0 else None
        return ratio, total, perc_e, perc_q

    # --- Process each UniProt ID ---
    for ac in ac_list:
        fasta_url = f"https://rest.uniprot.org/uniprotkb/{ac}.fasta"
        meta_url = f"https://rest.uniprot.org/uniprotkb/{ac}.json"

        fasta_response = requests.get(fasta_url)
        meta_response = requests.get(meta_url)

        if fasta_response.status_code == 200 and ">" in fasta_response.text:
            lines = fasta_response.text.splitlines()
            sequence = "".join([l.strip() for l in lines if not l.startswith(">")])
            ratio, total_len, perc_e, perc_q = analyze_sequence(sequence)

            # --- Extract metadata ---
            if meta_response.status_code == 200:
                data = meta_response.json()
                entry_name = data.get("uniProtkbId", ac)  # es. HBB_HUMAN
                protein_name = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "N/A")
                description = data.get("comments", [{}])[0].get("texts", [{}])[0].get("value", "")
            else:
                entry_name = ac
                protein_name = description = "N/A"

            uniprot_link = f"https://www.uniprot.org/uniprotkb/{ac}/entry"

            ratio_results.append({
                "Entry Name": entry_name,
                "Protein Name": protein_name,
                "Description": description,
                "Length (AA)": total_len,
                "% E": perc_e,
                "% Q": perc_q,
                "E/Q ratio": ratio,
                "UniProt Link": uniprot_link
            })
        else:
            st.warning(f"⚠️ Invalid UniProt code or sequence not found: {ac}")

    # --- Create DataFrame ---
    df = pd.DataFrame(ratio_results)
    df = df.dropna(subset=["E/Q ratio"]).sort_values(by="E/Q ratio", ascending=True)

    st.subheader("📊 E/Q Ratio Table (sorted ascending)")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # --- Bar plot ---
    st.subheader("📈 Bar Plot of Proteins Sorted by E/Q Ratio")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df["Entry Name"], df["E/Q ratio"], color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("E/Q ratio (E / Q)")
    plt.xlabel("Protein (Entry Name)")
    plt.tight_layout()
    st.pyplot(fig)

    # --- Save Data + Plot to Excel ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="E_Q_Ratio")

        # Save chart image
        img_bytes = BytesIO()
        fig.savefig(img_bytes, format="png")
        img_bytes.seek(0)

        worksheet = writer.sheets["E_Q_Ratio"]
        worksheet.insert_image("K2", "eq_ratio_plot.png", {"image_data": img_bytes})

    st.download_button(
        label="⬇️ Download Excel (Data + Plot)",
        data=output.getvalue(),
        file_name="eq_ratio_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

