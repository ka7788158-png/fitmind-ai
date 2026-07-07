from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv, find_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import os
from langchain_chroma import Chroma

load_dotenv(find_dotenv())

CHROMA_DIR = "./chroma_db"

embedding = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")

vectorstore = Chroma(
    persist_directory = CHROMA_DIR, 
    embedding_function = embedding
)

retriever = vectorstore.as_retriever(search_kwargs={"k":4})

llm = ChatMistralAI(
    model = "mistral-small-2506", 
    api_key = os.getenv("MISTRAL_API_KEY"),
    temperature = 0.7
)

PLAN_PROMPT = PromptTemplate(
    input_variables=["context", "profile"],
    template="""
You are an expert gym coach and certified nutritionist.
Use the context below from trusted fitness and nutrition guidelines to create a plan.

Context:
{context}

Member Profile:
{profile}

Generate a structured response with exactly these sections:

1. WEEKLY WORKOUT PLAN (6 days, rest on Sunday)
   - For each day: muscle group, 4-5 exercises with sets x reps

2. DIET PLAN
   - Daily calorie target
   - Macros (protein/carbs/fat in grams)
   - Meal plan: Breakfast, Mid-morning snack, Lunch, Evening snack, Dinner
   - Indian food options wherever possible

3. KEY TIPS (3-4 points specific to their goal and any injuries)

Keep it practical, specific, and beginner-friendly if needed.
"""
)

CHAT_PROMPT = PromptTemplate(
    input_variables= ["context", "history", "question"], 
    template = """
You are a helpful gym coach and nutriotionist assistant. 
Use the context below to answer the member's question. 

Context:
{context}

Conversation History:
{history}

Member Question: {question}

Give a helpful, specific, and concise answer. 
"""
)

DAILY_PROMPT = PromptTemplate(
    input_variables=["context", "profile", "day_name", "muscle_group"],
    template="""
You are an expert gym coach and nutritionist.

Member Profile:
{profile}

Today is {day_name}. Today's focus: {muscle_group}

Context from fitness guidelines:
{context}

Generate today's complete plan with EXACTLY these sections:

1. TODAY'S WORKOUT — {muscle_group}
   - 5-6 exercises with sets x reps format like: "- Exercise Name — 3x10-12"
   - Brief tip for each exercise

2. TODAY'S FOOD TIMELINE
   - Breakfast: [time and food]
   - Mid-Morning: [time and food]  
   - Lunch: [time and food]
   - Evening: [time and food]
   - Dinner: [time and food]
   - Post-Workout: [food]

3. TODAY'S FOCUS TIP
   - One specific tip for {muscle_group} training

Use Indian food options. Keep it practical and specific.
"""
)

MODIFY_PROMPT = PromptTemplate(
    input_variables=["current_plan", "request", "profile"],
    template="""
You are an expert gym coach. A member wants to modify their current plan.

Member Profile:
{profile}

Current Plan:
{current_plan}

Member's Request: {request}

Generate a modified version of the plan addressing their request.
Keep the same structure and format as the original plan.
Only change what the member asked for, keep everything else the same.
"""
)

CALORIE_PROMPT = PromptTemplate(
    input_variables=["food"],
    template="""
You are a nutrition expert. The user ate the following food:
"{food}"

Respond ONLY with a JSON object like this, nothing else:
{{
  "items": [
    {{"name": "Apple", "calories": 95}},
    {{"name": "2 Rotis", "calories": 160}}
  ],
  "total": 255,
  "meal_type": "snack"
}}

meal_type must be one of: breakfast, midmorning, lunch, evening, dinner
Estimate calories accurately for Indian foods too.   
"""
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate_daily_plan(profile: dict, day_number: int, day_name: str) -> str:
    MUSCLES = ['Rest','Chest & Triceps','Back & Biceps','Legs & Core','Shoulders & Abs','Full Body','Arms & Core']
    muscle_group = MUSCLES[day_number] if day_number < len(MUSCLES) else 'Full Body'

    profile_text = f"""
    Name: {profile.get('name')}
    Age: {profile.get('age')}
    Weight: {profile.get('weight')} kg
    Height: {profile.get('height')} cm
    Goal: {profile.get('goal')}
    Diet: {profile.get('diet_type')}
    Injuries: {profile.get('injuries', 'None')}
    Experience: {profile.get('experience')}
    """

    query = f"{muscle_group} workout exercises and nutrition"
    docs = retriever.invoke(query)
    context = format_docs(docs)

    chain = DAILY_PROMPT | llm | StrOutputParser()
    return chain.invoke({
        "context": context,
        "profile": profile_text,
        "day_name": day_name,
        "muscle_group": muscle_group
    })

def modify_existing_plan(current_plan: str, request: str, profile: dict) -> str:
    profile_text = f"Goal: {profile.get('goal')}, Diet: {profile.get('diet_type')}, Injuries: {profile.get('injuries','None')}"
    chain = MODIFY_PROMPT | llm | StrOutputParser()
    return chain.invoke({
        "current_plan": current_plan,
        "request": request,
        "profile": profile_text
    })

def generate_plan(profile: dict) -> str:
    profile_text = f"""
    Age: {profile.get('age')}
    Weight: {profile.get('weight')} kg
    Height: {profile.get('height')} cm
    Goal: {profile.get('goal')}
    Diet Type: {profile.get('diet_type')}
    Injuries/Limitations: {profile.get('injuries', 'None')}
    Experience Level: {profile.get('experience')}
"""
    
    query = f"{profile.get('goal')} workout and diet plan for {profile.get('experience')} level"
    docs = retriever.invoke(query)
    context = format_docs(docs)

    chain = PLAN_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"context": context, "profile" : profile_text})
    return result

def chat_with_coach(question: str, history: list) -> str:
    docs = retriever.invoke(question)
    context = format_docs(docs)

    history_text = ""
    for msg in history[-6:]:
        role = "Member" if msg["role"] == "user" else "Coach"
        history_text += f"{role}: {msg['content']}\n"

    chain = CHAT_PROMPT | llm | StrOutputParser()
    result = chain.invoke({
        "context" : context, 
        "history" : history_text, 
        "question" : question
    })

    return result

def calculate_food_calories(food_description: str) -> dict:
    chain = CALORIE_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"food":food_description})
    try:
        import json, re
        clean = re.search(r'\{.*\}',result, re.DOTALL)
        if clean:
            return json.loads(clean.group())
        
    except:
        pass
    return {"items" : [], "total" : 0, "meal_type": "lunch"}