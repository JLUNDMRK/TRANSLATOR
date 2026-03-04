import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pathlib import Path
import json

from src.runtime.internal_gpt import InternalGPTRuntime
from src.runtime.ollama_runtime import OllamaRuntime
from src.runtime.copilot import CopilotRuntime
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
        self.decode_dtc_var = tk.BooleanVar(value=False)
        self.text_column_var = tk.StringVar(value="")  # Will be auto-detected

        # Target language selection
        self.target_lang_var = tk.StringVar(value="en")  # en or sv

        # --- Log routing state ---
        # Where should incoming log lines go right now?
        # "api" = prompts+responses, "err" = errors, "other" = general/progress
        self._log_mode = "other"
        self._in_block = False  # between ----- ... ----- and --------------------------------

        row = 0

        # Claim file
        tk.Label(root, text="Claim-fil (Excel/CSV):").grid(row=row, column=0, sticky="w")
        tk.Entry(root, textvariable=self.claim_path_var, width=60).grid(row=row, column=1, padx=5)
        tk.Button(root, text="Bläddra...", command=self.choose_claim).grid(row=row, column=2, padx=5)
        row += 1

        # Decode DTC checkbox
        self.decode_dtc_check = tk.Checkbutton(
            root,
            text="Decode DTC",
            variable=self.decode_dtc_var,
            command=self.on_decode_dtc_change
        )
        self.decode_dtc_check.grid(row=row, column=0, sticky="w")
        row += 1

        # DTC file
        self.dtc_label = tk.Label(root, text="DTC-fil (Excel/CSV):")
        self.dtc_label.grid(row=row, column=0, sticky="w")
        self.dtc_entry = tk.Entry(root, textvariable=self.dtc_path_var, width=60, state="disabled")
        self.dtc_entry.grid(row=row, column=1, padx=5)
        self.dtc_button = tk.Button(root, text="Bläddra...", command=self.choose_dtc, state="disabled")
        self.dtc_button.grid(row=row, column=2, padx=5)
        row += 1

        # Text column selection
        tk.Label(root, text="Textkolumn:").grid(row=row, column=0, sticky="w")
        self.text_col_entry = tk.Entry(root, textvariable=self.text_column_var, width=60)
        self.text_col_entry.grid(row=row, column=1, padx=5)
        tk.Label(root, text="(auto-detekteras när fil väljs)").grid(row=row, column=2, sticky="w", padx=5)
        row += 1

        # Runtime selection
        tk.Label(root, text="Runtime:").grid(row=row, column=0, sticky="w")
        runtime_frame = tk.Frame(root)
        runtime_frame.grid(row=row, column=1, sticky="w", padx=5)

        tk.Radiobutton(
            runtime_frame,
            text="Intern GPT / Closed OpenAI",
            variable=self.runtime_var,
            value="internal",
            command=self.on_runtime_change,
        ).pack(anchor="w")

        tk.Radiobutton(
            runtime_frame,
            text="Ollama (Apple Silicon / NVIDIA)",
            variable=self.runtime_var,
            value="ollama",
            command=self.on_runtime_change,
        ).pack(anchor="w")

        tk.Radiobutton(
            runtime_frame,
            text="Extern OpenAI",
            variable=self.runtime_var,
            value="openai",
            command=self.on_runtime_change,
        ).pack(anchor="w")

        tk.Radiobutton(
            runtime_frame,
            text="GitHub Copilot style",
            variable=self.runtime_var,
            value="copilot",
            command=self.on_runtime_change,
        ).pack(anchor="w")

        row += 1

        # Ollama model dropdown
        tk.Label(root, text="Välj Ollama-modell:").grid(row=row, column=0, sticky="w")
        self.ollama_dropdown = tk.OptionMenu(root, self.ollama_model_choice_var, *ollama_models)
        self.ollama_dropdown.grid(row=row, column=1, sticky="w")
        row += 1

        # Target language dropdown
        tk.Label(root, text="Översätt till språk:").grid(row=row, column=0, sticky="w")
        tk.OptionMenu(root, self.target_lang_var, "en", "sv").grid(row=row, column=1, sticky="w")
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

        # Buttons row
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=10)

        tk.Button(btn_frame, text="Kör", command=self.run).pack(side="left")

        tk.Button(btn_frame, text="Rensa API-logg", command=self.clear_api_log).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Rensa Fel-logg", command=self.clear_error_log).pack(side="left", padx=8)

        tk.Label(btn_frame, textvariable=self.status_var).pack(side="left", padx=12)
        row += 1

        # Notebook (tabs) for logs
        tk.Label(root, text="Loggar:").grid(row=row, column=0, sticky="w")
        row += 1

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=row, column=0, columnspan=3, sticky="nsew")

        # Make the notebook expand
        root.grid_rowconfigure(row, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Tab 1: API Log (prompts + replies)
        api_tab = ttk.Frame(self.notebook)
        self.notebook.add(api_tab, text="API Log (Prompt/Svar)")

        self.api_text = tk.Text(api_tab, height=18, width=110, wrap="word")
        self.api_text.pack(side="left", fill="both", expand=True)
        api_scroll = ttk.Scrollbar(api_tab, orient="vertical", command=self.api_text.yview)
        api_scroll.pack(side="right", fill="y")
        self.api_text.configure(yscrollcommand=api_scroll.set)

        # Tab 2: Errors
        err_tab = ttk.Frame(self.notebook)
        self.notebook.add(err_tab, text="Fel (API & Körning)")

        self.err_text = tk.Text(err_tab, height=18, width=110, wrap="word")
        self.err_text.pack(side="left", fill="both", expand=True)
        err_scroll = ttk.Scrollbar(err_tab, orient="vertical", command=self.err_text.yview)
        err_scroll.pack(side="right", fill="y")
        self.err_text.configure(yscrollcommand=err_scroll.set)

        # Tab 3: Progress (optional, but useful)
        prog_tab = ttk.Frame(self.notebook)
        self.notebook.add(prog_tab, text="Progress")

        self.progress_text = tk.Text(prog_tab, height=18, width=110, wrap="word")
        self.progress_text.pack(side="left", fill="both", expand=True)
        prog_scroll = ttk.Scrollbar(prog_tab, orient="vertical", command=self.progress_text.yview)
        prog_scroll.pack(side="right", fill="y")
        self.progress_text.configure(yscrollcommand=prog_scroll.set)

        self.on_runtime_change()

    def on_runtime_change(self):
        choice = self.runtime_var.get()
        if choice == "ollama":
            self.api_entry.config(state="disabled")
        else:
            self.api_entry.config(state="normal")

    def on_decode_dtc_change(self):
        """Enable/disable DTC file input based on checkbox state"""
        if self.decode_dtc_var.get():
            self.dtc_entry.config(state="normal")
            self.dtc_button.config(state="normal")
        else:
            self.dtc_entry.config(state="disabled")
            self.dtc_button.config(state="disabled")

    def choose_claim(self):
        path = filedialog.askopenfilename(
            title="Välj claim-fil",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("Alla filer", "*.*")],
        )
        if path:
            self.claim_path_var.set(path)
            # Try to detect text column
            try:
                if path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(path)
                else:
                    df = pd.read_csv(path)
                
                # Find text-like columns
                text_columns = []
                for col in df.columns:
                    col_lower = col.lower()
                    # Prioritize common text column names
                    if any(pattern in col_lower for pattern in ["claim", "text", "desc", "description"]):
                        text_columns.append(col)
                
                if text_columns:
                    # Auto-select the first matching column
                    selected_col = text_columns[0]
                    self.text_column_var.set(selected_col)
                    self.status_var.set(f"Kolumn detekterad: {selected_col}")
                else:
                    # If no matching column, show available columns
                    self.status_var.set(f"Tillgängliga kolumner: {', '.join(df.columns[:5])}")
            except Exception as e:
                self.status_var.set(f"Kunde inte läsa fil: {str(e)}")

    def choose_dtc(self):
        path = filedialog.askopenfilename(
            title="Välj DTC-fil",
            filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("Alla filer", "*.*")],
        )
        if path:
            self.dtc_path_var.set(path)

    def clear_api_log(self):
        self.api_text.delete("1.0", tk.END)

    def clear_error_log(self):
        self.err_text.delete("1.0", tk.END)

    def clear_progress_log(self):
        self.progress_text.delete("1.0", tk.END)

    def _append_text(self, widget: tk.Text, text: str):
        widget.insert(tk.END, text + "\n")
        widget.see(tk.END)
        widget.update()

    def log(self, text: str):
        """
        Single logger callback used by both:
        - runtime.set_logger(self.log)
        - progress_callback=self.log

        We route output into:
        - API tab: prompts + replies
        - Errors tab: API errors + other errors
        - Progress tab: everything else
        """

        t = (text or "").strip()

        # Detect start of blocks
        if "----- PROMPT TILL MODELLEN -----" in t:
            self._log_mode = "api"
            self._in_block = True
            self.notebook.select(0)  # jump to API tab
            self._append_text(self.api_text, t)
            return

        if "----- SVAR FRÅN MODELLEN -----" in t:
            self._log_mode = "api"
            self._in_block = True
            self.notebook.select(0)
            self._append_text(self.api_text, t)
            return

        if "----- FEL VID API-ANROP -----" in t:
            self._log_mode = "err"
            self._in_block = True
            self.notebook.select(1)  # jump to Errors tab
            self._append_text(self.err_text, t)
            return

        # Detect end of block
        if t == "--------------------------------" and self._in_block:
            if self._log_mode == "api":
                self._append_text(self.api_text, t)
            elif self._log_mode == "err":
                self._append_text(self.err_text, t)
            else:
                self._append_text(self.progress_text, t)

            self._in_block = False
            self._log_mode = "other"
            return

        # Route normal lines based on current mode
        if self._log_mode == "api":
            self._append_text(self.api_text, t)
        elif self._log_mode == "err":
            self._append_text(self.err_text, t)
        else:
            self._append_text(self.progress_text, t)

    def run(self):
        claim = self.claim_path_var.get().strip()
        dtc = self.dtc_path_var.get().strip()
        api_key = self.api_key_var.get().strip()
        runtime_choice = self.runtime_var.get()
        ollama_model = self.ollama_model_choice_var.get()
        target_lang = self.target_lang_var.get()
        decode_dtc = self.decode_dtc_var.get()

        if not claim or not Path(claim).exists():
            messagebox.showerror("Fel", "Ogiltig claim-fil.")
            return

        # Only validate DTC file if decode_dtc is checked
        if decode_dtc and (not dtc or not Path(dtc).exists()):
            messagebox.showerror("Fel", "DTC-fil måste väljas när 'Decode DTC' är aktiverat.")
            return

        if runtime_choice in ("internal", "openai") and not api_key:
            messagebox.showerror("Fel", "API-nyckel krävs för intern/extern GPT.")
            return
        if runtime_choice == "copilot" and not api_key:
            # Copilot may operate without a key in some setups, but warn the user
            messagebox.showwarning("Varning", "Ingen API-nyckel angiven för Copilot-rutinen.")

        self.status_var.set("Kör pipeline...")
        self.root.update_idletasks()

        try:
            if runtime_choice == "ollama":
                runtime = OllamaRuntime(model=ollama_model)
            elif runtime_choice == "internal":
                runtime = InternalGPTRuntime(
                    api_key=api_key,
                    model=self.model_var.get(),
                    use_internal=True,
                )
            elif runtime_choice == "copilot":
                # Copilot uses the same model field; API key optional
                runtime = CopilotRuntime(
                    model=self.model_var.get(),
                    api_key=api_key or None,
                )
            else:
                runtime = InternalGPTRuntime(
                    api_key=api_key,
                    model=self.model_var.get(),
                    use_internal=False,
                )

            # send all runtime logs into our router
            runtime.set_logger(self.log)

            out_path = run_pipeline(
                claim_file=claim,
                dtc_file=dtc if decode_dtc else None,
                runtime=runtime,
                target_lang=target_lang,
                progress_callback=self.log,
                text_column=self.text_column_var.get() if self.text_column_var.get() else None,
            )

        except Exception as e:
            self.status_var.set("Fel.")
            # Also log the exception to the error tab
            self.log("----- FEL VID KÖRNING -----")
            self.log(str(e))
            self.log("--------------------------------")
            messagebox.showerror("Fel vid körning", str(e))
            return

        self.status_var.set(f"Klar: {out_path}")
        messagebox.showinfo("Klar", f"Ny fil skapad:\n{out_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()