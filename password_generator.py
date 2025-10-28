import random
from fastapi import APIRouter
router = APIRouter()

# ------------------- Password Generator -------------------
letters = list("abcdefghjklmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ")
numbers = list("23456789")
symbols = list("!#$%()*+")
cases = [0, 0, 1, 1, 2]

@router.post("/password/{length}")
async def generate_password(length: int):
    if length < 12 or length > 16:
        return {"error": "Length must be between 12 and 16"}
    password = ""
    for _ in range(length):
        case = random.choice(cases)
        if case == 0:
            password += random.choice(letters)
        elif case == 1:
            password += random.choice(numbers)
        else:
            password += random.choice(symbols)
    return {"password": password}