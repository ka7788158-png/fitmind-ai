from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from database import init_db, get_db, Member, Payment, GymProfile
from datetime import datetime, timedelta
from chain import generate_plan, chat_with_coach, generate_daily_plan, modify_existing_plan, calculate_food_calories
from adaptive_graph import run_adaptive_coaching
from weekly_graph import run_weekly_summary

app = FastAPI(title="FitMind AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

init_db()

# ── MODELS ──
class MemberProfile(BaseModel):
    member_id: str
    name: str
    age: int
    weight: float
    height: float
    goal: str
    diet_type: str
    injuries: Optional[str] = "None"
    experience: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    gender: Optional[str] = "male"

class ChatMessage(BaseModel):
    member_id: str
    question: str
    history: List[dict] = []

class DailyPlanRequest(BaseModel):
    member_id: str
    profile: dict
    day_number: int
    day_name: str

class ModifyPlanRequest(BaseModel):
    current_plan: str
    request: str
    profile: dict

class CalorieRequest(BaseModel):
    food_description: str

class PaymentCreate(BaseModel):
    member_id: str
    member_name: str
    amount: float
    plan_type: str
    payment_date: str
    expiry_date: str
    payment_mode: Optional[str] = "cash"
    notes: Optional[str] = ""

class GymProfileUpdate(BaseModel):
    gym_name: Optional[str] = None
    owner_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    monthly_fee: Optional[float] = None
    quarterly_fee: Optional[float] = None
    yearly_fee: Optional[float] = None

class OwnerLogin(BaseModel):
    password: str

class MemberUpdate(BaseModel):
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    expiry_date: Optional[str] = None
    experience: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    goal: Optional[str] = None



# ── ROOT ──
@app.get("/")
def root():
    return {"status": "FitMind AI running"}

# ── MEMBER ENDPOINTS ──
@app.post("/generate-plan")
def generate(profile: MemberProfile, db: Session = Depends(get_db)):
    plan = generate_plan(profile.dict())

    member = db.query(Member).filter(Member.member_id == profile.member_id).first()
    if member:
        member.plan = plan
        member.weight = profile.weight
    else:
        member = Member(
            member_id=profile.member_id,
            name=profile.name,
            email=profile.email or "",
            phone=profile.phone or "",
            age=profile.age,
            weight=profile.weight,
            height=profile.height,
            goal=profile.goal,
            diet_type=profile.diet_type,
            injuries=profile.injuries or "None",
            experience=profile.experience,
            plan=plan,
            joined_date=datetime.now().strftime("%Y-%m-%d")
        )
        db.add(member)
    db.commit()
    return {"member_id": profile.member_id, "plan": plan}

@app.post("/generate-daily-plan")
def daily_plan(req: DailyPlanRequest, db: Session = Depends(get_db)):
    plan = generate_daily_plan(req.profile, req.day_number, req.day_name)

    member = db.query(Member).filter(Member.member_id == req.member_id).first()
    if member:
        member.last_checkin = datetime.now().strftime("%Y-%m-%d")
        member.total_checkins = (member.total_checkins or 0) + 1
        db.commit()

    return {"plan": plan}

@app.post("/modify-plan")
def modify_plan(req: ModifyPlanRequest):
    plan = modify_existing_plan(req.current_plan, req.request, req.profile)
    return {"modified_plan": plan}

@app.post("/chat")
def chat(msg: ChatMessage):
    response = chat_with_coach(msg.question, msg.history)
    return {"response": response}

@app.post("/calculate-calories")
def calc_calories(req: CalorieRequest):
    result = calculate_food_calories(req.food_description)
    return result

@app.get("/member/{member_id}")
def get_member(member_id: str, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        return {"error": "Member not found"}
    return {
        "member_id": member.member_id,
        "name": member.name,
        "profile": {
            "member_id": member.member_id,
            "name": member.name,
            "age": member.age,
            "weight": member.weight,
            "height": member.height,
            "goal": member.goal,
            "diet_type": member.diet_type,
            "injuries": member.injuries,
            "experience": member.experience,
            "email": member.email,
            "phone": member.phone
        },
        "plan": member.plan,
        "is_premium": member.is_premium,
        "joined_date": member.joined_date,
        "last_checkin": member.last_checkin,
        "total_checkins": member.total_checkins
    }

@app.get("/all-members")
def all_members(db: Session = Depends(get_db)):
    members = db.query(Member).all()
    return {"members": [
        {
            "member_id": m.member_id,
            "name": m.name,
            "goal": m.goal,
            "experience": m.experience,
            "is_premium": m.is_premium,
            "is_active": m.is_active,
            "joined_date": m.joined_date,
            "last_checkin": m.last_checkin,
            "total_checkins": m.total_checkins,
            "expiry_date": m.expiry_date
        } for m in members
    ]}

@app.patch("/member/{member_id}")
def update_member(member_id: str, update: MemberUpdate, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        return {"error": "Member not found"}
    if update.is_premium is not None: member.is_premium = update.is_premium
    if update.is_active is not None: member.is_active = update.is_active
    if update.expiry_date is not None: member.expiry_date = update.expiry_date
    if update.experience is not None: member.experience = update.experience
    if update.weight is not None: member.weight = update.weight
    if update.height is not None: member.height = update.height
    if update.goal is not None: member.goal = update.goal
    db.commit()
    return {"success": True}

@app.delete("/member/{member_id}")
def delete_member(member_id: str, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        return {"error": "Not found"}
    db.delete(member)
    db.commit()
    return {"success": True}

# ── PAYMENT ENDPOINTS ──
@app.post("/payment")
def add_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    p = Payment(**payment.dict())
    db.add(p)

    member = db.query(Member).filter(Member.member_id == payment.member_id).first()
    if member:
        member.is_premium = True
        member.expiry_date = payment.expiry_date
    db.commit()
    return {"success": True, "id": p.id}

@app.get("/payments")
def get_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
    return {"payments": [
        {
            "id": p.id,
            "member_id": p.member_id,
            "member_name": p.member_name,
            "amount": p.amount,
            "plan_type": p.plan_type,
            "payment_date": p.payment_date,
            "expiry_date": p.expiry_date,
            "payment_mode": p.payment_mode,
            "notes": p.notes
        } for p in payments
    ]}

@app.delete("/payment/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        return {"error": "Not found"}
    db.delete(p)
    db.commit()
    return {"success": True}

@app.get("/revenue-stats")
def revenue_stats(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    members = db.query(Member).all()
    today = datetime.now().strftime("%Y-%m-%d")
    this_month = datetime.now().strftime("%Y-%m")

    total_revenue = sum(p.amount for p in payments)
    monthly_revenue = sum(p.amount for p in payments if p.payment_date.startswith(this_month))
    active_premium = sum(1 for m in members if m.is_premium and m.expiry_date >= today)
    expiring_soon = sum(1 for m in members if m.is_premium and m.expiry_date and
                       0 <= (datetime.strptime(m.expiry_date, "%Y-%m-%d") - datetime.now()).days <= 7)
    dropout_risk = sum(1 for m in members if m.last_checkin and
                      (datetime.now() - datetime.strptime(m.last_checkin, "%Y-%m-%d")).days >= 5)

    return {
        "total_revenue": total_revenue,
        "monthly_revenue": monthly_revenue,
        "total_members": len(members),
        "active_premium": active_premium,
        "expiring_soon": expiring_soon,
        "dropout_risk": dropout_risk,
        "total_payments": len(payments)
    }

# ── GYM PROFILE ──
@app.get("/gym-profile")
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(GymProfile).first()
    return {
        "gym_name": profile.gym_name,
        "owner_name": profile.owner_name,
        "phone": profile.phone,
        "email": profile.email,
        "address": profile.address,
        "monthly_fee": profile.monthly_fee,
        "quarterly_fee": profile.quarterly_fee,
        "yearly_fee": profile.yearly_fee
    }

@app.patch("/gym-profile")
def update_profile(update: GymProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(GymProfile).first()
    if update.gym_name: profile.gym_name = update.gym_name
    if update.owner_name: profile.owner_name = update.owner_name
    if update.phone: profile.phone = update.phone
    if update.email: profile.email = update.email
    if update.address: profile.address = update.address
    if update.monthly_fee: profile.monthly_fee = update.monthly_fee
    if update.quarterly_fee: profile.quarterly_fee = update.quarterly_fee
    if update.yearly_fee: profile.yearly_fee = update.yearly_fee
    db.commit()
    return {"success": True}

@app.post("/owner-login")
def owner_login(req: OwnerLogin, db: Session = Depends(get_db)):
    profile = db.query(GymProfile).first()
    if req.password == profile.password:
        return {"success": True, "gym_name": profile.gym_name, "owner_name": profile.owner_name}
    return {"success": False, "error": "Wrong password"}

@app.get("/adaptive-coaching/{member_id}")
def adaptive_coaching(member_id: str, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        return {"error": "Member not found"}

    member_data = {
        "member_id": member.member_id,
        "name": member.name,
        "experience": member.experience,
        "goal": member.goal,
        "total_checkins": member.total_checkins or 0,
        "joined_date": member.joined_date,
        "last_checkin": member.last_checkin or ""
    }

    result = run_adaptive_coaching(member_data)

    # auto upgrade if needed
    if result["should_upgrade"] and result["new_experience"] != member.experience:
        member.experience = result["new_experience"]
        db.commit()

    return result

@app.get("/weekly-summary")
def weekly_summary(db: Session = Depends(get_db)):
    profile = db.query(GymProfile).first()
    members = db.query(Member).all()

    members_data = [{
        "member_id": m.member_id,
        "name": m.name,
        "goal": m.goal,
        "experience": m.experience,
        "is_premium": m.is_premium,
        "total_checkins": m.total_checkins or 0,
        "joined_date": m.joined_date,
        "last_checkin": m.last_checkin or ""
    } for m in members]

    result = run_weekly_summary(profile.gym_name, members_data)
    return result