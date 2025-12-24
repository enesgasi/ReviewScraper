import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import pandas as pd
import time
import datetime
import os
import threading

# ==========================
# API KEY
# ==========================
STEAM_API_KEY = '5E9B70CD0A6DFFF6349F5A5025A6E848'

# ==========================
# STEAM USERNAME RESOLUTION
# ==========================
def resolve_usernames(steamids, api_key=STEAM_API_KEY, batch_size=100, delay=1.0):
    mapping = {}
    steamids = [str(s) for s in set(steamids) if s]

    if not steamids or not api_key:
        return {sid: sid for sid in steamids}

    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    headers = {"User-Agent": "SteamReviewFetcher/1.0"}

    for i in range(0, len(steamids), batch_size):
        batch = steamids[i:i + batch_size]
        try:
            resp = requests.get(
                url,
                params={"key": api_key, "steamids": ",".join(batch)},
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            players = resp.json().get("response", {}).get("players", [])
            for p in players:
                mapping[p["steamid"]] = p.get("personaname", p["steamid"])
        except Exception:
            for sid in batch:
                mapping[sid] = sid

        time.sleep(delay)

    return mapping

# ==========================
# REVIEW FETCHING
# ==========================
def get_reviews_with_playtime(
    appid,
    total_reviews=100,
    language="english",
    review_type="all",
    progress_callback=None
):
    url = f"https://store.steampowered.com/appreviews/{appid}"
    cursor = "*"
    reviews = []

    while len(reviews) < total_reviews:
        try:
            resp = requests.get(
                url,
                params={
                    "json": 1,
                    "filter": "recent",
                    "review_type": review_type,
                    "purchase_type": "all",
                    "language": language,
                    "num_per_page": 100,
                    "cursor": cursor
                },
                headers={"User-Agent": "SteamReviewFetcher/1.0"},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            break

        batch = data.get("reviews", [])
        if not batch:
            break

        for r in batch:
            reviews.append({
                "author_steamid": r["author"].get("steamid", ""),
                "author": r["author"].get("steamid", ""),
                "review": r.get("review", ""),
                "voted_up": r.get("voted_up", False),
                "timestamp": datetime.datetime.utcfromtimestamp(
                    r.get("timestamp_created", 0)
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "playtime_minutes": r["author"].get("playtime_forever", 0)
            })

            if progress_callback:
                progress_callback(len(reviews), total_reviews)

            if len(reviews) >= total_reviews:
                break

        cursor = data.get("cursor")
        time.sleep(0.25)

    ids = {r["author_steamid"] for r in reviews if r["author_steamid"]}
    id_map = resolve_usernames(ids)

    for r in reviews:
        r["author"] = id_map.get(r["author_steamid"], r["author_steamid"])

    return reviews

# ==========================
# LOAD GAME CACHE
# ==========================
with open("steam_games.json", "r", encoding="utf-8") as f:
    all_games = json.load(f)

game_names = list(all_games.keys())

# ==========================
# TKINTER GUI
# ==========================
root = tk.Tk()
root.title("Steam Review Fetcher")
root.geometry("600x500")

# ==========================
# AUTOCOMPLETE COMBOBOX
# ==========================
class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._after_id = None
        self["values"] = self._completion_list[:50]
        self.bind("<KeyRelease>", self._on_keyrelease)

    def _on_keyrelease(self, event):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(250, self._filter)

    def _filter(self):
        value = self.get().lower()
        if not value:
            data = self._completion_list[:50]
        else:
            data = [g for g in self._completion_list if value in g.lower()][:50]
        self["values"] = data

# ==========================
# HEADER
# ==========================
tk.Label(
    root,
    text="Steam Review Fetcher",
    font=("Arial", 20, "bold"),
    bg="#2040ac",
    fg="white",
    pady=10
).pack(fill="x")

# ==========================
# INPUTS
# ==========================
tk.Label(root, text="Select Game:").pack(pady=(10, 0))
game_var = tk.StringVar()
game_combo = AutocompleteCombobox(root, textvariable=game_var, width=65)
game_combo.set_completion_list(game_names)
game_combo.pack()

tk.Label(root, text="Language:").pack(pady=(10, 0))
lang_var = tk.StringVar(value="english")
ttk.Combobox(root, textvariable=lang_var,
             values=["english", "german", "french", "spanish", "turkish"]).pack()

tk.Label(root, text="Review Type:").pack(pady=(10, 0))
review_var = tk.StringVar(value="all")
ttk.Combobox(root, textvariable=review_var,
             values=["all", "positive", "negative"]).pack()

tk.Label(root, text="Number of Reviews:").pack(pady=(10, 0))
review_count_var = tk.StringVar(value="200")
ttk.Combobox(root, textvariable=review_count_var,
             values=[200, 300, 400, 500, 750, 1000]).pack()

# ==========================
# PROGRESS BAR
# ==========================
progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=10)

status_label = tk.Label(root, text="")
status_label.pack()

# ==========================
# FETCH THREAD
# ==========================
def fetch_and_save():
    threading.Thread(target=_fetch_thread, daemon=True).start()

def _fetch_thread():
    try:
        game_name = game_var.get()
        appid = all_games.get(game_name)
        if not appid:
            messagebox.showerror("Error", "Invalid game selected.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text File", "*.txt"),
                ("CSV File", "*.csv"),
                ("Excel File", "*.xlsx"),
                ("JSON File", "*.json")
            ]
        )
        if not save_path:
            return

        def update_progress(cur, total):
            percent = int((cur / total) * 100)
            root.after(0, lambda: progress.config(value=percent))
            root.after(0, lambda: status_label.config(text=f"Fetching... {percent}%"))

        root.after(0, lambda: progress.config(value=0))
        root.after(0, lambda: status_label.config(text="Starting..."))

        reviews = get_reviews_with_playtime(
            appid,
            int(review_count_var.get()),
            lang_var.get(),
            review_var.get(),
            update_progress
        )

        df = pd.DataFrame(reviews)

        if save_path.endswith(".txt"):
            with open(save_path, "w", encoding="utf-8") as f:
                for i, r in enumerate(reviews, 1):
                    f.write(f"Review {i}\nAuthor: {r['author']}\n\n{r['review']}\n\n{'-'*80}\n")
        elif save_path.endswith(".csv"):
            df.to_csv(save_path, index=False, encoding="utf-8")
        elif save_path.endswith(".xlsx"):
            df.to_excel(save_path, index=False)
        elif save_path.endswith(".json"):
            df.to_json(save_path, orient="records", force_ascii=False)

        root.after(0, lambda: progress.config(value=100))
        root.after(0, lambda: status_label.config(text="Done ✅"))
        root.after(0, lambda: messagebox.showinfo("Success", f"{len(reviews)} reviews saved"))

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", str(e)))

# ==========================
# BUTTON
# ==========================
tk.Button(
    root,
    text="Fetch & Save Reviews",
    command=fetch_and_save,
    bg="green",
    fg="white"
).pack(pady=20)

root.mainloop()
