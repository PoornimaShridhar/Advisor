Final UI Architecture (clean version)
🟦 LEFT PANEL (Navigation)

Campaign list:

📁 Campaigns
- Preschool Search
- Brand Campaign
- Local Ads

Click → updates state

🟨 RIGHT PANEL (Workspace)
🧱 A. Global Header (fixed)
🎯 Ads Dashboard
Total Spend | Total Leads | Avg CPL | Active Campaigns
🧱 B. Campaign Context Banner (ONLY when selected)
📊 Campaign Snapshot
Spend | Leads | CTR | CPL | Trend

If no campaign selected → hidden or replaced with placeholder

🧱 C. 6 AI INSIGHT CARDS (core system)

Layout:

Row 1:
[Ads Analyst] [Budget Optimizer] [Keyword Intelligence]

Row 2:
[Risk Detector] [Growth Finder] [Experiment Ideas]
🟩 BEFORE CAMPAIGN SELECTION

Right panel shows:

👉 Select a campaign to begin analysis

AND:

6 cards are visible BUT greyed out
disabled state
no click behavior
🟦 AFTER CAMPAIGN SELECTION
banner appears
cards activate
clicking triggers expansion
🧠 CARD BEHAVIOR (important consistency rule)

Each card:

Idle
Title only + 1-line hint
Clicked
Expands in place
→ loading
→ MiniCPM explanation
→ action buttons

No page change ever.

🎯 3. Final Simple Design Doc (you can implement directly)
🧩 Layout Structure
1. App Layout
Left: Campaign Navigator (fixed width ~25%)
Right: Analysis Workspace (~75%)
🧱 2. Right Panel Structure
A. Global Metrics Header (always visible)
Total Spend
Total Leads
Average CPL
Active Campaigns
B. Campaign Context Banner

Visible only when campaign selected:

Campaign name
Spend
CTR
CPL
Trend indicators

If no selection:

show placeholder message
C. AI Insight Grid (2x3 layout)

Cards:

Ads Performance Analyst
Budget Optimizer
Keyword Intelligence
Risk Detector
Growth Opportunities
Experiment Ideas
🎨 3. Visual States
STATE 1: No campaign selected

Right panel:

message: “Select a campaign to begin analysis”
6 cards greyed out
STATE 2: Campaign selected
Context banner appears
Cards activate (clickable)
STATE 3: Card clicked

Inside same card:

loading spinner
MiniCPM explanation
recommendation

⚡ 4. Key UX Principles
Context ≠ Action (banner vs cards)
No navigation changes (single workspace)
Progressive disclosure (click → expand)
Grey-out inactive capability (not hide it)

┌──────────────────────────────────────────────────────────────┐
│ HEADER: Global KPIs (always visible)                        │
├───────────────┬──────────────────────────────────────────────┤
│ LEFT PANEL    │ RIGHT PANEL                                 │
│ Campaign List │ Workspace                                   │
│               │                                              │
│               │ [Campaign Context Banner]                   │
│               │                                              │
│               │ [6 AI Cards Grid (2x3)]                    │
└───────────────┴──────────────────────────────────────────────┘