import pandas as pd

def merge_dfs(real_dfs: dict, sample_dfs: dict) -> dict:
    """
    Merge real Google Ads data with synthetic sample data.
    Keeps schema identical and adds source tracking.
    """

    merged = {}

    for key in real_dfs.keys():
        real_df = real_dfs.get(key)
        sample_df = sample_dfs.get(key)

        # If both exist
        if real_df is not None and sample_df is not None:
            real_df = real_df.copy()
            sample_df = sample_df.copy()

            real_df["source"] = "real"
            sample_df["source"] = "sample"

            # Align columns safely
            for col in real_df.columns:
                if col not in sample_df.columns:
                    sample_df[col] = None

            for col in sample_df.columns:
                if col not in real_df.columns:
                    real_df[col] = None

            # Ensure same column order
            sample_df = sample_df[real_df.columns]

            merged[key] = pd.concat([real_df, sample_df], ignore_index=True)

        elif real_df is not None:
            real_df = real_df.copy()
            real_df["source"] = "real"
            merged[key] = real_df

        elif sample_df is not None:
            sample_df = sample_df.copy()
            sample_df["source"] = "sample"
            merged[key] = sample_df

    return merged