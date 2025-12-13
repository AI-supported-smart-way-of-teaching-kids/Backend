# 🎓 **Learnify Backend - Django Educational Platform**

## 📖 **Project Overview**

Learnify is an **intelligent educational platform** for kindergarten students (KG1-KG3) that provides personalized learning experiences through AI-powered recommendations. This repository contains the **Django backend** for the Learnify platform.

### 🎯 **Core Features**
- **User Management**: Child, teacher, and admin roles
- **Content Management**: Lessons, quizzes, and educational media
- **Progress Tracking**: Real-time learning progress and achievements
- **AI Integration**: ML-powered personalized recommendations
- **Class-Based Learning**: Tailored content for KG1, KG2, KG3 levels
- **Security**: Audit logging and secure authentication

---

## 🏗️ **Project Structure**

```
backend/
├── accounts/          # User authentication & profiles
├── lessons/           # Lesson content management
├── quizzes/           # Quizzes and assessments
├── progress/          # Progress tracking & badges
├── ai/                # ML pipeline integration tables
├── core/              # Core utilities & audit logs
├── config/            # Django settings & configuration
├── media/             # Uploaded media files
├── static/            # Static files
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container configuration
└── docker-compose.yml # Multi-container setup
```

---

## 📦 **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Django 4.2+ | Backend API and admin |
| **Database** | PostgreSQL 14 | Primary data storage |
| **Cache** | Redis | Session and cache management |
| **ORM** | Django ORM | Database abstraction |
| **API** | Django REST Framework | RESTful API endpoints |
| **Authentication** | JWT | Secure user authentication |
| **ML Integration** | Custom tables | ML pipeline data exchange |

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### **Local Development Setup**

#### **Option 1: Using Docker (Recommended)**
```bash
# Clone the repository
git clone <repository-url>
cd backend

# Copy environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access the application
# Django Admin: http://localhost:8000/admin
# API: http://localhost:8000/api/
```

#### **Option 2: Manual Setup**
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
export DATABASE_URL=postgres://user:password@localhost:5432/learnify
export SECRET_KEY=your-secret-key
export DEBUG=True

# 4. Create database
createdb learnify

# 5. Run migrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
```

---

## 📊 **Database Schema**

### **Core Tables**
| App | Model | Purpose | Key Relationships |
|-----|-------|---------|-------------------|
| `accounts` | `User` | Authentication & basic info | - |
| `accounts` | `ChildProfile` | Child-specific data | User (OneToOne) |
| `accounts` | `TeacherProfile` | Teacher metadata | User (OneToOne) |
| `lessons` | `Lesson` | Educational content | TeacherProfile (ForeignKey) |
| `quizzes` | `Quiz` | Lesson assessments | Lesson (ForeignKey) |
| `quizzes` | `QuizAttempt` | Child's quiz attempts | ChildProfile, Quiz (ForeignKeys) |
| `progress` | `Progress` | Learning progress | ChildProfile, Lesson (ForeignKeys) |
| `ai` | `MLStudentMap` | ML ↔ Backend mapping | ChildProfile (ForeignKey) |
| `ai` | `Recommendation` | AI recommendations | ChildProfile, Lesson (ForeignKeys) |
| `core` | `AuditLog` | Security events | User (ForeignKey) |

### **ML Pipeline Tables**
| Table | Purpose | Data Flow |
|-------|---------|-----------|
| `lesson_interactions_raw` | Raw lesson interaction data | Backend → ML |
| `quiz_attempts_raw` | Raw quiz attempt data | Backend → ML |
| `lesson_interactions_clean` | Cleaned interaction data | ML → Backend |
| `quiz_attempts_clean` | Cleaned quiz data | ML → Backend |
| `student_ml_dataset` | Final ML dataset | ML → Backend |
| `recommendations` | Generated recommendations | ML → Backend |

---

## 🔌 **API Endpoints**

### **Authentication**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | User registration | No |
| POST | `/api/auth/login/` | User login | No |
| POST | `/api/auth/logout/` | User logout | Yes |
| POST | `/api/auth/refresh/` | Refresh JWT token | Yes |

### **User Management**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile/` | Get current user profile |
| PUT | `/api/users/profile/` | Update user profile |
| GET | `/api/children/{id}/` | Get child profile |
| GET | `/api/children/{id}/progress/` | Get child's progress |
| GET | `/api/children/{id}/recommendations/` | Get AI recommendations |

