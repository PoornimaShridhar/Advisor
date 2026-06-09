import os
import time
import pickle
import pandas as pd
from app.ads1.fetch_ads_data import fetch_all_data, to_dataframes

CACHE_FILE = "/tmp/google_ads_cache.pkl"
CACHE_TTL = 3600  # Cache data for 1 hour (3600 seconds)

def load_google_ads_data(force_refresh=False):
    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    if not customer_id:
        raise ValueError("GOOGLE_ADS_CUSTOMER_ID missing")

    # Check if a fresh disk cache exists
    if not force_refresh and os.path.exists(CACHE_FILE):
        file_mod_time = os.path.getmtime(CACHE_FILE)
        if (time.time() - file_mod_time) < CACHE_TTL:
            print("🚀 Loading data from local disk cache...")
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)

    print("🌐 Disk cache expired or missing. Fetching live Google Ads data...")
    raw = fetch_all_data(customer_id)
    dfs = to_dataframes(raw)

    # Save to disk cache safely
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(dfs, f)

    return dfs
