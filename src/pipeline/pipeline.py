import pandas as pd
from pathlib import Path
from typing import Optional
from .dtc_lookup import load_dtc_database, lookup_dtc_entries
from .extractor import extract_dtc_codes

def run_pipeline(claim_file, dtc_file: Optional[str], runtime, target_lang="en", progress_callback=None, text_column=None):
    """
    claim_file: path to claim Excel/CSV
    dtc_file: path to DTC Excel/CSV (optional)
    runtime: InternalGPTRuntime, OllamaRuntime or CopilotRuntime
    target_lang: "en" or "sv"
    progress_callback: function for logging progress
    text_column: name of the text column to process (auto-detect if None)
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

    # Find text column if not specified
    if text_column is None:
        # Try common column names
        for col_name in ["CLAIM_TEXT_DESC", "claim_text_desc", "description", "Description", "text", "Text", "claim", "Claim"]:
            if col_name in claim_df.columns:
                text_column = col_name
                break
        
        # If still not found, try case-insensitive match for common patterns
        if text_column is None:
            for col in claim_df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in ["claim", "text", "desc", "description"]):
                    text_column = col
                    break
    
    # Ensure we found a text column
    if text_column is None:
        raise ValueError(
            f"Kunde inte hitta textkolumn i filen.\n"
            f"Tillgängliga kolumner: {', '.join(claim_df.columns)}\n"
            f"Förväntade namn: CLAIM_TEXT_DESC, description, text eller liknande."
        )
    
    if text_column not in claim_df.columns:
        raise ValueError(
            f"Kolumnen '{text_column}' finns inte i filen.\n"
            f"Tillgängliga kolumner: {', '.join(claim_df.columns)}"
        )
    
    if progress_callback:
        progress_callback(f"Använder kolumn: '{text_column}'")

    texts = claim_df[text_column].fillna("").tolist()

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
