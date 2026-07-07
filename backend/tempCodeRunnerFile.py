from chain import generate_plan

profile = {
    "age": 20,
    "weight": 70,
    "height": 175,
    "goal": "muscle gain",
    "diet_type": "vegetarian",
    "injuries": "none",
    "experience": "beginner"
}

print(generate_plan(profile))