import pandas as pd
from pathlib import Path

def run_pipeline(claim_file, dtc_file, runtime, target_lang="en", progress_callback=None):
    """
    claim_file: path to claim Excel/CSV
    dtc_file: path to DTC Excel/CSV
    runtime: InternalGPTRuntime or OllamaRuntime
    target_lang: "en" or "sv"
    progress_callback: function for logging progress
    """

    # Load files
    claim_df = pd.read_excel(claim_file) if claim_file.endswith(".xlsx") else pd.read_csv(claim_file)
    dtc_df = pd.read_excel(dtc_file) if dtc_file.endswith(".xlsx") else pd.read_csv(dtc_file)

    # Ensure required columns exist
    if "CLAIM_TEXT_DESC" not in claim_df.columns:
        raise ValueError("CLAIM_TEXT_DESC saknas i claim-filen.")

    texts = claim_df["CLAIM_TEXT_DESC"].fillna("").tolist()

    detected_languages = []
    translated_texts = []

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

        if progress_callback:
            progress_callback(f"Rad {i}: Klar.")

    # Add new columns
    claim_df["detected_language"] = detected_languages
    claim_df["translated_text"] = translated_texts

    # Save output
    out_path = Path(claim_file).with_name("claim_translated_output.xlsx")
    claim_df.to_excel(out_path, index=False)

    if progress_callback:
        progress_callback(f"Pipeline klar. Sparad till: {out_path}")

    return str(out_path)
