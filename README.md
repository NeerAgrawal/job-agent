# Job AI Agent

A local-first AI-powered Product Manager job acquisition system built with Python, FastAPI, and Streamlit.

## 🚀 Features

- **Local-first Architecture**: All data stored locally with SQLite
- **AI-Powered Job Matching**: Intelligent job filtering and ranking
- **Automated Job Fetching**: Scheduled fetching from multiple job boards
- **Web Dashboard**: Beautiful Streamlit interface for monitoring
- **REST API**: FastAPI backend for programmatic access
- **Async-Ready**: Full async/await support throughout
- **Extensible**: Modular design for easy feature additions

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Streamlit
- **Database**: SQLite (with PostgreSQL support ready)
- **AI**: OpenAI API integration
- **HTTP Client**: httpx for async requests
- **Logging**: loguru for structured logging
- **Future Support**: Playwright (web scraping), Telegram Bot API

## 📋 Prerequisites

- Python 3.11+
- Git

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job_ai_agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
   ```

6. **Start the applications**
   
   **Option 1: Use startup scripts**
   ```bash
   # Start API server
   scripts/start_api.bat
   
   # Start Streamlit app (in separate terminal)
   scripts/start_streamlit.bat
   ```
   
   **Option 2: Manual startup**
   ```bash
   # Start API server
   python -m app.main
   
   # Start Streamlit app (in separate terminal)
   streamlit run app/web/app.py
   ```

7. **Access the applications**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Streamlit Dashboard: http://localhost:8501

## 📁 Project Structure

```
job_ai_agent/
├── app/
│   ├── api/                    # FastAPI routes and dependencies
│   │   ├── v1/                # API version 1 routes
│   │   └── dependencies/       # FastAPI dependencies
│   ├── core/                   # Core application logic
│   │   ├── config/           # Configuration management
│   │   ├── database/         # Database setup and connection
│   │   └── logging/          # Logging configuration
│   ├── models/                 # Data models and schemas
│   │   ├── entities/         # SQLAlchemy models
│   │   └── schemas/          # Pydantic schemas
│   ├── services/              # Business logic services
│   │   ├── fetchers/         # Job board fetchers
│   │   ├── ai/               # AI processing services
│   │   └── notifications/    # Notification services
│   ├── web/                   # Streamlit web interface
│   │   ├── pages/            # Streamlit pages
│   │   └── components/       # Reusable components
│   ├── utils/                 # Utility functions
│   └── main.py               # FastAPI application entry point
├── scripts/                   # Startup and utility scripts
├── tests/                     # Test files
├── logs/                      # Application logs
├── data/                      # Database files
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## ⚙️ Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

### Core Settings
- `APP_NAME`: Application name
- `DEBUG`: Enable debug mode
- `ENVIRONMENT`: Environment (development/production)

### Database
- `DATABASE_URL`: Database connection string

### API Settings
- `API_HOST`: API server host
- `API_PORT`: API server port

### AI Configuration
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `AI_MODEL`: OpenAI model to use

### Scheduler
- `SCHEDULER_ENABLED`: Enable job fetching scheduler
- `FETCH_INTERVAL_HOURS`: Job fetching interval
- `MAX_JOBS_PER_RUN`: Maximum jobs to fetch per run

## 🔧 Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

## 🚀 Deployment

### Docker (Future)
```bash
docker build -t job-ai-agent .
docker run -p 8000:8000 -p 8501:8501 job-ai-agent
```

### Production Considerations
- Use PostgreSQL instead of SQLite for production
- Configure proper CORS origins
- Set up SSL certificates
- Use environment-specific configuration
- Set up proper logging and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🔮 Roadmap

- [ ] Job board fetchers (LinkedIn, Indeed, Glassdoor)
- [ ] AI-powered job matching and ranking
- [ ] Automated application submissions
- [ ] Interview scheduling integration
- [ ] Telegram bot notifications
- [ ] Advanced analytics and reporting
- [ ] Resume optimization suggestions
- [ ] Company research automation

## 🆘 Support

For issues and questions:
1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include logs and configuration details

---

**Built with ❤️ for PMs seeking their next opportunity**
