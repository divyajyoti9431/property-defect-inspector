# Property Defect Inspection System

AI-powered web app for detecting property defects from photos and generating PDF inspection reports.

## Features
- Upload multiple property images (drag & drop)
- GPT-4o Vision AI detects: cracks, water damage, paint defects, mold, tile issues, electrical, plumbing, and more
- Comprehensive flat-buyer inspection checklist
- PDF report with defect table, severity ratings, buyer impact & recommendations
- Email report delivery

## Tech Stack
- **Backend**: Python FastAPI
- **AI**: OpenAI GPT-4o Vision
- **PDF**: ReportLab
- **Frontend**: HTML + Tailwind CSS

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY in .env
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000

## Get OpenAI API Key
https://platform.openai.com/api-keys  (requires billing credits)