### **Content Management**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/lessons/` | List all lessons |
| GET | `/api/lessons/{id}/` | Get lesson details |
| GET | `/api/lessons/{id}/quiz/` | Get lesson quiz |
| POST | `/api/lessons/{id}/progress/` | Update lesson progress |
| POST | `/api/quizzes/{id}/attempt/` | Submit quiz attempt |

### **Admin & Monitoring**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/analytics/` | Platform analytics |
| GET | `/api/admin/audit-logs/` | View audit logs |
| GET | `/api/health/` | System health check |

---

## 🤖 **ML Integration**

### **Data Flow**
```
[Backend App] → [Raw ML Tables] → [ML Pipeline] → [Clean/Feature Tables] → [Recommendations]
```

### **Setup for ML Team**
1. **Database Access**: ML team needs read/write access to `ai_*` tables
2. **Environment Variables**:
   ```bash
   ML_DB_HOST=localhost
   ML_DB_NAME=learnify
   ML_DB_USER=ml_user
   ML_DB_PASSWORD=ml_password
   ```
3. **Data Mapping**: Use `MLStudentMap` to map `ml_student_id` to `child_id`

### **ML Team Responsibilities**
- Read from `*_raw` tables
- Write to `*_clean`, `*_features`, `student_ml_dataset` tables
- Generate and write to `recommendations` table
- Update `MLModel` table with model metadata

---

## 🎯 **Class-Based Learning (KG1, KG2, KG3)**

### **Class Structure**
```python
# Child's class assignment (auto-based on age)
AGE_TO_CLASS = {
    4: 'KG1',  # Kindergarten 1
    5: 'KG2',  # Kindergarten 2  
    6: 'KG3',  # Kindergarten 3
}

# Lesson classification
KG_CLASSES = [
    ('KG1', 'Kindergarten 1 (Age 4)'),
    ('KG2', 'Kindergarten 2 (Age 5)'),
    ('KG3', 'Kindergarten 3 (Age 6)'),
    ('MIXED', 'Mixed (All Classes)'),
]
```

### **Recommendation Logic**
The system considers:
1. **Class Level**: KG1, KG2, or KG3 appropriate content
2. **Performance**: Individual mastery level (Low/Medium/High)
3. **Skill Gaps**: Areas needing improvement
4. **Learning Pace**: Time spent, completion rates

---

## 🔒 **Security & Authentication**

### **Authentication Method**
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Child, Teacher, Admin roles
- **Password Policies**: BCrypt hashing with salt

### **Security Features**
- **Audit Logging**: All critical actions logged
- **CORS Protection**: Configured allowed origins
- **Rate Limiting**: API request limiting
- **SQL Injection Protection**: Django ORM parameterized queries
- **XSS Protection**: Django template auto-escaping

### **Environment Variables**
```bash
# Required
SECRET_KEY=your-django-secret-key
DEBUG=False  # Set to True for development
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000

# ML Integration
ML_DB_USER=ml_user
ML_DB_PASSWORD=ml_password
```

---

## 📈 **Monitoring & Analytics**

### **Built-in Monitoring**
- **Django Admin**: `/admin` for data management
- **Audit Logs**: All user actions tracked in `core.AuditLog`
- **Health Checks**: `/api/health/` endpoint
- **Error Tracking**: Sentry integration (optional)

### **Key Metrics Tracked**
- User engagement (lessons completed, time spent)
- Quiz performance (average scores, attempts)
- Recommendation effectiveness (click-through rates)
- System performance (response times, error rates)

