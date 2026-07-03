# 🍽️ Menu Sidekick Backend API

A comprehensive backend API for Menu Sidekick mobile application, designed to help users with dietary restrictions and preferences analyze restaurant menus for safe dining experiences. Built with Django REST Framework featuring menu scanning, dietary analysis, admin dashboard, and user management.

## 📋 Environment Variables

Required environment variables for deployment:
```bash
DEBUG=True
DJANGO_ALLOWED_HOSTS=http://127.0.0.1:8000,http://localhost:8000,34.229.201.189:8000,34.229.201.189
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,localhost,127.0.0.1,api.menusidekick.app,34.229.201.189

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SECRET_KEY=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_CUSTOM_DOMAIN=menu-sidekick-bucket.s3.amazonaws.com
AWS_S3_FILE_OVERWRITE=False
AWS_S3_REGION_NAME=

RDS_DB_NAME=
RDS_MASTERUSERNAME=postgres
RDS_MASTERPASSWORD=
RDS_HOSTNAME=
RDS_PORT=5432


OPENAI_API_KEY=
```



## Features

- 🔐 **User Authentication**
  - JWT-based login/register using **Simple-JWT**
  - Social media authentication support (Google, Facebook, Apple)
  - Custom user profiles with dietary preferences and allergies
  
- 🍽️ **Menu Scanning & Analysis**
  - OCR-powered menu text extraction from images
  - Dietary preference matching and allergen detection
  - Menu item modification suggestions
  - Multi-language menu translation support
  
- 📊 **Admin Dashboard**
  - Restaurant menu management system
  - User analytics and dietary trend insights
  - Menu translation management
  - System performance monitoring
  
- 🥗 **Dietary Management**
  - Comprehensive dietary restriction tracking
  - Allergen database management
  - Custom meal creation and modification
  - Nutritional information integration

## Tech Stack

- Django, Django REST Framework
- SimpleJWT for JWT authentication
- drf_yasg for Swagger API Documentation
- OCR integration for menu scanning
- Multi-language translation services
- Docker containerization
- AWS deployment with CI/CD pipeline

## 📄 API Documentation (Swagger)

Access the interactive API documentation:

```bash
http://localhost:8000/api/docs/   # Swagger UI
http://localhost:8000/api/redoc/  # ReDoc UI 
```

## 🪪 Authorization

Click "Authorize" in Swagger UI and paste your JWT token:

```
Bearer <your_access_token>
```

## 🗄️ Database Models

### Core Models
- **User**: Extended with dietary preferences, allergies, and profile settings
- **Menu**: Restaurant menu information with OCR text data
- **Scan**: Menu scan history and analysis results
- **DietaryRestriction**: Allergen and dietary preference definitions
- **AdminUser**: Dashboard access and restaurant management

## 📁 Project Structure

The project follows a modular and scalable architecture:
```
backend/
├── core/                    # Project-level configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI configuration
├── apps/                    # Modular app structure
│   ├── admin_dashboard/     # Admin panel and management APIs
│   ├── diets/              # Dietary restrictions and preferences APIs
│   ├── scans/              # Menu scanning and analysis APIs
│   └── users/              # User authentication and profile APIs
├── docker/                  # Docker configuration files
├── deployment/              # CI/CD and deployment scripts
└── manage.py
```

App Responsibilities:
- `core/`: Project-level settings, URL routing, and configuration
- `apps/admin_dashboard/`: Restaurant menu management and analytics
- `apps/diets/`: Dietary restrictions, allergens, and preferences management
- `apps/scans/`: Menu scanning, OCR processing, and analysis logic
- `apps/users/`: User authentication, profiles, and social login integration

## 🔐 API Endpoints & Usage

### 👤 User Authentication

#### Register
`POST /api/auth/register/`
```json
{
  "username": "johndoe",
  "email": "john@example.com", 
  "password": "securepass123",
  "dietary_preferences": ["vegetarian", "gluten-free"],
  "allergies": ["nuts", "shellfish"]
}
```

#### Login (JWT)
`POST /api/auth/login/`
```json
{
  "username": "johndoe",
  "password": "securepass123"
}
```

#### Social Login
`POST /api/auth/social-login/`
```json
{
  "provider": "google",
  "access_token": "social_provider_token"
}
```

### 📱 Menu Scanning

#### Scan Menu
`POST /api/scans/menu/`
```json
{
  "scan_id": "UUID",
  "source_type": "photo|pdf|url|upload",
  "file_url": "signed-url-or-null",
  "detected_language": "fr",
  "preference": { …PreferencePayload… }
}
```

#### Get Scan Results
`GET /api/scans/{scan_id}/results/`

#### Get Scan History
`GET /api/scans/history/`

### 🥗 Dietary Management

