# Job AI Agent - Architecture Documentation

## 📋 Overview

The Job AI Agent is a local-first AI-powered Product Manager job acquisition system built with Python, FastAPI, and Streamlit. This document outlines the complete architecture, design decisions, and implementation patterns.

## 🏗️ System Architecture

### High-Level Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   SQLite DB     │
│   Dashboard     │◄──►│   Backend API   │◄──►│   Local Storage │
│   (Port 8501)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface│    │  Business Logic │    │   Data Models   │
│   - Dashboard   │    │  - Job Fetching │    │  - Jobs         │
│   - Settings    │    │  - AI Matching  │    │  - Applications │
│   - Monitoring  │    │  - Notifications│    │  - Users        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Principles

1. **Local-First**: All data stored locally, privacy-focused
2. **Async-Ready**: Full async/await support for scalability
3. **Modular Design**: Clean separation of concerns
4. **Configuration-Driven**: Environment-based settings
5. **Dependency Injection**: Testable and maintainable code

## 📁 Project Structure

```
job_ai_agent/
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                       # API layer
│   │   ├── __init__.py
│   │   ├── v1/                   # API version 1 routes
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py           # Job management endpoints
│   │   │   ├── applications.py   # Application endpoints
│   │   │   └── analytics.py      # Analytics endpoints
│   │   └── dependencies/          # FastAPI dependencies
│   │       ├── __init__.py
│   │       └── database.py       # Database session dependency
│   │
│   ├── core/                      # Core application logic
│   │   ├── __init__.py
│   │   ├── config/               # Configuration management
│   │   │   ├── __init__.py
│   │   │   └── settings.py       # Pydantic settings model
│   │   ├── database/             # Database setup and connection
│   │   │   ├── __init__.py
│   │   │   └── connection.py     # SQLAlchemy setup and utilities
│   │   └── logging/              # Logging configuration
│   │       ├── __init__.py
│   │       └── logger.py         # Loguru setup and configuration
│   │
│   ├── models/                    # Data models and schemas
│   │   ├── __init__.py
│   │   ├── entities/             # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base model with common fields
│   │   │   ├── job.py            # Job entity model
│   │   │   ├── application.py    # Application entity model
│   │   │   └── user.py           # User entity model
│   │   └── schemas/              # Pydantic schemas
│   │       ├── __init__.py
│   │       ├── base.py           # Base schemas and response models
│   │       ├── job.py            # Job-related schemas
│   │       └── application.py    # Application-related schemas
│   │
│   ├── services/                  # Business logic services
│   │   ├── __init__.py
│   │   ├── fetchers/             # Job board fetchers
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # Base fetcher interface
│   │   │   ├── linkedin.py       # LinkedIn job fetcher
│   │   │   ├── indeed.py         # Indeed job fetcher
│   │   │   └── glassdoor.py      # Glassdoor job fetcher
│   │   ├── ai/                   # AI processing services
│   │   │   ├── __init__.py
│   │   │   ├── matcher.py        # Job matching algorithm
│   │   │   ├── analyzer.py       # Job description analysis
│   │   │   └── optimizer.py      # Resume optimization
│   │   └── notifications/        # Notification services
│   │       ├── __init__.py
│   │       ├── base.py           # Base notification interface
│   │       ├── telegram.py       # Telegram bot notifications
│   │       └── email.py          # Email notifications
│   │
│   ├── web/                       # Streamlit web interface
│   │   ├── app.py                # Main Streamlit application
│   │   ├── pages/                # Streamlit pages
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py      # Dashboard page
│   │   │   ├── jobs.py           # Jobs management page
│   │   │   ├── applications.py   # Applications page
│   │   │   └── settings.py       # Settings page
│   │   └── components/           # Reusable Streamlit components
│   │       ├── __init__.py
│   │       ├── metrics.py        # Metrics display components
│   │       ├── tables.py         # Data table components
│   │       └── forms.py          # Form components
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── http_client.py        # HTTP client utilities
│       ├── text_processing.py    # Text processing utilities
│       └── scheduler.py          # Scheduler utilities
│
├── scripts/                       # Startup and utility scripts
│   ├── setup.sh                  # Unix/Linux setup script
│   ├── setup.bat                 # Windows setup script
│   ├── start_api.sh              # Unix/Linux API startup script
│   ├── start_api.bat             # Windows API startup script
│   ├── start_streamlit.sh        # Unix/Linux Streamlit startup script
│   └── start_streamlit.bat       # Windows Streamlit startup script
│
├── tests/                         # Test files
│   ├── __init__.py
│   ├── unit/                     # Unit tests
│   │   ├── __init__.py
│   │   ├── test_services.py      # Service layer tests
│   │   ├── test_models.py        # Model tests
│   │   └── test_utils.py         # Utility tests
│   └── integration/              # Integration tests
│       ├── __init__.py
│       ├── test_api.py           # API integration tests
│       └── test_database.py      # Database integration tests
│
├── logs/                          # Application logs
├── data/                          # Database files and data
├── requirements.txt               # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # Project documentation
└── architecture.md               # This architecture document
```

