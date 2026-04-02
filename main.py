from fastapi import FastAPI, File, UploadFile
import shutil, os, re, uuid
import pytesseract
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

# ✅ ENV
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔧 Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# 🔥 FORMAT MEMORY
# ==============================
known_vendors = {}

# ==============================
# 🔥 OCR (IMAGE ONLY)
# ==============================
def extract_text(file_path):
    try:
        image = Image.open(file_path).convert("L")
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return ""


# ==============================
# 🔥 PARSER
# ==============================
def extract_data(text):
    lines = text.split("\n")

    # ✅ Vendor
    vendor = None
    for line in lines[:5]:
        line = line.strip()
        if len(line) > 3 and not any(x in line.lower() for x in ["invoice", "date", "bill"]):
            vendor = line
            break

    # ✅ Date
    date_patterns = [
        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}",
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}"
    ]

    invoice_date = None
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            invoice_date = match.group(0)
            break

    # ✅ Amount
    total_amount = None
    match = re.search(r"total[^0-9]*(\d+[.,]\d+)", text, re.IGNORECASE)

    if match:
        total_amount = match.group(1)
    else:
        amounts = re.findall(r"\d+\.\d+", text)
        if amounts:
            total_amount = str(max([float(a) for a in amounts]))

    # ✅ Currency
    currency = "USD" if "$" in text else "INR"

    return {
        "vendor": vendor or "Unknown",
        "invoice_date": invoice_date or "N/A",
        "total_amount": total_amount or "0",
        "currency": currency
    }


# ==============================
# 🔥 FORMAT DETECTION
# ==============================
def detect_format(parsed_data):
    vendor = parsed_data["vendor"]

    if vendor in known_vendors:
        return "existing"
    else:
        known_vendors[vendor] = True
        return "new"


# ==============================
# 🔥 DUPLICATE CHECK
# ==============================
def check_duplicate(data):
    existing = supabase.table("invoices") \
        .select("*") \
        .eq("vendor", data["vendor"]) \
        .eq("total_amount", data["total_amount"]) \
        .eq("invoice_date", data["invoice_date"]) \
        .execute()

    return len(existing.data) > 0


# ==============================
# ✅ HOME
# ==============================
@app.get("/")
def home():
    return {"message": "Invoice Extraction API 🚀"}


# ==============================
# ✅ GET INVOICES
# ==============================
@app.get("/invoices")
def get_invoices():
    try:
        response = supabase.table("invoices").select("*").execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}


# ==============================
# ✅ DELETE
# ==============================
@app.delete("/invoice/{id}")
def delete_invoice(id: int):
    try:
        supabase.table("invoices").delete().eq("id", id).execute()
        return {"message": "Deleted successfully"}
    except Exception as e:
        return {"error": str(e)}


# ==============================
# ✅ ANALYTICS
# ==============================
@app.get("/analytics")
def analytics():
    try:
        response = supabase.table("invoices").select("*").execute()
        data = response.data

        total_spend = 0
        vendor_summary = {}

        for item in data:
            try:
                amount = float(str(item.get("total_amount", "0")).replace(",", ""))
            except:
                amount = 0

            total_spend += amount

            vendor = item.get("vendor") or "Unknown"

            if vendor in vendor_summary:
                vendor_summary[vendor] += amount
            else:
                vendor_summary[vendor] = amount

        return {
            "total_invoices": len(data),
            "total_spend": round(total_spend, 2),
            "vendor_summary": vendor_summary
        }

    except Exception as e:
        return {"error": str(e)}


# ==============================
# ✅ UPLOAD
# ==============================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ❌ Restrict only images
        if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            return {"error": "Only JPG/PNG images supported ❌"}

        # 🔥 Save file
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_name)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🔥 OCR
        text = extract_text(file_path)

        if not text.strip():
            return {"error": "OCR failed to extract text ❌"}

        # 🔥 Parse
        parsed_data = extract_data(text)

        # 🔥 Format detection
        format_type = detect_format(parsed_data)

        # 🔥 Duplicate check
        if check_duplicate(parsed_data):
            return {"error": "Duplicate invoice detected ❌"}

        # 🔥 Upload to Supabase Storage
        with open(file_path, "rb") as f:
            supabase.storage.from_("invoices").upload(
                unique_name,
                f,
                {"content-type": "application/octet-stream"}
            )

        file_url = f"{SUPABASE_URL}/storage/v1/object/public/invoices/{unique_name}"

        # 🔥 Save to DB
        supabase.table("invoices").insert({
            "filename": unique_name,
            "file_url": file_url,
            "vendor": parsed_data["vendor"],
            "invoice_date": parsed_data["invoice_date"],
            "total_amount": parsed_data["total_amount"],
            "currency": parsed_data["currency"],
            "format_type": format_type
        }).execute()

        return {
            "message": "Uploaded successfully ✅",
            "format": format_type,
            "parsed": parsed_data
        }

    except Exception as e:
        return {"error": str(e)}