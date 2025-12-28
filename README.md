# IntelliGrader - AI-Powered Exam Grading System

An intelligent exam grading system that uses GPT-4o for automated assessment across multiple question types, with batch processing capabilities for entire classes.

## 🚀 Features

- **AI-Powered Grading**: Uses GPT-4o for intelligent assessment with detailed reasoning
- **6 Question Types**: MCQ, Fill-in-Blank, Descriptive, Ordering, Programming, Mathematical
- **OCR Extraction**: GPT-4 Vision for extracting answers from scanned papers
- **Batch Processing**: Upload and grade entire classes at once via ZIP files
- **Multi-Page Support**: Each student can have multiple answer sheet images
- **Teacher Review**: Review and override AI grading decisions
- **CSV Export**: Export batch results for analysis
- **REST API**: Complete FastAPI backend with documentation
- **Modern Frontend**: React-based user interface

## 🏗️ Architecture

- **Backend**: Python FastAPI with PostgreSQL database
- **Frontend**: React 18 with Vite
- **AI Services**: OpenAI GPT-4o and GPT-4 Vision
- **Deployment**: Docker/Podman containers
- **Database**: PostgreSQL 16

## 📋 Prerequisites

- **Podman Desktop** or Docker Desktop
- **Python 3.11+** (for podman-compose)
- **OpenAI API Key** with GPT-4o access
- **8GB RAM** (16GB recommended)
- **10GB disk space**

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/intelligrader.git
cd intelligrader
```

### 2. Configure API Key
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env and add your OpenAI API key
OPENAI_API_KEY=your-actual-api-key-here
```

### 3. Start Services
```bash
# Using Podman (recommended)
podman-compose up -d

# Or using Docker
docker-compose up -d
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 Installation

### Windows Setup
For detailed Windows installation instructions, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

Or run the automated setup:
```powershell
.\setup-windows.bat
```

### Manual Installation

#### Install Podman Desktop
```bash
# Windows (using winget)
winget install -e --id RedHat.Podman-Desktop

# macOS (using Homebrew)
brew install podman-desktop

# Linux - see https://podman-desktop.io/downloads
```

#### Install podman-compose
```bash
pip install podman-compose
```

#### Initialize Podman Machine
```bash
podman machine init
podman machine start
```

## 📚 Usage

### Single Student Workflow
1. **Upload Answer Key**: Configure questions and grading criteria
2. **Upload Student Paper**: Submit answer sheets for individual student
3. **Grade Paper**: AI processes and grades the submission
4. **Review Results**: View detailed grading with AI reasoning
5. **Teacher Review**: Edit grades and add comments if needed

### Batch Processing Workflow
1. **Prepare ZIP File**: Create folders for each student with their answer sheets
   ```
   class_papers.zip
   ├── STUDENT001/
   │   ├── page1.jpg
   │   └── page2.jpg
   └── STUDENT002/
       └── page1.jpg
   ```
2. **Upload Batch**: Use "Batch Upload" feature
3. **Grade All**: Process entire class automatically
4. **Export Results**: Download CSV with all student scores

For detailed batch processing guide, see [BATCH_QUICK_START.md](BATCH_QUICK_START.md)

## 🎯 Question Types & Grading

### MCQ (Multiple Choice)
- Exact match with correct option
- Clear reasoning for selection

### Fill-in-the-Blank
- Semantic similarity matching
- Handles synonyms and minor variations

### Descriptive/Essay
- **Concept Coverage** (40%): Required concepts present
- **Accuracy** (30%): Factual correctness
- **Completeness** (20%): Thoroughness of explanation
- **Clarity** (10%): Organization and presentation

### Ordering/Sequence
- Position-by-position comparison
- Partial credit: (correct_positions / total) × max_marks

### Programming
- **Correctness** (50%): Logic and output validation
- **Logic** (20%): Algorithm soundness
- **Code Quality** (15%): Readability and conventions
- **Efficiency** (15%): Time/space complexity

### Mathematical
- **Final Answer** (40%): Correctness of result
- **Method** (30%): Approach used
- **Steps** (20%): Intermediate calculations
- **Notation** (10%): Mathematical symbols and format

## 🔌 API Endpoints

### Ground Truth Management
- `POST /api/upload-ground-truth` - Upload answer key
- `POST /api/auto-configure` - Auto-extract from images
- `GET /api/exams` - List all exams

### Student Submissions
- `POST /api/upload-student-papers` - Single student upload
- `POST /api/grade-paper/{id}` - Grade individual paper

### Batch Processing
- `POST /api/upload-batch-papers` - Upload ZIP with multiple students
- `POST /api/grade-batch/{id}` - Grade entire batch
- `GET /api/batch-status/{id}` - Check batch progress
- `GET /api/batch-results/{id}/csv` - Export results
- `GET /api/batches` - List all batches

### Results & Review
- `GET /api/results/{id}` - Get grading results
- `GET /api/review/{id}` - Teacher review interface
- `PUT /api/edit-grade/{sub_id}/{q_id}` - Edit individual grades

## 💾 Database Schema

### Core Tables
- **ground_truths**: Exam configurations and answer keys
- **submissions**: Student paper submissions with extracted answers
- **results**: Individual question grading results
- **grade_edits**: Teacher modifications to AI grades

### Batch Processing Tables
- **batch_jobs**: Batch processing job tracking
- **batch_submissions**: Individual student status within batches

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Performance & Costs

### Processing Time
- **OCR**: ~2-5 seconds per page
- **Grading**: ~1-3 seconds per question
- **Batch (30 students, 3 pages, 10 questions)**: ~15 minutes

### OpenAI API Costs (Approximate)
- **OCR (GPT-4 Vision)**: $0.01 per page
- **Grading (GPT-4o)**: $0.005 per question
- **Total per student** (10 questions, 3 pages): ~$0.08

## 🔒 Security & Production

### Security Considerations
- Never commit `.env` files with real API keys
- Change default database passwords in production
- Use HTTPS in production environments
- Implement authentication for production use
- Regular database backups recommended

### Production Deployment
1. Use environment-specific `.env` files
2. Set up SSL/TLS certificates
3. Configure proper firewall rules
4. Set up monitoring and logging
5. Implement backup strategies

## 🚨 Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check Podman machine status
podman machine list
podman machine start

# Check container logs
podman-compose logs
```

