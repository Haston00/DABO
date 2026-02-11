"""
Plotly chart builders for DABO dashboard.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def build_gantt_data(activities: list, start_date: datetime) -> list[dict]:
    """
    Convert CPM activities to Gantt chart row dicts.
    Each row: Task, Start, Finish, Resource (discipline), Critical (bool).
    """
    from scheduling.cpm_engine import day_to_date

    rows = []
    for act in activities:
        if act.is_milestone:
            continue
        s = day_to_date(act.early_start, start_date)
        f = day_to_date(act.early_finish, start_date)
        if f <= s:
            f = s + timedelta(days=1)
        rows.append({
            "Task": act.activity_name,
            "Start": s,
            "Finish": f,
            "Resource": act.division or "General",
            "Critical": act.total_float == 0,
            "Float": act.total_float,
            "ID": act.activity_id,
        })
    return rows


def gantt_chart(gantt_data: list[dict]):
    """Build a Plotly Gantt chart from gantt_data rows."""
    try:
        import plotly.express as px
    except ImportError:
        return None

    if not gantt_data:
        return None

    import pandas as pd
    df = pd.DataFrame(gantt_data)

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Critical",
        color_discrete_map={True: "#d32f2f", False: "#1976d2"},
        hover_data=["ID", "Float", "Resource"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=max(400, len(gantt_data) * 28),
        showlegend=True,
        legend_title_text="Critical Path",
        margin=dict(l=250),
    )
    return fig


def severity_pie(conflicts: list[dict]):
    """Pie chart of conflict severities."""
    try:
        import plotly.express as px
    except ImportError:
        return None

    if not conflicts:
        return None

    import pandas as pd
    from collections import Counter
    counts = Counter(c.get("severity", "UNKNOWN") for c in conflicts)
    df = pd.DataFrame(list(counts.items()), columns=["Severity", "Count"])

    color_map = {"CRITICAL": "#d32f2f", "MAJOR": "#f57c00", "MINOR": "#fbc02d", "INFO": "#1976d2"}
    fig = px.pie(
        df, values="Count", names="Severity",
        color="Severity", color_discrete_map=color_map,
    )
    fig.update_layout(height=300)
    return fig


def discipline_bar(sheets: list[dict]):
    """Bar chart of sheet counts by discipline."""
    try:
        import plotly.express as px
    except ImportError:
        return None

    if not sheets:
        return None

    import pandas as pd
    from collections import Counter
    counts = Counter(s.get("discipline", "UNKNOWN") for s in sheets)
    df = pd.DataFrame(
        sorted(counts.items(), key=lambda x: x[1], reverse=True),
        columns=["Discipline", "Sheets"],
    )

    fig = px.bar(df, x="Discipline", y="Sheets", color="Discipline")
    fig.update_layout(height=350, showlegend=False)
    return fig


def accuracy_trend(metrics_history: list[dict]):
    """Line chart of accuracy metrics over time."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        return None

    if not metrics_history:
        return None

    fig = go.Figure()
    dates = [m.get("date", "") for m in metrics_history]
    fig.add_trace(go.Scatter(
        x=dates,
        y=[m.get("true_positive_rate", 0) for m in metrics_history],
        mode="lines+markers", name="True Positive Rate",
        line=dict(color="#4caf50"),
    ))
    fig.add_trace(go.Scatter(
        x=dates,
        y=[m.get("false_positive_rate", 0) for m in metrics_history],
        mode="lines+markers", name="False Positive Rate",
        line=dict(color="#f44336"),
    ))
    fig.update_layout(
        height=300, yaxis_title="Rate", xaxis_title="Run Date",
        yaxis=dict(range=[0, 1]),
    )
    return fig
