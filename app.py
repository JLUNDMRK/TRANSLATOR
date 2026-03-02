import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import json

from src.runtime.internal_gpt import InternalGPTRuntime
from src.runtime.ollama_runtime import OllamaRuntime
from src.pipeline.pipeline import run_pipeline

# Load settings
with open("config/settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

ollama_models = settings.get("ollama_models", [])
default_ollama_model = ollama_models[0] if ollama_models else ""


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DTC Analyzer")

        self.claim_path_var = tk.StringVar()
        self.dtc_path_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.model_var = tk.StringVar(value="gpt-4o")
        self.status_var = tk.StringVar(value="Redo.")
        self.runtime_var = tk.StringVar(value="internal")
        self.ollama_model_choice_var = tk.StringVar(value=default_ollama_model)

        row = 0

        # Claim file
        tk.Label(root, text="Claim-fil (Excel/CSV):").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.claim_path_var, width=60).grid(row=row, column=1, padx=5)
        tk.Button(root, text="Bläddra...", command=self.choose_claim).grid(row=row, column=2, padx=5)
        row += 1

        # DTC file
        tk.Label(root, text="DTC-fil (Excel/CSV):").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.dtc_path_var, width=60).grid(row=row, column=1, padx=5)
        tk.Button(root, text="Bläddra...", command=self.choose_dtc).grid(row=row, column=2, padx=5)
        row += 1

        # Runtime selection
        tk.Label(root, text="Runtime:").grid(row=row, column=0, sticky="w")
        runtime_frame = tk.Frame(root)
        runtime_frame.grid(row=row, column=1, sticky="w", padx=5)

        tk.Radiobutton(runtime_frame, text="Intern GPT / Closed OpenAI",
                       variable=self.runtime_var, value="internal",
                       command=self.on_runtime_change).pack(anchor="w")

        tk.Radiobutton(runtime_frame, text="Ollama (Apple Silicon / NVIDIA)",
                       variable=self.runtime_var, value="ollama",
                       command=self.on_runtime_change).pack(anchor="w")

        tk.Radiobutton(runtime_frame, text="Extern OpenAI",
                       variable=self.runtime_var, value="openai",
                       command=self.on_runtime_change).pack(anchor="w")
        row += 1

        # Ollama model dropdown
        tk.Label(root, text="Välj Ollama-modell:").grid(row=row, column=0, sticky="w")
        self.ollama_dropdown = tk.OptionMenu(root, self.ollama_model_choice_var, *ollama_models)
        self.ollama_dropdown.grid(row=row, column=1, sticky="w")
        row += 1

        # API key
        tk.Label(root, text="API-nyckel (intern/extern):").grid(row=row, column=0, sticky="w")
        self.api_entry = tk.Entry(root, textvariable=self.api_key_var, width=60, show="*")
        self.api_entry.grid(row=row, column=1, padx=5)
        row += 1

        # GPT model name
        tk.Label(root, text="Modellnamn (GPT):").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.model_var, width=30).grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        # Run button + status
        tk.Button(root, text="Kör", command=self.run).grid(row=row, column=0, pady=10)
        tk.Label(root, textvariable=self.status_var).grid(row=row, column=1, sticky="w")
        row += 1

        # Progress text box
        self.progress_text = tk.Text(root, height=10, width=70)
        self.progress_text.grid(row=row, column=0, columnspan=3)
        row += 1

        self.on_runtime_change()

    def on_runtime_change(self):
        choice = self.runtime_var.get()

        if choice == "ollama":
            self.api_entry.config(state="disabled")
        elif choice == "openai":
            self.api_entry.config(state="normal")
        else:  # internal
            self.api_entry.config(state="normal")

    def choose_claim(self):
        path = filedialog.askopenfilename(
            title="Välj claim-fil",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("Alla filer", "*.*")]
        )
        if path:
            self.claim_path_var.set(path)

    def choose_dtc(self):
        path = filedialog.askopenfilename(
            title="Välj DTC-fil",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("Alla filer", "*.*")]
        )
        if path:
            self.dtc_path_var.set(path)

    def run(self):
        claim = self.claim_path_var.get().strip()
        dtc = self.dtc_path_var.get().strip()
        api_key = self.api_key_var.get().strip()
        runtime_choice = self.runtime_var.get()
        ollama_model = self.ollama_model_choice_var.get()

        if not claim or not Path(claim).exists():
            messagebox.showerror("Fel", "Ogiltig claim-fil.")
            return

        if not dtc or not Path(dtc).exists():
            messagebox.showerror("Fel", "Ogiltig DTC-fil.")
            return

        if runtime_choice in ("internal", "openai") and not api_key:
            messagebox.showerror("Fel", "API-nyckel krävs för intern/extern GPT.")
            return

        self.status_var.set("Kör pipeline...")
        self.root.update_idletasks()

        try:
            if runtime_choice == "ollama":
                runtime = OllamaRuntime(model=ollama_model)
            elif runtime_choice == "internal":
                runtime = InternalGPTRuntime(api_key=api_key, model=self.model_var.get(), use_internal=True)
            else:
                runtime = InternalGPTRuntime(api_key=api_key, model=self.model_var.get(), use_internal=False)

            out_path = run_pipeline(claim, dtc, runtime)

        except Exception as e:
            self.status_var.set("Fel.")
            messagebox.showerror("Fel vid körning", str(e))
            return

        self.status_var.set(f"Klar: {out_path}")
        messagebox.showinfo("Klar", f"Ny fil skapad:\n{out_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
