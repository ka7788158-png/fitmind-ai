from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict, Optional
from dotenv import load_dotenv
import os 
import json

load_dotenv("./.env")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

# --- STATE ---
class AdaptiveState(TypedDict):
    member_id : str
    name: str
    current_experience : str
    goal : str
    total_checkins: int
    joined_date: str
    last_checkin : str
    days_since_joined: int
    checkin_rate: float
    analysis: Optional[str]
    recommendation: Optional[str]
    should_upgrade: Optional[bool]
    new_experience: Optional[str]
    motivation_message: Optional[str]
    improvement_tips: Optional[list]

# ---- Node 1 - ANALYZE PROGRESS ----- 
def analyze_progress(state: AdaptiveState) -> AdaptiveState:
    prompt_text = f"""
You are an AI fitness progress analyzer.

Member: {state["name"]}
Current Level: {state["current_experience"]}
Goal: {state["goal"]}
Total Gym Checkins: {state["total_checkins"]}
Days Since Joined: {state["days_since_joined"]}
Checkin Rate: {state["checkin_rate"]}%

Analyze their progress and respond ONLY with a JSON object:
{{
  "consistency": "high/medium/low",
  "ready_for_upgrade": true,
  "reason": "brief reason why or why not",
  "weeks_active": {state["total_checkins"]}
}}

Rules for ready_for_upgrade:
- true if: checkin_rate > 60% AND total_checkins >= 12 AND experience is "beginner"
- true if: checkin_rate > 65% AND total_checkins >= 20 AND experience is "intermediate"
- false if: checkin_rate < 40%
- false if: experience is already "advanced"
"""
    result = llm.invoke(prompt_text).content
    try:
        import re
        clean = re.search(r'\{.*\}', result, re.DOTALL)
        data = json.loads(clean.group()) if clean else {}
        state["analysis"] = data.get("reason", "Analysis complete")
        state["should_upgrade"] = data.get("ready_for_upgrade", False)
    except:
        state["analysis"] = "Could not analyze"
        state["should_upgrade"] = False
    return state

# --- NODE 2 - DIFFICULTY ASSESSOR --- 
def difficulty_assessor(state: AdaptiveState) -> AdaptiveState:
    if not state["should_upgrade"]:
        state["new_experience"] = state["current_experience"]
        return state
    
    upgrade_map = {
        "beginner" : "intermediate", 
        "intermediate": "advanced", 
        "advanced" : "advanced"
    }
    state["new_experience"] = upgrade_map.get(state["current_experience"], state["current_experience"])
    return state

# --- NODE 3 - GENERATE RECOMMENDATION ---- 
def generate_recommendation(state: AdaptiveState) -> AdaptiveState:
    if state["should_upgrade"]:
        prompt_text = f"""
You are an enthusiastic gym coach. A member has earned a level upgrade!

Member: {state["name"]}
Level Change: {state["current_experience"]} → {state["new_experience"]}
Total Workouts Completed: {state["total_checkins"]}
Goal: {state["goal"]}

Generate as JSON only:
{{
  "message": "exciting upgrade announcement (2-3 sentences)",
  "changes": ["change 1", "change 2", "change 3"],
  "challenge": "two week challenge"
}}
"""
    else:
        prompt_text = f"""
You are a supportive gym coach.

Member: {state["name"]}
Level: {state["current_experience"]}
Consistency: {state["checkin_rate"]}%
Goal: {state["goal"]}

Generate as JSON only:
{{
  "message": "encouraging message (2-3 sentences)",
  "changes": ["tip 1", "tip 2", "tip 3"],
  "challenge": "one week mini challenge"
}}
"""
    result = llm.invoke(prompt_text).content
    try:
        import re
        clean = re.search(r'\{.*\}', result, re.DOTALL)
        data = json.loads(clean.group()) if clean else {}
        state["motivation_message"] = data.get("message", "Keep pushing!")
        state["improvement_tips"] = data.get("changes", [])
        state["recommendation"] = data.get("challenge", "")
    except:
        state["motivation_message"] = "Keep going, you're doing great!"
        state["improvement_tips"] = ["Stay consistent", "Push harder", "Track progress"]
        state["recommendation"] = "Hit the gym 5 days this week"
    return state

# -- ROUTER --- 
def should_upgrade_router(state: AdaptiveState) -> str:
    return "upgrade" if state["should_upgrade"] else "encourage"

# BUILD GRAPH -----
def build_adaptive_graph():
    graph = StateGraph(AdaptiveState)

    graph.add_node("analyze_progress", analyze_progress)
    graph.add_node("difficulty_assessor", difficulty_assessor)
    graph.add_node("generate_recommendation", generate_recommendation)

    graph.set_entry_point("analyze_progress")
    graph.add_edge("analyze_progress", "difficulty_assessor")
    graph.add_conditional_edges(
        "difficulty_assessor",
        should_upgrade_router,
        {
            "upgrade": "generate_recommendation",
            "encourage": "generate_recommendation"
        }
    )
    graph.add_edge("generate_recommendation", END)

    return graph.compile()

adaptive_graph = build_adaptive_graph()

def run_adaptive_coaching(member_data: dict) -> dict:
    from datetime import datetime

    joined = member_data.get("joined_date", datetime.now().strftime("%Y-%m-%d"))
    try:
        days_since = (datetime.now() - datetime.strptime(joined, "%Y-%m-%d")).days
    except:
        days_since = 0

    total_checkins = member_data.get("total_checkins", 0)
    possible_days = max(days_since - (days_since // 7), 7)
    checkin_rate = min(round((total_checkins / possible_days) * 100, 1), 100)

    state = AdaptiveState(
        member_id=member_data.get("member_id", ""),
        name=member_data.get("name", "Member"),
        current_experience=member_data.get("experience", "beginner"),
        goal=member_data.get("goal", "muscle gain"),
        total_checkins=total_checkins,
        joined_date=joined,
        last_checkin=member_data.get("last_checkin", ""),
        days_since_joined=days_since,
        checkin_rate=checkin_rate,
        analysis=None,
        recommendation=None,
        should_upgrade=None,
        new_experience=None,
        motivation_message=None,
        improvement_tips=None
    )


    result = adaptive_graph.invoke(state)
    return {
        "should_upgrade": result["should_upgrade"],
        "current_experience": result["current_experience"],
        "new_experience": result["new_experience"],
        "analysis": result["analysis"],
        "motivation_message": result["motivation_message"],
        "improvement_tips": result["improvement_tips"],
        "challenge": result["recommendation"],
        "checkin_rate": checkin_rate
    }