**Database connection failed**
```bash
# Restart database
podman restart grading_db
sleep 10
podman restart grading_backend
```

**API key errors**
- Verify key is set in `backend/.env`
- Check key has GPT-4o access
- Monitor API usage limits

For detailed troubleshooting, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

## 📖 Documentation

- [WINDOWS_SETUP.md](WINDOWS_SETUP.md) - Windows installation guide
- [BATCH_QUICK_START.md](BATCH_QUICK_START.md) - 5-minute batch processing guide
- [BATCH_PROCESSING.md](BATCH_PROCESSING.md) - Comprehensive batch documentation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command reference and troubleshooting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o and GPT-4 Vision APIs
- FastAPI for the excellent Python web framework
- React team for the frontend framework
- PostgreSQL for reliable database management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/intelligrader/issues)
- **Documentation**: Check the docs folder
- **API Reference**: http://localhost:8000/docs (when running)

---

**Made with ❤️ for educators and students worldwide**

## Project Structure

```
ai-grading-system/
├── backend/                    # Python FastAPI backend
│   ├── ai_grading_engine.py   # AI grading logic
│   ├── main.py                # FastAPI application
│   ├── database.py            # PostgreSQL operations
│   ├── models.py              # Pydantic models
│   ├── ocr_service.py         # OCR with GPT-4 Vision
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── .env                   # Environment variables
├── frontend/                   # React frontend (optional)
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   └── styles/            # CSS files
│   ├── Dockerfile
│   └── package.json
├── podman-compose.yml         # Container orchestration
├── test_system.py             # Automated tests
└── README.md                  # This file
```

## Question Types and Grading

### 1. MCQ (Multiple Choice)
AI compares student's answer with correct option. Reasoning explains whether the selected option matches and why.

### 2. Fill-in-the-Blank
AI checks semantic similarity with acceptable answers, considering synonyms and minor spelling variations. Reasoning shows which answer matched.

### 3. Descriptive/Essay
AI grades on 4 criteria:
- Concept Coverage (40%): Identifies required concepts present/missing
- Accuracy (30%): Checks factual correctness
- Completeness (20%): Evaluates thoroughness
- Clarity (10%): Assesses organization

Reasoning lists found/missing concepts and explains each criterion's evaluation.

### 4. Ordering/Sequence
AI compares position-by-position with correct order. Partial credit: (correct_positions / total) x max_marks. Reasoning shows detailed sequence comparison.

