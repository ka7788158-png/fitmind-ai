from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict, Optional, List
from dotenv import load_dotenv
import os
import json
import re

load_dotenv("./.env")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

# ── STATE ──
class WeeklyState(TypedDict):
    gym_name: str
    members: List[dict]
    week_start: str
    week_end: str
    leaderboard: Optional[List[dict]]
    summaries: Optional[List[dict]]
    gym_summary: Optional[dict]
    improvement_tips: Optional[dict]

# ── NODE 1 — BUILD LEADERBOARD ──
def build_leaderboard(state: WeeklyState) -> WeeklyState:
    members = state["members"]
    scored = []

    for m in members:
        score = 0
        checkins = m.get("total_checkins", 0)
        is_premium = m.get("is_premium", False)

        # scoring formula
        score += checkins * 10
        if is_premium: score += 20

        # consistency bonus
        joined = m.get("joined_date", "2024-01-01")
        try:
            from datetime import datetime
            days = max((datetime.now() - datetime.strptime(joined, "%Y-%m-%d")).days, 1)
            rate = (checkins / max(days - days//7, 1)) * 100
            if rate > 80: score += 50
            elif rate > 60: score += 30
            elif rate > 40: score += 15
        except:
            rate = 0

        scored.append({
            "member_id": m.get("member_id"),
            "name": m.get("name"),
            "score": score,
            "checkins": checkins,
            "goal": m.get("goal"),
            "experience": m.get("experience"),
            "is_premium": is_premium
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # assign ranks and medals
    medals = ["🥇", "🥈", "🥉"]
    for i, m in enumerate(scored):
        m["rank"] = i + 1
        m["medal"] = medals[i] if i < 3 else f"#{i+1}"

    state["leaderboard"] = scored
    return state

# ── NODE 2 — GENERATE GYM SUMMARY ──
def generate_gym_summary(state: WeeklyState) -> WeeklyState:
    members = state["members"]
    leaderboard = state["leaderboard"]
    total = len(members)
    premium = sum(1 for m in members if m.get("is_premium"))
    top3 = json.dumps([{"name": m["name"], "checkins": m["checkins"]} for m in leaderboard[:3]])

    prompt_text = f"""
You are a gym analytics AI for {state["gym_name"]}.

Week: {state["week_start"]} to {state["week_end"]}
Total Members: {total}
Premium Members: {premium}
Top 3 Performers: {top3}

Generate as JSON only:
{{
  "headline": "exciting one-line headline for this week",
  "highlights": ["highlight 1", "highlight 2", "highlight 3"],
  "owner_tip": "one specific tip for gym owner to improve retention"
}}
"""
    result = llm.invoke(prompt_text).content
    try:
        clean = re.search(r'\{.*\}', result, re.DOTALL)
        state["gym_summary"] = json.loads(clean.group()) if clean else {}
    except:
        state["gym_summary"] = {
            "headline": "Another great week at the gym!",
            "highlights": ["Members stayed consistent", "Premium members led the pack", "Great energy this week"],
            "owner_tip": "Follow up with inactive members this week"
        }
    return state

# ── NODE 3 — GENERATE IMPROVEMENT TIPS ──
def generate_improvement_tips(state: WeeklyState) -> WeeklyState:
    leaderboard = state["leaderboard"] or []
    bottom = json.dumps([{"name": m["name"], "checkins": m["checkins"]} for m in leaderboard[-3:]])

    prompt_text = f"""
You are a gym retention specialist.

Total Members: {len(state["members"])}
Members needing attention: {bottom}

Generate as JSON only:
{{
  "retention_tips": ["tip 1", "tip 2", "tip 3"],
  "engagement_ideas": ["idea 1", "idea 2"],
  "message_for_inactive": "short motivating WhatsApp message for inactive members"
}}
"""
    result = llm.invoke(prompt_text).content
    try:
        clean = re.search(r'\{.*\}', result, re.DOTALL)
        state["improvement_tips"] = json.loads(clean.group()) if clean else {}
    except:
        state["improvement_tips"] = {
            "retention_tips": ["Send reminder messages", "Offer free session", "Check in personally"],
            "engagement_ideas": ["Start a monthly challenge", "Add leaderboard in gym"],
            "message_for_inactive": "Hey! We miss you at the gym. Come back stronger this week! 💪"
        }
    return state

# ── BUILD GRAPH ──
def build_weekly_graph():
    graph = StateGraph(WeeklyState)

    graph.add_node("build_leaderboard", build_leaderboard)
    graph.add_node("generate_gym_summary", generate_gym_summary)
    graph.add_node("generate_improvement_tips", generate_improvement_tips)

    graph.set_entry_point("build_leaderboard")
    graph.add_edge("build_leaderboard", "generate_gym_summary")
    graph.add_edge("generate_gym_summary", "generate_improvement_tips")
    graph.add_edge("generate_improvement_tips", END)

    return graph.compile()

weekly_graph = build_weekly_graph()

def run_weekly_summary(gym_name: str, members: list) -> dict:
    from datetime import datetime, timedelta
    today = datetime.now()
    week_start = (today - timedelta(days=today.weekday()+1)).strftime("%Y-%m-%d")
    week_end = today.strftime("%Y-%m-%d")

    state = WeeklyState(
        gym_name=gym_name,
        members=members,
        week_start=week_start,
        week_end=week_end,
        leaderboard=None,
        summaries=None,
        gym_summary=None,
        improvement_tips=None
    )

    result = weekly_graph.invoke(state)
    return {
        "leaderboard": result["leaderboard"],
        "gym_summary": result["gym_summary"],
        "improvement_tips": result["improvement_tips"],
        "week_start": week_start,
        "week_end": week_end
    }