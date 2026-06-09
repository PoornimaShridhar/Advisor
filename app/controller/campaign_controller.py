def on_campaign_select(dfs, campaign_name):
    """
    dfs = full dataset
    """

    df = dfs["campaigns"].copy()
    filtered = df[df["name"] == campaign_name]

    return {
        "campaign_name": campaign_name,
        "campaign_df": filtered,
        "full_dfs": dfs   # IMPORTANT: keep full dataset for analytics
    }