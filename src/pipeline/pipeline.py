import pandas as pd
from pathlib import Path
from typing import Optional
from .dtc_lookup import load_dtc_database, lookup_dtc_entries
from .extractor import extract_dtc_codes

def run_pipeline(claim_file, dtc_file: Optional[str], runtime, target_lang="en", progress_callback=None):
    """
    claim_file: path to claim Excel/CSV
    dtc_file: path to DTC Excel/CSV (optional)
    runtime: InternalGPTRuntime, OllamaRuntime or CopilotRuntime
    target_lang: "en" or "sv"
    progress_callback: function for logging progress
    """

    # Load claim file
    claim_df = pd.read_excel(claim_file) if claim_file.endswith(".xlsx") else pd.read_csv(claim_file)

    # Load DTC database if provided
    dtc_map = None
    if dtc_file:
        if progress_callback:
            progress_callback(f"Laddar DTC-databas från: {dtc_file}")
        try:
            dtc_map = load_dtc_database(dtc_file)
            if progress_callback:
                progress_callback(f"DTC-databas laddad: {len(dtc_map)} koder")
        except Exception as e:
            if progress_callback:
                progress_callback(f"Fel vid laddning av DTC-databas: {e}")

    # Ensure required columns exist
    if "CLAIM_TEXT_DESC" not in claim_df.columns:
        raise ValueError("CLAIM_TEXT_DESC saknas i claim-filen.")

    texts = claim_df["CLAIM_TEXT_DESC"].fillna("").tolist()

    detected_languages = []
    translated_texts = []
    dtc_codes_list = []
    dtc_details_list = []

    for i, text in enumerate(texts):
        if progress_callback:
            progress_callback(f"Rad {i}: Detekterar språk...")

        # Language detection
        try:
            lang = runtime.detect_language(text)
        except Exception:
            lang = "unknown"

        detected_languages.append(lang)

        if progress_callback:
            progress_callback(f"Rad {i}: Språk = {lang}, översätter till {target_lang}...")

        # Translation
        try:
            translated = runtime.translate(text, target_lang)
        except Exception:
            translated = text  # fallback

        translated_texts.append(translated)

        # Extract and decode DTC codes if DTC database is available
        if dtc_map:
            extracted_codes = extract_dtc_codes(text)
            dtc_codes_list.append(", ".join(extracted_codes) if extracted_codes else "")
            
            if extracted_codes:
                dtc_entries = lookup_dtc_entries(dtc_map, extracted_codes)
                # Format DTC details as a readable string
                details = []
                for entry in dtc_entries:
                    detail = f"{entry['dtc_no']}: {entry['heading']}"
                    if entry.get('component'):
                        detail += f" - {entry['component']}"
                    details.append(detail)
                dtc_details_list.append(" | ".join(details) if details else "")
            else:
                dtc_details_list.append("")
        else:
            dtc_codes_list.append("")
            dtc_details_list.append("")

        if progress_callback:
            progress_callback(f"Rad {i}: Klar.")

    # Add new columns
    claim_df["detected_language"] = detected_languages
    claim_df["translated_text"] = translated_texts
    
    # Add DTC columns if DTC decoding was performed
    if dtc_map:
        claim_df["extracted_dtc_codes"] = dtc_codes_list
        claim_df["dtc_details"] = dtc_details_list

    # Save output
    out_path = Path(claim_file).with_name("claim_translated_output.xlsx")
    claim_df.to_excel(out_path, index=False)

    if progress_callback:
        progress_callback(f"Pipeline klar. Sparad till: {out_path}")

    return str(out_path)
