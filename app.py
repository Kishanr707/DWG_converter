import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import requests

API_URL = "https://api2convert.com/v1/convert"

# Optional built-in key so the app works out of the box on any PC.
# Paste the office key between the quotes, or leave "" to make users paste it once.
DEFAULT_API_KEY = "f8140f7f559be33928cb025656a9ade1"

# A key typed into the box is remembered between launches in this small per-user file.
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NCS_DWG_Converter")
KEY_FILE = os.path.join(CONFIG_DIR, "api_key.txt")


def load_saved_key():
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            saved = f.read().strip()
    except Exception:
        saved = ""
    return saved or DEFAULT_API_KEY


def save_key(key):
    try:
        if not key or key == DEFAULT_API_KEY:
            # Nothing custom to remember: fall back to the built-in key next time.
            if os.path.exists(KEY_FILE):
                os.remove(KEY_FILE)
            return
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key)
    except Exception:
        pass


def convert_files(api_key, file_paths, status_var, progress_bar):
    if not api_key:
        messagebox.showerror("Error", "Please enter a valid API key.")
        return

    total = len(file_paths)
    progress_bar["maximum"] = total
    progress_bar["value"] = 0

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    output_dir = os.path.join(desktop_path, "NCS_Converted_DWG")
    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    fail_count = 0

    for index, file_path in enumerate(file_paths, 1):
        file_name = os.path.basename(file_path)
        status_var.set(f"Converting ({index}/{total}): {file_name}...")
        root.update_idletasks()

        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    API_URL,
                    files={"file": f},
                    data={"target": "dwg", "version": "AC1018", "auth": api_key},
                    timeout=60,
                )

            if response.status_code == 200:
                res_json = response.json()
                download_url = res_json.get("url")
                file_data = requests.get(download_url, timeout=60)
                out_path = os.path.join(output_dir, file_name)
                with open(out_path, "wb") as out_f:
                    out_f.write(file_data.content)
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1

        progress_bar["value"] = index
        root.update_idletasks()

    status_var.set(
        f"Done! Success: {success_count}, Failed: {fail_count}. "
        "Saved to Desktop\\NCS_Converted_DWG"
    )
    messagebox.showinfo(
        "Complete",
        f"Batch conversion finished!\nSuccessfully converted: {success_count}"
        f"\nFailed: {fail_count}\n\nSaved in:\nDesktop\\NCS_Converted_DWG",
    )


def start_conversion_thread():
    api_key = api_entry.get().strip()
    file_paths = listbox.get(0, tk.END)
    if not file_paths:
        messagebox.showwarning("Warning", "Please add at least one DWG file.")
        return
    threading.Thread(
        target=convert_files,
        args=(api_key, file_paths, status_var, progress_bar),
        daemon=True,
    ).start()


def browse_files():
    filenames = filedialog.askopenfilenames(
        title="Select DWG Files", filetypes=[("DWG Files", "*.dwg")]
    )
    existing = listbox.get(0, tk.END)
    for name in filenames:
        if name not in existing:
            listbox.insert(tk.END, name)


def remove_selected():
    for i in reversed(listbox.curselection()):
        listbox.delete(i)


def clear_list():
    listbox.delete(0, tk.END)


root = tk.Tk()
root.title("NCS DWG Converter")
root.geometry("600x500")
root.minsize(550, 450)

key_frame = tk.LabelFrame(root, text=" API Key ", padx=10, pady=10)
key_frame.pack(fill="x", padx=15, pady=10)
tk.Label(key_frame, text="Enter API Key:").pack(side="left")
key_var = tk.StringVar(value=load_saved_key())
key_var.trace_add("write", lambda *args: save_key(key_var.get().strip()))
api_entry = tk.Entry(key_frame, show="*", textvariable=key_var)
api_entry.pack(side="left", padx=(0, 10), expand=True, fill="x")

list_frame = tk.LabelFrame(root, text=" Selected DWG Files ", padx=10, pady=10)
list_frame.pack(fill="both", expand=True, padx=15, pady=5)
listbox = tk.Listbox(
    list_frame, selectmode="extended", width=50, height=10, exportselection=False
)
listbox.pack(side="left", fill="both", expand=True)
scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
scrollbar.pack(side="right", fill="y")
listbox.config(yscrollcommand=scrollbar.set)

btn_frame = tk.Frame(root)
btn_frame.pack(fill="x", padx=15, pady=5)
tk.Button(btn_frame, text="Add DWG Files...", command=browse_files, width=15).pack(side="left")
tk.Button(btn_frame, text="Remove Selected", command=remove_selected, width=15).pack(side="left", padx=(5, 0))
tk.Button(btn_frame, text="Clear List", command=clear_list, width=12).pack(side="left", padx=(5, 0))

convert_btn = tk.Button(
    root,
    text="CONVERT TO AUTOCAD 2004",
    bg="#005A9E",
    fg="white",
    font=("Arial", 10, "bold"),
    command=start_conversion_thread,
    height=2,
)
convert_btn.pack(fill="x", padx=15, pady=10)

status_var = tk.StringVar(value="Ready.")
tk.Label(root, textvariable=status_var, anchor="w", font=("Arial", 9)).pack(fill="x", padx=15)
progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate")
progress_bar.pack(fill="x", padx=15, pady=(5, 15))

root.mainloop()