### 5. Programming
AI grades on 4 criteria:
- Correctness (50%): Traces code logic, checks output
- Logic (20%): Evaluates algorithm soundness
- Code Quality (15%): Checks readability and conventions
- Efficiency (15%): Assesses time/space complexity

Reasoning includes code review, test case results, and identified bugs.

### 6. Mathematical
AI grades on 4 criteria:
- Final Answer (40%): Checks if answer is correct
- Method (30%): Evaluates approach used
- Steps (20%): Verifies intermediate steps
- Notation (10%): Checks proper mathematical symbols

Reasoning explains solution analysis and partial credit for correct method.

## API Endpoints

```
POST /api/upload-ground-truth      # Upload answer key
POST /api/upload-student-papers    # Upload student papers
POST /api/grade-paper/{id}         # Grade submission
GET  /api/results/{id}             # Get results (by submission or student ID)
GET  /api/review/{id}              # Get detailed review
PUT  /api/edit-grade/{id}/{q_id}   # Edit grade
GET  /api/exams                    # List all exams
GET  /api/health                   # Health check
```

## Example Ground Truth Format

```json
{
  "Q1": {
    "type": "mcq",
    "marks": 2,
    "question_text": "What is photosynthesis?",
    "ground_truth": {
      "correct_answer": "A"
    }
  },
  "Q2": {
    "type": "descriptive",
    "marks": 5,
    "question_text": "Explain photosynthesis.",
    "ground_truth": {
      "model_answer": "Photosynthesis is the process...",
      "key_concepts": ["light energy", "chlorophyll", "oxygen"]
    }
  },
  "Q3": {
    "type": "programming",
    "marks": 10,
    "question_text": "Write a function to reverse a string.",
    "ground_truth": {
      "expected_output": "olleh",
      "test_cases": [
        {"input": "hello", "output": "olleh"}
      ]
    }
  },
  "Q4": {
    "type": "mathematical",
    "marks": 5,
    "question_text": "Solve: 2x + 5 = 13",
    "ground_truth": {
      "correct_answer": "4",
      "solution_steps": ["2x = 8", "x = 4"]
    }
  }
}
```

## Configuration

### Environment Variables (backend/.env)

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Database (default values)
DATABASE_URL=postgresql://grading_user:grading_pass@db:5432/grading_db
POSTGRES_DB=grading_db
POSTGRES_USER=grading_user
POSTGRES_PASSWORD=grading_pass
```

## Testing

```bash
# Run automated test suite
python3 test_system.py

# Test health endpoint
curl http://localhost:8000/api/health

# Test grading
curl http://localhost:8000/api/grade-paper/1
```

## Database Operations

```bash
# Connect to database
podman exec -it grading_db psql -U grading_user -d grading_db

# Backup database
podman exec grading_db pg_dump -U grading_user grading_db > backup.sql

# Restore database
cat backup.sql | podman exec -i grading_db psql -U grading_user -d grading_db

# View logs
podman-compose logs -f backend
```

## Troubleshooting

### Backend not starting
```bash
# Check logs
podman logs grading_backend

# Verify API key is set
podman exec grading_backend env | grep OPENAI

# Restart services
podman-compose restart
```

### Database connection issues
```bash
# Check database status
podman exec grading_db pg_isready -U grading_user

# Restart database
podman restart grading_db
sleep 30
podman restart grading_backend
```

### OCR not working
- Verify OPENAI_API_KEY is set correctly
- Check API key has access to GPT-4o and GPT-4 Vision
- Review logs: `podman logs grading_backend`

## System Architecture

```
Student Paper (Images)
    |
    v
OCR Extraction (GPT-4 Vision)
    |
    v
Answer Preprocessing
    |
    v
AI Grading (GPT-4o)
    |
    v
Detailed Reasoning + Score
    |
    v
Database Storage
    |
    v
Professor Review Interface
```

## Cost Estimate

- OCR (GPT-4 Vision): approximately $0.01 per page
- Grading (GPT-4o): approximately $0.005 per question
- Total per student (10 questions, 3 pages): approximately $0.08

## Security Notes

- Change default database password in production
- Never commit .env file with real API keys
- Use HTTPS in production
- Implement authentication for production use
- Regular database backups recommended

## Development

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## License

MIT License

## Support

For issues or questions:
1. Check logs: `podman-compose logs`
2. Review API docs: http://localhost:8000/docs
3. Test health: `curl http://localhost:8000/api/health`
4. Run test suite: `python3 test_system.py`
# intelligrader
