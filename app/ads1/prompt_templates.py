def ads_analyst_prompt(name: str, payload: str) -> str:
    return (
        f"Write 3 to 5 bullet points of actionable Google Ads insights for {name}.\n"
        "Use simple language. One insight per bullet. Start each line with '- '. No intro sentence.\n\n"
        f"Data (JSON):\n{payload}"
    )


def keyword_inspector_prompt(payload: str) -> str:
    return (
        "Write 3 to 5 bullet points of actionable keyword performance insights.\n"
        "Classify individual keywords as winning, wasted spend, or scaling opportunities using CTR, cost, and conversions.\n"
        "Use simple language. One insight per bullet. Start each line with '- '. No intro sentence.\n\n"
        f"Data (JSON):\n{payload}"
    )


def search_term_cleaner_prompt(name: str, payload: str) -> str:
    return (
        f"Write 3 to 5 bullet points of actionable search term cleanup insights for {name}.\n"
        "Classify search terms as wasted spend, high intent, scale, or negative keyword candidates using total_cost, clicks, conversions, CPA, CVR, and CPC.\n"
        "Use simple language. One search term action per bullet. Start each line with '- '. No intro sentence.\n\n"
        f"Data (JSON):\n{payload}"
    )

