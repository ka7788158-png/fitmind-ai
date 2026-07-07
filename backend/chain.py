import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# Load environment variables
load_dotenv("./.env")

# Initialize the LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

def get_profile_text(profile: dict) -> str:
    return f"""
Name: {profile.get('name')}
Age: {profile.get('age')}
Weight: {profile.get('weight')} kg
Height: {profile.get('height')} cm
Goal: {profile.get('goal')}
Diet Type: {profile.get('diet_type')}
Injuries/Limitations: {profile.get('injuries', 'None')}
Experience Level: {profile.get('experience')}
Gender: {profile.get('gender', 'Not specified')}
"""

def generate_plan(profile: dict) -> str:
    template = """You are an expert gym coach and certified nutritionist specializing in Indian fitness.

Member Profile:
{profile_text}

Generate a complete fitness plan with EXACTLY these sections:

1. WEEKLY WORKOUT PLAN (6 days, rest on Sunday)
   - For each day: muscle group, 5-6 exercises with sets x reps format like "- Exercise Name — 3x10-12"

2. DIET PLAN
   - Daily calorie target based on their stats
   - Macros: protein, carbs, fat in grams
   - Meal plan: Breakfast, Mid-Morning, Lunch, Evening, Dinner
   - Use Indian food options

3. KEY TIPS (4 specific tips for their goal and any injuries)

Be specific, practical and beginner-friendly if needed."""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({"profile_text": get_profile_text(profile)})

def generate_daily_plan(profile: dict, day_number: int, day_name: str) -> str:
    MUSCLES = ['Rest','Chest & Triceps','Back & Biceps','Legs & Core','Shoulders & Abs','Full Body','Arms & Core']
    muscle_group = MUSCLES[day_number] if day_number < len(MUSCLES) else 'Full Body'

    template = """You are an expert gym coach and nutritionist specializing in Indian fitness.

Member Profile:
{profile_text}

Today is {day_name}. Today's focus: {muscle_group}

Generate today's complete plan with EXACTLY these sections:

1. TODAY'S WORKOUT — {muscle_group}
   - 5-6 exercises in this format: "- Exercise Name — 3x10-12"
   - Brief tip for each exercise

2. TODAY'S FOOD TIMELINE
   - Breakfast: (time) food description
   - Mid-Morning: (time) food description
   - Lunch: (time) food description
   - Evening: (time) food description
   - Dinner: (time) food description
   - Post-Workout: food description

3. TODAY'S FOCUS TIP
   - One specific tip for {muscle_group} training

Use Indian food options. Keep it practical and specific."""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({
        "profile_text": get_profile_text(profile),
        "day_name": day_name,
        "muscle_group": muscle_group
    })

def modify_existing_plan(current_plan: str, request: str, profile: dict) -> str:
    template = """You are an expert gym coach. A member wants to modify their plan.

Member Profile:
Goal: {goal}, Diet: {diet_type}, Injuries: {injuries}

Current Plan:
{current_plan}

Member's Request: {request}

Generate a modified version addressing their request.
Keep the same structure and format as the original.
Only change what was requested, keep everything else the same."""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({
        "goal": profile.get('goal'),
        "diet_type": profile.get('diet_type'),
        "injuries": profile.get('injuries', 'None'),
        "current_plan": current_plan,
        "request": request
    })

def chat_with_coach(question: str, history: list) -> str:
    history_text = ""
    for msg in history[-6:]:
        role = "Member" if msg["role"] == "user" else "Coach"
        history_text += f"{role}: {msg['content']}\n"

    template = """You are a helpful gym coach and nutritionist assistant for Indian users.
Answer fitness, nutrition, and health questions helpfully and specifically.

Conversation History:
{history_text}

Member Question: {question}

Give a helpful, specific, and concise answer. Use Indian context where relevant."""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    return chain.invoke({
        "history_text": history_text,
        "question": question
    })

def calculate_food_calories(food_description: str) -> dict:
    template = """You are a nutrition expert familiar with Indian foods.
The user ate: "{food_description}"

Analyze the meal and provide a calorie breakdown. 
Important: meal_type MUST be exactly one of: breakfast, midmorning, lunch, evening, dinner.
Be familiar with Indian foods like roti, dal, paneer, rice etc.

{format_instructions}"""
    
    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Bind JSON formatting directly to Groq for maximum reliability
    json_llm = llm.bind(response_format={"type": "json_object"})
    chain = prompt | json_llm | parser
    
    try:
        return chain.invoke({"food_description": food_description})
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return {"items": [], "total": 0, "meal_type": "lunch"}