
from fastapi import FastAPI, File, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil, os, re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from dotenv import load_dotenv
from supabase import create_client
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

# ================= INIT =================
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= AUTH =================
def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data):
    data["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(authorization: str):
    try:
        if not authorization or " " not in authorization:
            return None

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("email")

    except Exception as e:
        print("AUTH ERROR:", e)
        return None

# ================= OCR =================
def extract_text(path, filename):
    text = ""

    try:
        if filename.lower().endswith(".pdf"):
            pages = convert_from_path(path)
            for p in pages:
                text += pytesseract.image_to_string(p)
        else:
            img = Image.open(path).convert("L")
            text = pytesseract.image_to_string(img)
    except Exception as e:
        print("OCR ERROR:", e)

    return text

def extract_data(text):
    vendor = "Unknown"

    for line in text.split("\n")[:5]:
        if len(line.strip()) > 3:
            vendor = line.strip()
            break

    # ✅ FIXED DATE REGEX (proper indentation)
    date = re.search(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
        r"\d{1,2}\s[A-Za-z]{3,9}\s\d{4}|[A-Za-z]{3,9}\s\d{1,2},\s\d{4})\b",
        text
    )

    amount = re.search(r"\d+\.\d+", text)

    return {
        "vendor": vendor,
        "invoice_date": date.group(0) if date else "N/A",
        "total_amount": amount.group(0) if amount else "0",
        "currency": "USD" if "$" in text else "INR"
    }

# ================= ROUTES =================

@app.post("/register")
async def register(user: dict):
    supabase.table("users").insert({
        "email": user["email"],
        "password": hash_password(user["password"])
    }).execute()
    return {"message": "Registered"}

@app.post("/login")
async def login(user: dict):
    res = supabase.table("users").select("*").eq("email", user["email"]).execute()

    if not res.data:
        return {"error": "User not found"}

    db_user = res.data[0]

    if not verify_password(user["password"], db_user["password"]):
        return {"error": "Invalid password"}

    token = create_token({"email": user["email"]})
    return {"access_token": token}

@app.get("/invoices")
def get_invoices(authorization: str = Header(None)):
    user = get_current_user(authorization)
    if not user:
        return []

    res = supabase.table("invoices").select("*").eq("user_email", user).execute()
    return res.data

@app.post("/upload")
async def upload(file: UploadFile = File(...), authorization: str = Header(None)):
    user = get_current_user(authorization)
    if not user:
        return {"error": "Unauthorized"}

    path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = extract_text(path, file.filename)
    parsed = extract_data(text)

    supabase.table("invoices").insert({
        **parsed,
        "filename": file.filename,
        "file_url": f"http://127.0.0.1:8000/uploads/{file.filename}",
        "user_email": user
    }).execute()

    return {"message": "Uploaded"}

@app.get("/analytics")
def analytics(authorization: str = Header(None)):
    user = get_current_user(authorization)
    if not user:
        return {}

    res = supabase.table("invoices").select("*").eq("user_email", user).execute()
    data = res.data or []

    return {
        "total_invoices": len(data),
        "total_spend": sum(float(i["total_amount"]) for i in data)
    }

@app.delete("/invoice/{id}")
def delete(id: int, authorization: str = Header(None)):
    supabase.table("invoices").delete().eq("id", id).execute()
    return {"message": "Deleted"}