## 🔧 Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation and settings management

### Database
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **SQLite**: Local file-based database (development)
- **PostgreSQL**: Production database option

### Frontend
- **Streamlit**: Rapid web application development
- **HTML/CSS**: Custom styling and components

### HTTP & Async
- **httpx**: Async HTTP client for API calls
- **asyncio**: Python async programming support

### Scheduling
- **APScheduler**: Advanced Python scheduler

### Logging
- **loguru**: Python logging made simple

### AI & ML
- **OpenAI API**: AI-powered job matching and analysis
- **Future**: Custom ML models for job recommendations

### Web Scraping (Future)
- **Playwright**: Browser automation for job fetching

### Notifications (Future)
- **python-telegram-bot**: Telegram bot API
- **smtplib**: Email notifications

## 🔄 Data Flow Architecture

### Job Fetching Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │    │   Job Fetcher   │    │   Job Board     │
│   (APScheduler) │──►│   (Service)     │──►│   (API/Web)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │   AI Service    │    │   Raw Job Data  │
                        │   (Matcher)     │◄───┤   (Structured) │
                        └─────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │   Database      │
                        │   (SQLite)      │
                        └─────────────────┘
```

### User Interaction Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Database      │
│   Dashboard     │◄──►│   Backend       │◄──►│   Layer         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │   Business      │    │   Data Models   │
│   - Metrics     │    │   Logic         │    │   - Jobs        │
│   - Tables      │    │   - Services    │    │   - Applications│
│   - Forms       │    │   - Validation  │    │   - Users       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Design Patterns

### 1. Repository Pattern
- **Purpose**: Abstract database operations
- **Implementation**: Service layer uses repositories to access data
- **Benefits**: Testability, separation of concerns

### 2. Dependency Injection
- **Purpose**: Loose coupling between components
- **Implementation**: FastAPI's dependency system
- **Benefits**: Easier testing, better modularity

### 3. Factory Pattern
- **Purpose**: Create different types of job fetchers
- **Implementation**: Fetcher factory based on job board type
- **Benefits**: Extensibility, maintainability

### 4. Observer Pattern
- **Purpose**: Notify users of job updates
- **Implementation**: Notification service observers
- **Benefits**: Decoupled notification system

### 5. Strategy Pattern
- **Purpose**: Different AI matching algorithms
- **Implementation**: Pluggable matching strategies
- **Benefits**: Flexibility in AI approaches

## 🔐 Security Considerations

### Data Privacy
- Local-first approach minimizes data exposure
- No cloud storage of personal information
- Configurable data retention policies

### API Security
- CORS configuration for frontend access
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy

### Environment Security
- Environment variables for sensitive data
- No hardcoded credentials
- Secure key management practices

## 🚀 Performance Considerations

### Database Optimization
- Indexed queries for common operations
- Connection pooling with SQLAlchemy
- Efficient query patterns

### Async Operations
- Non-blocking I/O for HTTP requests
- Concurrent job fetching
- Background task processing

### Caching Strategy
- In-memory caching for frequently accessed data
- API response caching where appropriate
- Database query result caching

## 📊 Monitoring & Observability

### Logging
- Structured logging with loguru
- Log levels for different environments
- File rotation and compression

### Health Checks
- `/health` endpoint for API status
- Database connectivity checks
- External service availability

### Metrics (Future)
- Job fetching success rates
- API response times
- User engagement metrics

## 🔄 Deployment Architecture

### Development
- SQLite database
- Local file storage
- Development configuration

### Production
- PostgreSQL database
- Containerized deployment
- Production configuration
- Load balancing (if needed)

## 🧪 Testing Strategy

### Unit Tests
- Service layer testing
- Model validation testing
- Utility function testing

### Integration Tests
- API endpoint testing
- Database integration testing
- External service mocking

### End-to-End Tests
- Full workflow testing
- UI interaction testing
- Performance testing

## 📈 Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Database connection pooling
- Load balancer ready

### Vertical Scaling
- Async processing capabilities
- Efficient resource usage
- Memory optimization

### Data Growth
- Database partitioning strategy
- Archive policies for old data
- Backup and recovery procedures

## 🇮🇳 India Source Expansion (v0.5-stable-india-foundation)

### New India Fetchers Architecture
- **BaseIndiaFetcher**: Common base class for all India job sources
- **InstahyreFetcher**: Async HTTP + BeautifulSoup implementation
- **CutshortFetcher**: Enhanced parsing with robust selectors
- **NaukriFetcher**: Lightweight implementation with proper headers
- **IndiaFetchUtils**: Shared utilities for URL validation, location normalization
- **SourceHealthTracker**: Health monitoring and performance metrics

### Enhanced PM Filtering
- Strict PM role validation (Product Manager, Associate PM, Technical PM, etc.)
- Reject non-PM roles (Sales, QA, Recruiter, Support, etc.)
- India-specific location normalization (Bangalore, Hyderabad, Pune, etc.)
- Salary parsing for LPA format and ranges
- Domain tag extraction (SaaS, FinTech, Healthcare, etc.)

### Integration Improvements
- Seamless integration into existing orchestrator
- Maintained async stability with httpx.AsyncClient
- Preserved existing Greenhouse/Lever flow
- Added proper error handling and retry logic
- Enhanced logging with structured context

### Production Enhancements
- User-Agent headers for better compatibility
- HTTP transport with retries
- SSL verification options
- Debug file generation for troubleshooting
- Git ignore for temporary debug files

## 🔮 Future Enhancements

### AI/ML Features
- Custom job recommendation models
- Resume optimization suggestions
- Interview preparation tools
- Salary negotiation insights

### Integration Features
- LinkedIn API integration
- Calendar integration
- Email client integration
- ATS (Applicant Tracking System) integration

### Advanced Features
- Multi-user support
- Team collaboration
- Advanced analytics
- Mobile application

---

## 📝 Architecture Updates

This document will be updated as the system evolves. Key changes will be tracked in this section.

### Version History
- **v0.1.0** (2026-05-06): Initial architecture foundation
  - Basic project structure
  - Core configuration and logging
  - Database setup with SQLAlchemy
  - FastAPI and Streamlit foundations
  - Placeholder for future features

- **v0.5-stable-india-foundation** (2026-05-09): India source expansion
  - Complete India fetcher architecture with BaseIndiaFetcher
  - Instahyre, Cutshort, Naukri integration
  - Enhanced PM filtering and India location normalization
  - Source health tracking and utilities
  - Production-stable async implementation
  - Seamless orchestrator integration
  - Enhanced error handling and logging

---

*Last Updated: May 9, 2026*
