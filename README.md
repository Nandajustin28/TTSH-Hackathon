# Tan Tock Seng Hospital Hackathon
## Triaging System for Patient Admission

This project uses:
- **Backend:** Django
- **Frontend:** CSS

## Setup Instructions

### 1) Install backend dependencies

From the project root:

```bash
python -m pip install -r requirements.txt
```

### 2) Run Django migrations

```bash
python manage.py migrate
```

### 3) Create super admin user (as required) (OPTIONAL)

```bash
python manage.py createsuperuser
```

### 4) Generate Patient data (OPTIONAL)

To populate the current database with sample patients to visualize the workflows:

```bash
python manage.py generate_test_data --clear --count 30
```

Options:
- `--clear`: Clear existing data before generating (optional)
- `--count`: Number of employees to generate (default: 30)

### 5) Install frontend dependencies

```bash
cd frontend
npm install
```

### 6) Configure frontend environment

Create `frontend/.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 7) Start backend

From the project root:

```bash
python manage.py runserver 8000
```

### 8) Start frontend

In another terminal:

```bash
cd frontend
npm run dev
```

## Run URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin
