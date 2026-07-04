# 🍽️ MenuSideKick Backend

AI-powered dietary assistant backend built with Django REST Framework.

MenuSideKick helps users identify safe food choices by analyzing restaurant menus, extracting menu items through OCR, and matching them against dietary preferences, allergies, and nutritional restrictions.

---

## 🚀 Features

### Authentication & User Management
- JWT Authentication
- User Registration & Login
- Social Authentication
- Role-Based Access Control (RBAC)

### Menu Processing
- OCR-based menu extraction
- Image-to-text conversion
- Menu item parsing and categorization

### Dietary Intelligence
- Allergen detection
- Dietary restriction matching
- Personalized food recommendations
- Ingredient risk analysis

### API Infrastructure
- RESTful API architecture
- OpenAPI / Swagger documentation
- Rate limiting
- CORS protection
- Production-ready error handling

### Deployment & Scalability
- Dockerized environment
- Development & Production configurations
- PostgreSQL support
- AWS deployment ready
- CI/CD friendly structure

---

## 🛠️ Tech Stack

### Backend
- Django
- Django REST Framework
- Python

### Authentication
- JWT Authentication
- OAuth / Social Login

### Database
- PostgreSQL

### AI & OCR
- OCR Processing
- NLP-based dietary analysis

### Infrastructure
- Docker
- Docker Compose
- AWS

---

## 📂 Project Structure

```text
MenuSideKick/
│
├── apps/                  # Application modules
├── core/                  # Core settings and configurations
├── .github/               # GitHub workflows
│
├── Dockerfile
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── manage.py
├── pyproject.toml
├── entrypoint.sh
│
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/MenuSideKick.git
cd MenuSideKick
```

### Create Environment Variables

Create:

```bash
.env
```

Example:

```env
DEBUG=True

SECRET_KEY=your-secret-key

DB_NAME=menusidekick
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=*
```

---

## 🐳 Run with Docker

Development:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

Production:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

---

## 🔄 Apply Migrations

```bash
docker exec -it backend python manage.py migrate
```

Create Superuser:

```bash
docker exec -it backend python manage.py createsuperuser
```

---

## ▶️ Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start server:

```bash
python manage.py runserver
```

---

## 📖 API Documentation

Swagger UI:

```text
/api/docs/
```

OpenAPI Schema:

```text
/api/schema/
```

---

## 🔐 Authentication

MenuSideKick uses JWT Authentication.

### Obtain Token

```http
POST /api/auth/login/
```

Request:

```json
{
    "email": "user@example.com",
    "password": "password"
}
```

Response:

```json
{
    "access": "jwt_access_token",
    "refresh": "jwt_refresh_token"
}
```

---

## 📸 OCR Workflow

1. User uploads menu image.
2. OCR extracts text.
3. Menu items are identified.
4. Ingredients are analyzed.
5. Dietary restrictions are matched.
6. Safe food recommendations are returned.

---

## 📊 Example Use Cases

- Gluten-free dining
- Vegan food recommendations
- Nut allergy detection
- Dairy-free meal selection
- Personalized dietary guidance

---

## 🔒 Security Features

- JWT Authentication
- RBAC Permissions
- Rate Limiting
- CORS Protection
- Input Validation
- Secure Environment Configuration

---

## 🚀 Future Enhancements

- AI-powered meal scoring
- Restaurant recommendation engine
- Nutritional analytics dashboard
- Multi-language OCR support
- LLM-powered menu explanation

---

## 👨‍💻 Author

### Prosenjit Saha Apu

AI Engineer & Backend Developer

- LinkedIn: https://linkedin.com/in/your-profile
- GitHub: https://github.com/apusaha0011

---

## 📄 License

This project is licensed under the MIT License.
