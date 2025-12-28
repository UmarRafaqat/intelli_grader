from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from contextlib import asynccontextmanager
import os
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import local modules
from models import QuestionConfig, GroundTruthCreate, SubmissionCreate, GradeEdit
from database import Database
from ai_grading_engine import AIGradingEngine
from ocr_service import EnhancedOCRService
from validators import SubmissionValidator, GradingValidator, ValidationError
from batch_processor import BatchProcessor

# Global instances
db = None
grading_engine = None
ocr_service = None
batch_processor = None

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def initialize_services():
    """Initialize services with API key and database"""
    global grading_engine, ocr_service, db, batch_processor
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\nWARNING: OPENAI_API_KEY not set!")
        print("AI grading and OCR features will not work.")
        print("Please add your OpenAI API key to backend/.env file:")
        print("OPENAI_API_KEY=your-key-here\n")
    
    # Initialize database
    try:
        db = Database()
        if db.is_connected():
            print("Database connected successfully")
        else:
            print("Database connection failed")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        db = None
    
    # Initialize AI services
    if api_key:
        try:
            grading_engine = AIGradingEngine(api_key)
            ocr_service = EnhancedOCRService(api_key)
            print("AI services initialized successfully")
        except Exception as e:
            print(f"AI services initialization error: {str(e)}")
            grading_engine = None
            ocr_service = None
    else:
        grading_engine = None
        ocr_service = None
    
    # Initialize batch processor
    try:
        batch_processor = BatchProcessor()
        print("Batch processor initialized successfully")
    except Exception as e:
        print(f"Batch processor initialization error: {str(e)}")
        batch_processor = None
    
    print("\nSERVICE STATUS:")
    print(f"  Database: {'Active' if db and db.is_connected() else 'Inactive'}")
    print(f"  AI Grading: {'Active' if grading_engine else 'Inactive'}")
    print(f"  OCR Service: {'Active' if ocr_service else 'Inactive'}")
    print(f"  Batch Processor: {'Active' if batch_processor else 'Inactive'}\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\nStarting AI Grading System...")
    initialize_services()
    yield
    print("\nShutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Grading System",
    version="2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ENDPOINTS

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "AI Grading System is running",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "grading_engine": "active" if grading_engine else "inactive",
            "ocr_service": "active" if ocr_service else "inactive",
            "database": "active" if (db and db.is_connected()) else "inactive"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/auto-configure")
async def auto_configure(
    exam_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Auto-configure questions from images using GPT-4 Vision"""
    if not ocr_service:
        raise HTTPException(
            status_code=503, 
            detail="OCR service not available. Please configure OPENAI_API_KEY in backend/.env file."
        )
    
    try:
        file_paths = []
        for file in files:
            file_path = UPLOAD_DIR / f"temp_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(str(file_path))
        
        # Extract ground truth with auto-config
        questions_dict = ocr_service.extract_ground_truth(file_paths)
        
        # Cleanup temp files
        for path in file_paths:
            try:
                os.remove(path)
            except:
                pass
        
        return {
            "success": True,
            "questions": questions_dict,
            "exam_name": exam_name
        }
    except Exception as e:
        print(f"Auto-configure error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-configure failed: {str(e)}")


@app.post("/api/upload-ground-truth")
async def upload_ground_truth(
    exam_name: str = Form(...),
    questions: str = Form(...),
    total_marks: str = Form(...)
):
    """Upload ground truth (answer key)"""
    try:
        questions_dict = json.loads(questions)
        total_marks_float = float(total_marks)
        
        # Validate ground truth
        validation_result = SubmissionValidator.validate_ground_truth(questions_dict, total_marks_float)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Ground truth validation failed",
                    "warnings": validation_result["warnings"]
                }
            )
        
        # Store in database
        exam_id = db.add_ground_truth(exam_name, questions_dict, total_marks_float)
        
        response = {
            "success": True,
            "exam_id": exam_id,
            "exam_name": exam_name,
            "total_marks": total_marks_float,
            "questions_count": len(questions_dict)
        }
        
        if validation_result["warnings"]:
            response["warnings"] = validation_result["warnings"]
        
        return response
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration format: {str(e)}")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        print(f"Error uploading ground truth: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exams")
async def get_exams():
    """Get all exams with submission counts"""
    try:
        exams = db.get_all_ground_truths()
        return [
            {
                "id": exam.id,
                "exam_name": exam.exam_name,
                "total_marks": exam.total_marks,
                "questions_count": len(exam.questions),
                "upload_time": exam.upload_time.isoformat(),
                "submissions_count": db.count_submissions_for_exam(exam.id)
            }
            for exam in exams
        ]
    except Exception as e:
        print(f"Error getting exams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-student-papers")
async def upload_student_papers(
    exam_id: int = Form(...),
    student_id: str = Form(...),
    files: List[UploadFile] = File(...),
    allow_duplicate: bool = Form(False)
):
    """Upload student papers"""
    try:
        # Verify exam exists
        ground_truth = db.get_ground_truth(exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Check for duplicate submission
        existing_submission = SubmissionValidator.check_duplicate_submission(db, student_id, exam_id)
        if existing_submission and not allow_duplicate:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Student {student_id} already submitted for this exam",
                    "existing_submission": existing_submission,
                    "hint": "Set allow_duplicate=true to override"
                }
            )
        
        # Save files
        file_paths = []
        for file in files:
            file_path = UPLOAD_DIR / f"student_{student_id}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(str(file_path))
        
        # Extract answers using OCR
        extracted_answers = {}
        if ocr_service:
            try:
                extracted_answers = ocr_service.extract_student_answers(file_paths)
                print(f"OCR extracted answers: {list(extracted_answers.keys())}")
            except Exception as e:
                print(f"OCR extraction failed: {str(e)}")
                extracted_answers = {}
        else:
            print("OCR service not available")
        
        # Validate extracted answers against ground truth
        validation_result = SubmissionValidator.validate_extracted_answers(
            ground_truth.questions, 
            extracted_answers
        )
        
        if not validation_result["valid"]:
            print(f"Validation warnings: {validation_result['warnings']}")
        
        # Store submission
        submission_id = db.add_submission(
            student_id=student_id,
            exam_id=exam_id,
            raw_images=file_paths,
            extracted_answers=extracted_answers
        )
        
        response = {
            "success": True,
            "submission_id": submission_id,
            "student_id": student_id,
            "exam_id": exam_id,
            "validation": validation_result,
            "message": "Paper uploaded successfully. Ready to grade."
        }
        
        if existing_submission:
            response["note"] = "This is a duplicate submission (previous submission exists)"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading student papers: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/grade-paper/{submission_id}")
async def grade_paper(submission_id: int):
    """Grade a student paper"""
    try:
        # Check if grading engine is available
        if not grading_engine:
            raise HTTPException(
                status_code=503,
                detail="AI grading service not available. Please configure OPENAI_API_KEY in backend/.env"
            )
        
        # Get submission
        submission = db.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get ground truth
        ground_truth = db.get_ground_truth(submission.exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Ground truth not found")
        
        # Validate extracted answers before grading
        validation_result = SubmissionValidator.validate_extracted_answers(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        # Get unanswered questions
        unanswered = SubmissionValidator.get_unanswered_questions(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        # Grade submission
        results = grading_engine.grade_submission(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        # Validate grading results
        grading_validation = GradingValidator.validate_grading_results(
            results,
            ground_truth.questions
        )
        
        # Store results
        db.add_results(submission_id, results)
        
        # Calculate totals
        total_score = sum(r["score"] for r in results)
        total_max = sum(r["max_score"] for r in results)
        percentage = round((total_score / total_max * 100), 2) if total_max > 0 else 0
        
        response = {
            "success": True,
            "submission_id": submission_id,
            "total_score": round(total_score, 2),
            "total_max": total_max,
            "percentage": percentage,
            "results": results,
            "validation": {
                "extraction": validation_result,
                "grading": grading_validation,
                "unanswered_questions": unanswered
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        print(f"Error grading paper: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/{submission_id_or_student_id}")
async def get_results(submission_id_or_student_id: str):
    """Get results by submission ID or student ID"""
    try:
        submission = None
        
        # Try as submission ID first
        if submission_id_or_student_id.isdigit():
            submission_id = int(submission_id_or_student_id)
            submission = db.get_submission(submission_id)
        
        # Try as student ID
        if not submission:
            submission = db.get_submission_by_student_id(submission_id_or_student_id)
        
        if not submission:
            raise HTTPException(
                status_code=404, 
                detail=f"No submission found for ID: {submission_id_or_student_id}"
            )
        
        # Get results
        results = db.get_results(submission.id)
        if not results:
            raise HTTPException(
                status_code=404, 
                detail="Submission found but not graded yet. Please grade the paper first."
            )
        
        # Calculate totals
        total_score = sum(r["score"] for r in results)
        total_max = sum(r["max_score"] for r in results)
        percentage = round((total_score / total_max * 100), 2) if total_max > 0 else 0
        
        return {
            "submission_id": submission.id,
            "student_id": submission.student_id,
            "exam_id": submission.exam_id,
            "total_score": round(total_score, 2),
            "total_max": total_max,
            "percentage": percentage,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting results: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validate-submission/{submission_id}")
async def validate_submission(submission_id: int):
    """Get validation status for a submission"""
    try:
        submission = db.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        ground_truth = db.get_ground_truth(submission.exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Ground truth not found")
        
        validation_result = SubmissionValidator.validate_extracted_answers(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        unanswered = SubmissionValidator.get_unanswered_questions(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        all_answered = SubmissionValidator.validate_all_questions_answered(
            ground_truth.questions,
            submission.extracted_answers
        )
        
        return {
            "submission_id": submission_id,
            "student_id": submission.student_id,
            "exam_id": submission.exam_id,
            "validation": validation_result,
            "unanswered_questions": unanswered,
            "all_questions_answered": all_answered,
            "ready_for_grading": validation_result["valid"] and all_answered
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error validating submission: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/review/{submission_id_or_student_id}")
async def get_review(submission_id_or_student_id: str):
    """Get detailed review for teacher"""
    try:
        submission = None
        
        # Try as submission ID first
        if submission_id_or_student_id.isdigit():
            submission_id = int(submission_id_or_student_id)
            submission = db.get_submission(submission_id)
        
        # Try as student ID
        if not submission:
            submission = db.get_submission_by_student_id(submission_id_or_student_id)
        
        if not submission:
            raise HTTPException(
                status_code=404, 
                detail=f"No submission found for ID: {submission_id_or_student_id}"
            )
        
        ground_truth = db.get_ground_truth(submission.exam_id)
        results = db.get_results(submission.id)
        edits = db.get_grade_edits(submission.id)
        
        # Apply grade edits to results
        if results and edits:
            edits_dict = {e["question_id"]: e for e in edits}
            for result in results:
                if result["question_id"] in edits_dict:
                    edit = edits_dict[result["question_id"]]
                    result["score"] = edit["edited_score"]
                    result["teacher_comment"] = edit["teacher_comment"]
        
        return {
            "submission": {
                "id": submission.id,
                "student_id": submission.student_id,
                "exam_id": submission.exam_id,
                "submission_time": submission.submission_time.isoformat()
            },
            "ground_truth": {
                "exam_name": ground_truth.exam_name,
                "total_marks": ground_truth.total_marks
            },
            "results": results or [],
            "edits": edits
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting review: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/edit-grade/{submission_id}/{question_id}")
async def edit_grade(
    submission_id: int,
    question_id: str,
    new_score: float = Form(...),
    teacher_comment: str = Form("")
):
    """Edit a grade"""
    try:
        # Get current results
        results = db.get_results(submission_id)
        if not results:
            raise HTTPException(status_code=404, detail="Results not found")
        
        # Find the question result
        original_score = None
        max_score = None
        for result in results:
            if result["question_id"] == question_id:
                original_score = result["score"]
                max_score = result["max_score"]
                break
        
        if original_score is None:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Validate new score
        try:
            GradingValidator.validate_score(new_score, max_score, question_id)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.message)
        
        # Create edit record
        edit = {
            "submission_id": submission_id,
            "question_id": question_id,
            "original_score": original_score,
            "edited_score": new_score,
            "teacher_comment": teacher_comment,
            "edited_at": datetime.now()
        }
        
        # Add edit
        db.add_grade_edit(edit)
        
        # Update the result in database
        for i, result in enumerate(results):
            if result["question_id"] == question_id:
                results[i]["score"] = new_score
                if teacher_comment:
                    results[i]["teacher_comment"] = teacher_comment
                break
        
        db.update_results(submission_id, results)
        
        return {
            "success": True,
            "message": "Grade updated successfully",
            "original_score": original_score,
            "new_score": new_score
        }
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        print(f"Error editing grade: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# BATCH PROCESSING ENDPOINTS

@app.post("/api/upload-batch-papers")
async def upload_batch_papers(
    exam_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload ZIP file containing multiple student papers"""
    try:
        # Verify services are available
        if not batch_processor:
            raise HTTPException(status_code=503, detail="Batch processor not available")
        
        if not ocr_service:
            raise HTTPException(status_code=503, detail="OCR service not available")
        
        # Verify exam exists
        ground_truth = db.get_ground_truth(exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Validate file is ZIP
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Save ZIP file
        zip_path = UPLOAD_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create batch job
        batch_id = db.create_batch_job(
            exam_id=exam_id,
            exam_name=ground_truth.exam_name,
            total_students=0  # Will update after extraction
        )
        
        # Extract ZIP
        try:
            extract_path = batch_processor.extract_zip(str(zip_path), batch_id)
        except ValueError as e:
            db.update_batch_job(batch_id, status="failed", error_message=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        
        # Group files by student
        student_papers = batch_processor.group_files_by_student(extract_path)
        
        # Validate structure
        is_valid, warnings = batch_processor.validate_batch_structure(student_papers)
        if not is_valid:
            db.update_batch_job(batch_id, status="failed", error_message="; ".join(warnings))
            raise HTTPException(status_code=400, detail={"message": "Invalid batch structure", "warnings": warnings})
        
        # Update batch job with actual student count
        db.update_batch_job(batch_id, total_students=len(student_papers))
        
        # Create batch submission records for each student
        batch_sub_ids = {}
        for student_id in student_papers.keys():
            batch_sub_id = db.add_batch_submission(batch_id, student_id)
            batch_sub_ids[student_id] = batch_sub_id
        
        # Process each student: OCR extraction and create submission
        for student_id, image_paths in student_papers.items():
            batch_sub_id = batch_sub_ids[student_id]
            
            try:
                # Extract answers using OCR
                extracted_answers = ocr_service.extract_student_answers(image_paths)
                
                # Validate extracted answers
                validation_result = SubmissionValidator.validate_extracted_answers(
                    ground_truth.questions,
                    extracted_answers
                )
                
                # Create submission
                submission_id = db.add_submission(
                    student_id=student_id,
                    exam_id=exam_id,
                    raw_images=image_paths,
                    extracted_answers=extracted_answers
                )
                
                # Update batch submission
                db.update_batch_submission(
                    batch_sub_id,
                    submission_id=submission_id,
                    status="uploaded",
                    processed_at=datetime.now()
                )
                
                print(f"Processed student {student_id}: submission_id={submission_id}")
                
            except Exception as e:
                error_msg = f"OCR/Upload failed: {str(e)}"
                db.update_batch_submission(
                    batch_sub_id,
                    status="failed",
                    error_message=error_msg,
                    processed_at=datetime.now()
                )
                print(f"Failed to process student {student_id}: {error_msg}")
        
        # Update batch job status
        batch_subs = db.get_batch_submissions(batch_id)
        successful = sum(1 for bs in batch_subs if bs.status == "uploaded")
        failed = sum(1 for bs in batch_subs if bs.status == "failed")
        
        db.update_batch_job(
            batch_id,
            processed_students=len(batch_subs),
            successful_students=successful,
            failed_students=failed,
            status="uploaded"
        )
        
        # Cleanup ZIP file
        try:
            os.remove(zip_path)
        except:
            pass
        
        response = {
            "success": True,
            "batch_id": batch_id,
            "total_students": len(student_papers),
            "uploaded": successful,
            "failed": failed,
            "message": f"Batch uploaded: {successful} students ready for grading"
        }
        
        if warnings:
            response["warnings"] = warnings
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading batch: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/grade-batch/{batch_id}")
async def grade_batch(batch_id: int):
    """Grade all submissions in a batch"""
    try:
        # Verify grading engine is available
        if not grading_engine:
            raise HTTPException(
                status_code=503,
                detail="AI grading service not available"
            )
        
        # Get batch job
        batch_job = db.get_batch_job(batch_id)
        if not batch_job:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        if batch_job.status not in ["uploaded", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Batch cannot be graded. Current status: {batch_job.status}"
            )
        
        # Get ground truth
        ground_truth = db.get_ground_truth(batch_job.exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Ground truth not found")
        
        # Update batch status to processing
        db.update_batch_job(batch_id, status="processing")
        
        # Get all batch submissions
        batch_subs = db.get_batch_submissions(batch_id)
        
        grading_results = []
        successful_count = 0
        failed_count = 0
        
        # Grade each submission
        for batch_sub in batch_subs:
            # Skip already failed submissions
            if batch_sub.status == "failed":
                failed_count += 1
                grading_results.append({
                    "student_id": batch_sub.student_id,
                    "status": "failed",
                    "error_message": batch_sub.error_message or "Upload failed"
                })
                continue
            
            try:
                # Get submission
                submission = db.get_submission(batch_sub.submission_id)
                if not submission:
                    raise ValueError("Submission not found")
                
                # Grade submission
                results = grading_engine.grade_submission(
                    ground_truth.questions,
                    submission.extracted_answers
                )
                
                # Validate grading results
                grading_validation = GradingValidator.validate_grading_results(
                    results,
                    ground_truth.questions
                )
                
                if not grading_validation["valid"]:
                    raise ValueError(f"Grading validation failed: {grading_validation['warnings']}")
                
                # Store results
                db.add_results(batch_sub.submission_id, results)
                
                # Calculate total score
                total_score = sum(r["score"] for r in results)
                
                # Update batch submission
                db.update_batch_submission(
                    batch_sub.id,
                    status="completed",
                    total_score=total_score,
                    processed_at=datetime.now()
                )
                
                successful_count += 1
                grading_results.append({
                    "student_id": batch_sub.student_id,
                    "submission_id": batch_sub.submission_id,
                    "status": "completed",
                    "total_score": round(total_score, 2)
                })
                
                print(f"Graded student {batch_sub.student_id}: {total_score}/{ground_truth.total_marks}")
                
            except Exception as e:
                error_msg = f"Grading failed: {str(e)}"
                db.update_batch_submission(
                    batch_sub.id,
                    status="failed",
                    error_message=error_msg,
                    processed_at=datetime.now()
                )
                
                failed_count += 1
                grading_results.append({
                    "student_id": batch_sub.student_id,
                    "status": "failed",
                    "error_message": error_msg
                })
                
                print(f"Failed to grade student {batch_sub.student_id}: {error_msg}")
        
        # Update batch job
        db.update_batch_job(
            batch_id,
            status="completed",
            successful_students=successful_count,
            failed_students=failed_count,
            completed_at=datetime.now()
        )
        
        # Generate report
        report = batch_processor.generate_batch_report(grading_results)
        
        # Cleanup batch files
        batch_processor.cleanup_batch(batch_id)
        
        return {
            "success": True,
            "batch_id": batch_id,
            "report": report,
            "results": grading_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error grading batch: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update batch status to failed
        try:
            db.update_batch_job(batch_id, status="failed", error_message=str(e))
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batch-status/{batch_id}")
async def get_batch_status(batch_id: int):
    """Get batch processing status"""
    try:
        batch_job = db.get_batch_job(batch_id)
        if not batch_job:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        batch_subs = db.get_batch_submissions(batch_id)
        
        return {
            "batch_id": batch_id,
            "exam_id": batch_job.exam_id,
            "exam_name": batch_job.exam_name,
            "status": batch_job.status,
            "total_students": batch_job.total_students,
            "processed_students": batch_job.processed_students,
            "successful_students": batch_job.successful_students,
            "failed_students": batch_job.failed_students,
            "created_at": batch_job.created_at.isoformat(),
            "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None,
            "error_message": batch_job.error_message,
            "submissions": [
                {
                    "student_id": bs.student_id,
                    "submission_id": bs.submission_id,
                    "status": bs.status,
                    "total_score": bs.total_score,
                    "error_message": bs.error_message
                }
                for bs in batch_subs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting batch status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batch-results/{batch_id}/csv")
async def export_batch_results_csv(batch_id: int):
    """Export batch results as CSV"""
    try:
        batch_job = db.get_batch_job(batch_id)
        if not batch_job:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        if batch_job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Batch not completed yet. Current status: {batch_job.status}"
            )
        
        # Get ground truth for total marks
        ground_truth = db.get_ground_truth(batch_job.exam_id)
        if not ground_truth:
            raise HTTPException(status_code=404, detail="Ground truth not found")
        
        # Get batch submissions
        batch_subs = db.get_batch_submissions(batch_id)
        
        # Prepare results for CSV
        results_data = []
        for bs in batch_subs:
            results_data.append({
                "student_id": bs.student_id,
                "submission_id": bs.submission_id,
                "status": bs.status,
                "total_score": bs.total_score,
                "error_message": bs.error_message
            })
        
        # Generate CSV
        csv_content = batch_processor.export_to_csv(
            results_data,
            batch_job.exam_name,
            ground_truth.total_marks
        )
        
        # Return as downloadable file
        from fastapi.responses import Response
        
        filename = f"batch_{batch_id}_{batch_job.exam_name.replace(' ', '_')}_results.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting batch results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batches")
async def get_all_batches():
    """Get all batch jobs"""
    try:
        batch_jobs = db.get_all_batch_jobs()
        
        return [
            {
                "id": bj.id,
                "exam_id": bj.exam_id,
                "exam_name": bj.exam_name,
                "total_students": bj.total_students,
                "successful_students": bj.successful_students,
                "failed_students": bj.failed_students,
                "status": bj.status,
                "created_at": bj.created_at.isoformat(),
                "completed_at": bj.completed_at.isoformat() if bj.completed_at else None
            }
            for bj in batch_jobs
        ]
    except Exception as e:
        print(f"Error getting batches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    import uvicorn
    print("\nStarting AI Grading System...")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)