---

## 🐳 **Docker Deployment**

### **Production Deployment**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: learnify
      POSTGRES_USER: learnify_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
  
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    environment:
      DATABASE_URL: postgres://learnify_user:${DB_PASSWORD}@postgres:5432/learnify
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
```

### **Deployment Commands**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input
```

---

## 🧪 **Testing**

### **Running Tests**
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts.tests
python manage.py test lessons.tests

# Run with coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

### **Test Structure**
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── api/           # API endpoint tests
└── fixtures/      # Test data fixtures
```

---

## 📋 **Development Workflow**

### **Branch Strategy**
```
main
├── develop
│   ├── feature/user-authentication
│   ├── feature/lesson-management
│   └── bugfix/login-issue
└── release/v1.0.0
```

### **Commit Convention**
```
feat: add user registration API
fix: resolve login token expiration
docs: update API documentation
test: add unit tests for quiz model
refactor: reorganize models structure
```

---

## 🤝 **Team Collaboration**

### **Backend Team Responsibilities**
- API development and maintenance
- Database design and optimization
- Authentication and security
- Integration with ML pipeline
- Deployment and monitoring

### **ML Team Collaboration**
- **Shared Database**: ML team reads/writes to `ai_*` tables
- **Data Format**: Raw data follows specified schema
- **Communication**: Weekly syncs on data quality and recommendations
- **Error Handling**: Fallback recommendations when ML fails

### **Frontend Team Collaboration**
- **API Contracts**: OpenAPI/Swagger documentation
- **WebSocket Events**: Real-time progress updates
- **File Uploads**: Media upload endpoints
- **Authentication**: JWT token flow

---

## 📚 **Documentation**

### **Available Documentation**
1. **API Documentation**: `/api/docs/` (Swagger/OpenAPI)
2. **Database Schema**: `/docs/schema/` (ER diagrams)
3. **Deployment Guide**: `/docs/deployment.md`
4. **ML Integration**: `/docs/ml-integration.md`
5. **API Reference**: `/docs/api-reference.md`

### **Generating Documentation**
```bash
# Generate OpenAPI schema
python manage.py generateschema > schema.yaml

# Generate database diagram
python manage.py graph_models -a -g -o docs/models.png
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Create database user
sudo -u postgres createuser learnify_user
sudo -u postgres createdb learnify

# Grant permissions
sudo -u postgres psql -c "ALTER USER learnify_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE learnify TO learnify_user;"
```

#### **Migration Issues**
```bash
# Reset migrations (development only)
python manage.py migrate --fake accounts zero
python manage.py migrate --fake lessons zero
python manage.py migrate --fake ai zero
python manage.py migrate
```

#### **ML Pipeline Integration Issues**
```bash
# Check ML tables exist
python manage.py dbshell
\dt ai_*

# Verify ML student mapping
python manage.py shell
from ai.models import MLStudentMap
print(MLStudentMap.objects.count())
```

---

## 📞 **Support & Contact**

### **Development Team**
- **Backend Lead**: [Name] - [email]
- **Database Admin**: [Name] - [email]
- **DevOps Engineer**: [Name] - [email]

### **ML Team Contact**
- **ML Lead**: [Name] - [email]
- **Data Engineer**: [Name] - [email]

### **Emergency Contacts**
- **Production Issues**: #backend-alerts Slack channel
- **Database Issues**: #dba-alerts Slack channel
- **Security Issues**: security@learnify.example.com

---

## 📄 **License**

This project is proprietary and confidential. All rights reserved.

© 2024 Learnify Educational Technologies. Unauthorized copying, distribution, or use is prohibited.

---

## 🙏 **Acknowledgments**

- **Django Community** for the excellent web framework
- **PostgreSQL Team** for robust database solutions
- **ML Team** for intelligent recommendation algorithms
- **Educational Consultants** for age-appropriate curriculum design

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Maintainer**: Backend Engineering Team


