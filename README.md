INVOICE AI - BACKEND

Description:
This is a FastAPI backend application for processing invoices using OCR, storing data in Supabase, and providing analytics.

--------------------------------------------------

Features:
- JWT Authentication (Login/Register)
- File upload (JPG, PNG, PDF)
- OCR using Tesseract
- Invoice data extraction
- Supabase database integration
- Analytics API
- Static file serving (image preview)

--------------------------------------------------

Technologies Used:
- FastAPI (Python)
- Supabase (Database)
- Tesseract OCR
- pdf2image
- JWT (python-jose)
- Passlib (bcrypt)

--------------------------------------------------

Project Structure:

backend/
  main.py
  uploads/
  .env
  requirements.txt

--------------------------------------------------

Setup Instructions:

1. Clone the repository:
   git clone <repo-link>

2. Navigate to backend folder:
   cd backend

3. Create virtual environment:
   python -m venv venv
   venv\Scripts\activate

4. Install dependencies:
   pip install -r requirements.txt

5. Create .env file:
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key

6. Run server:
   uvicorn main:app --reload

--------------------------------------------------

API Endpoints:

Authentication:
POST /register
POST /login

Invoices:
GET /invoices
POST /upload
DELETE /invoice/{id}

Analytics:
GET /analytics

--------------------------------------------------

Authentication:

All protected routes require JWT token:

Authorization: Bearer <token>

--------------------------------------------------

File Upload Support:

- JPG
- PNG
- PDF

--------------------------------------------------

OCR Flow:

1. Upload file
2. Extract text using Tesseract
3. Parse invoice data
4. Store in database
5. Return response

--------------------------------------------------

Requirements:

- Python 3.9+
- Tesseract OCR installed
- Poppler installed (for PDF)

--------------------------------------------------

Future Enhancements:

- AI-based invoice parsing
- Multi-language OCR
- Cloud storage integration
- Role-based authentication

--------------------------------------------------

Author:
Akash Pandit