#### Get Dietary Options
`GET /api/diets/restrictions/`

#### Update User Preferences --> What you send to the AI/OCR team
`PUT /api/diets/preferences/`
```json
{
  "profile_id": "UUID",
  "diet_type": "vegan|vegetarian|halal|kosher|keto|none|…",
  "strictness": 0,
  "allergens": ["peanut","gluten","shellfish", "..."],
  "medical_conditions": ["celiac","diabetes","..."],
  "banned_ingredients": ["gelatin","anchovy","..."],
  "preferred_language": "en",
  "region": "BD"
}
```


### 🏢 Admin Dashboard

#### Restaurant Management
```bash
GET /api/admin/restaurants/        # List restaurants
POST /api/admin/restaurants/       # Create restaurant (admin only)
PUT /api/admin/restaurants/{id}/   # Update restaurant (admin only)
```

#### Analytics
`GET /api/admin/analytics/dashboard/`

#### User Management
`GET /api/admin/users/statistics/`

## 🧮 Business Logic

### Menu Scanning System
1. **OCR Processing**: Extract text from menu images using advanced OCR
2. **Language Detection**: Auto-detect menu language for translation
3. **Item Parsing**: Identify individual menu items and ingredients
4. **Dietary Analysis**: Match items against user preferences and restrictions

### Dietary Analysis Engine
- **Allergen Detection**: Scan ingredients for potential allergens
- **Preference Matching**: Compare items against dietary preferences
- **Modification Suggestions**: Recommend menu item modifications
- **Safety Scoring**: Rate items based on user's dietary profile

### Admin Dashboard Features
- **Restaurant Analytics**: Track popular items and dietary trends
- **User Insights**: Analyze user behavior and preferences
- **Menu Management**: Upload and manage restaurant menus
- **Translation Oversight**: Review and approve menu translations

## 🚀 Setup & Installation

### ✅ Clone the repository
```bash
git clone <repository-url>
cd menu-sidekick-backend
```

### ✅ Navigate to backend directory
```bash
cd backend
```

### ✅ Install dependencies using uv
```bash
uv sync
```

### ✅ Activate Virtual Environment
```bash
source .venv/bin/activate  
```

### ✅ Environment Setup
```bash
cp .env.example .env
# Configure your environment variables
```

### ✅ Apply migrations
```bash
python manage.py migrate
```

### ✅ Create superuser for admin operations
```bash
python manage.py createsuperuser
```

### ✅ Run the development server
```bash
python manage.py runserver
```

### ✅ Access API Documentation
```bash
http://localhost:8000/api/docs/
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## ☁️ AWS Deployment

### Prerequisites
- AWS CLI configured
- Docker installed
- CI/CD pipeline setup

### Deployment Steps
```bash
# Build and push to ECR
./deployment/deploy.sh production

# Deploy to ECS
./deployment/ecs-deploy.sh
```

## 🔄 CI/CD Pipeline

The project includes automated CI/CD pipeline with:
- Automated testing on pull requests
- Docker image building and pushing to ECR
- Automated deployment to AWS ECS
- Environment-specific configurations

## 🔄 Testing Workflow

### For Mobile App Integration:
1. **Register User** ➝ `POST /api/auth/register/`
2. **Login** ➝ `POST /api/auth/login/` (get JWT token)
3. **Set Dietary Preferences** ➝ `PUT /api/diets/preferences/`
4. **Scan Menu** ➝ `POST /api/scans/menu/`
5. **Get Analysis Results** ➝ `GET /api/scans/{scan_id}/results/`
6. **View Recommendations** ➝ Based on dietary analysis

### For Admin Operations:
1. **Create Superuser** ➝ `python manage.py createsuperuser` (in terminal)
2. **Login with Admin** ➝ `POST /api/auth/login/` (use superuser credentials)
3. **Authorize** ➝ Use admin JWT token in Swagger UI
4. **Admin Operations** ➝ Manage restaurants, view analytics, user management

## 🔧 Assumptions & Limitations

### Current Implementation
- OCR processing optimized for English menus (multi-language support in progress)
- Dietary analysis based on keyword matching (ML enhancement planned)
- Admin dashboard provides basic analytics (advanced reporting in development)

### Known Limitations
- OCR accuracy depends on image quality and lighting
- Translation service requires internet connectivity
- Real-time analysis may have latency for complex menus
- Social login requires proper OAuth configuration



## ℹ️ Notes

- This project uses **uv** for modern Python package management
- Authentication supports both traditional JWT and social login
- API documentation generated with **drf_yasg**
- Docker containerization for consistent deployment environments
- AWS deployment with ECS and RDS for scalability
- CI/CD pipeline ensures automated testing and deployment
- Project follows Django best practices with modular and scalable app design#   M e n u S i d e K i c k  
 
# MenuSideKick
