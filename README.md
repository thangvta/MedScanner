
# 📱 Mobile Web-App for Detecting Drug-Drug Interactions via Prescription Scans

This is an AI-powered mobile web application designed to **automatically detect potential drug-drug interactions (DDIs)** by analyzing scanned prescriptions. It aims to enhance **patient safety**, **streamline clinical workflows**, and **support doctors, pharmacists, and patients** with intelligent medication validation.

---

## 🧠 Key Features

* **OCR + AI-powered Text Recognition**
  Extracts drug names and dosages from handwritten and printed prescriptions using a hybrid OCR pipeline (Tesseract, VietOCR, GPT-4o fallback).

* **Drug Interaction Detection**
  Queries DrugBank, DDInter, and SuperDRUG2 to flag risky interactions and contraindications.

* **Dosage & Allergy Verification**
  Matches prescribed dosages with medical guidelines and patient-specific data (age, weight, allergies).

* **Real-Time Inventory Tracking**
  Automatically updates drug stock levels and generates low-inventory alerts.

* **Multilingual Interface**
  Fully supports both English and Vietnamese. Built with accessibility in mind for mobile users.

---

## 🛠️ Tech Stack

### Backend

* **Python 3.11**, **Flask**, **SQLAlchemy**
* **PostgreSQL** database
* **Flask-Login** for role-based authentication
* **Flask-Babel** for multilingual support
* **Gunicorn** WSGI for production deployment

### Frontend

* **HTML5**, **CSS3**, **Bootstrap 5**, **JavaScript**
* Camera integration via **HTML5 Camera API**
* Responsive, mobile-first design

### AI & CV Components

* **Tesseract OCR** for text extraction
* **VietOCR** for Vietnamese handwriting
* **OpenAI GPT-4o** as a fallback for ambiguous inputs
* **OpenCV** for image preprocessing

---

## 🧪 Testing

### Types of Testing

* ✅ Unit Tests: Models, utility functions, and routes
* ✅ Integration Tests: End-to-end workflows
* ✅ User Acceptance Tests (UAT): Validated by healthcare professionals
* ✅ Prototype Simulations: UI and interaction logic demos

### Running Tests

```bash
# Install dependencies
pip install pytest pytest-flask pytest-cov

# Run all tests
python -m pytest tests/

# Run tests with coverage
pytest --cov=medscanner tests/
```

---

## 🏥 System Architecture

* **Modular design** for scalability and future expansion (e.g., EMR integration)
* **RESTful APIs** for data access and third-party service integration
* **Secure session management** and encrypted data handling
* Real-time alerts, reports, and notifications built into UI

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/thangvta/MedScanner.git
cd ddi-scanner-app
```

### 2. Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
flask db init
flask db migrate
flask db upgrade
```

### 4. Run the Server

```bash
flask run
```

---

## 🔐 Roles & Access

* **Patient**: Can scan prescriptions and view interaction reports.
* **Doctor**: Can access patient history, prescribe medication.
* **Pharmacist**: Can manage inventory and validate prescriptions.

---

## 👥 Contributors

* **To Ba Son** – Workflow Design, VAIPE Integration
* **Ta Viet Thang** – OCR Pipeline, Tesseract/VietOCR Evaluation
* **Bui Huy Linh Phuc** – DDI Dataset Integration, Database Design
* **Supervisor:** Prof. Pham Huy Hieu

---

## 📄 License

© 2025 To Ba Son, Ta Viet Thang, Bui Huy Linh Phuc
Licensed to VinUniversity under an open-access, non-exclusive license.

---

