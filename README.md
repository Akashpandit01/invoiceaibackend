📄 Invoice Extraction AI – Backend

🚀 Overview
This backend service is built using FastAPI to process invoice documents, extract structured data using OCR, and store results in Supabase.

It supports uploading invoice images, extracting key fields, storing them in a database, and providing analytics insights.

------------------------------------------------------------

🧠 Features

✅ File Upload
- Upload invoice images (JPG, PNG)
- Stores files in Supabase Storage

✅ OCR Processing
- Uses Tesseract OCR
- Extracts raw text from invoice images

✅ Data Extraction
- Parses extracted text into structured JSON:
  - Vendor Name
  - Invoice Date
  - Total Amount
  - Currency

✅ Format Detection
- Detects known invoice formats based on vendor
- Reuses parsing logic for better performance

✅ Duplicate Detection
- Prevents duplicate invoices using:
  - Vendor
  - Amount
  - Date

✅ Analytics API
- Total invoices count
- Total spend
- Vendor-wise spend
- Monthly spend trends

------------------------------------------------------------

🛠️ Tech Stack

- Backend Framework: FastAPI
- OCR Engine: Tesseract
- Database & Storage: Supabase
- Language: Python

------------------------------------------------------------

📂 Project Structure

backend/
│── main.py
│── requirements.txt
│── uploads/
│── .env

------------------------------------------------------------

⚙️ Setup Instructions

1️⃣ Clone Repository
git clone [https://github.com/your-username/your-repo.git](https://github.com/Akashpandit01/invoiceaibackend/
cd invoiceaibackend

------------------------------------------------------------

2️⃣ Install Dependencies
pip install -r requirements.txt

------------------------------------------------------------

3️⃣ Setup Environment Variables

Create a .env file:

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

------------------------------------------------------------

4️⃣ Run Server
uvicorn main:app --reload

------------------------------------------------------------

5️⃣ API Docs
http://127.0.0.1:8000/docs

------------------------------------------------------------

📡 API Endpoints

🔹 Upload Invoice
POST /upload

🔹 Get All Invoices
GET /invoices

🔹 Delete Invoice
DELETE /invoice/{id}

🔹 Analytics
GET /analytics

------------------------------------------------------------

⚠️ Limitations

- Currently supports only JPG/PNG images
- PDF support can be added using pdf2image
- Parsing is rule-based (regex), not LLM-based
- No user authentication implemented

------------------------------------------------------------

🚀 Future Improvements

- Integrate LLM (OpenAI/Gemini) for better parsing
- Add PDF support
- Improve format detection using ML
- Add user authentication
- Add confidence scoring

------------------------------------------------------------

🌐 Deployment

- Backend deployed on Render
- Accessible via public API URL

------------------------------------------------------------

🎯 Conclusion

This backend demonstrates a scalable architecture for invoice processing using OCR and structured data extraction, with scope for AI enhancement using LLMs.
