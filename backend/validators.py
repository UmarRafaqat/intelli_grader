"""
Validation module for submission and grading data
"""
from typing import Dict, List, Any, Optional


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, details: Dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SubmissionValidator:
    """Validates student submissions against ground truth"""
    
    @staticmethod
    def validate_extracted_answers(ground_truth_questions: Dict, 
                                   extracted_answers: Dict) -> Dict[str, Any]:
        """
        Validate that extracted answers match expected questions
        Returns validation result with warnings and missing/extra questions
        """
        expected_questions = set(ground_truth_questions.keys())
        extracted_questions = set(extracted_answers.keys())
        
        missing_questions = expected_questions - extracted_questions
        extra_questions = extracted_questions - expected_questions
        
        warnings = []
        is_valid = True
        
        if missing_questions:
            is_valid = False
            warnings.append(f"Missing answers for questions: {', '.join(sorted(missing_questions))}")
        
        if extra_questions:
            warnings.append(f"Unexpected questions found: {', '.join(sorted(extra_questions))}")
        
        empty_answers = [q_id for q_id, answer in extracted_answers.items() 
                        if not answer or (isinstance(answer, str) and not answer.strip())]
        
        if empty_answers:
            warnings.append(f"Empty answers detected for: {', '.join(sorted(empty_answers))}")
        
        return {
            "valid": is_valid,
            "warnings": warnings,
            "missing_questions": sorted(list(missing_questions)),
            "extra_questions": sorted(list(extra_questions)),
            "empty_answers": sorted(empty_answers),
            "total_expected": len(expected_questions),
            "total_extracted": len(extracted_questions),
            "match_rate": len(expected_questions & extracted_questions) / len(expected_questions) if expected_questions else 0
        }
    
    @staticmethod
    def check_duplicate_submission(db, student_id: str, exam_id: int) -> Optional[Dict]:
        """
        Check if student already submitted for this exam
        Returns existing submission info if found, None otherwise
        """
        from database import Submission
        
        existing = db.session.query(Submission).filter_by(
            student_id=student_id,
            exam_id=exam_id
        ).first()
        
        if existing:
            return {
                "submission_id": existing.id,
                "student_id": existing.student_id,
                "exam_id": existing.exam_id,
                "submission_time": existing.submission_time.isoformat()
            }
        
        return None
    
    @staticmethod
    def validate_ground_truth(questions: Dict, total_marks: float) -> Dict[str, Any]:
        """
        Validate ground truth configuration
        """
        if not questions:
            raise ValidationError("Questions dictionary cannot be empty")
        
        warnings = []
        calculated_total = 0
        
        for q_id, q_config in questions.items():
            if isinstance(q_config, dict):
                marks = q_config.get("marks", 0)
            else:
                marks = getattr(q_config, "marks", 0)
            
            calculated_total += marks
            
            if marks <= 0:
                warnings.append(f"{q_id}: marks must be positive (got {marks})")
        
        if abs(calculated_total - total_marks) > 0.01:
            warnings.append(
                f"Total marks mismatch: sum of question marks ({calculated_total}) "
                f"does not equal declared total ({total_marks})"
            )
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "calculated_total": calculated_total,
            "declared_total": total_marks
        }
    
    @staticmethod
    def validate_all_questions_answered(ground_truth_questions: Dict, 
                                       extracted_answers: Dict) -> bool:
        """
        Check if all questions have non-empty answers
        """
        for q_id in ground_truth_questions.keys():
            answer = extracted_answers.get(q_id, "")
            if not answer or (isinstance(answer, str) and not answer.strip()):
                return False
        return True
    
    @staticmethod
    def get_unanswered_questions(ground_truth_questions: Dict, 
                                extracted_answers: Dict) -> List[str]:
        """
        Get list of questions that have no answer or empty answer
        """
        unanswered = []
        for q_id in ground_truth_questions.keys():
            answer = extracted_answers.get(q_id, "")
            if not answer or (isinstance(answer, str) and not answer.strip()):
                unanswered.append(q_id)
        return unanswered


class GradingValidator:
    """Validates grading results"""
    
    @staticmethod
    def validate_score(score: float, max_score: float, question_id: str) -> None:
        """
        Validate that score is within valid range
        """
        if score < 0:
            raise ValidationError(
                f"Score cannot be negative for {question_id}",
                {"score": score, "max_score": max_score}
            )
        
        if score > max_score:
            raise ValidationError(
                f"Score cannot exceed max score for {question_id}",
                {"score": score, "max_score": max_score}
            )
    
    @staticmethod
    def validate_grading_results(results: List[Dict], 
                                ground_truth_questions: Dict) -> Dict[str, Any]:
        """
        Validate grading results completeness and correctness
        """
        warnings = []
        
        result_question_ids = {r["question_id"] for r in results}
        expected_question_ids = set(ground_truth_questions.keys())
        
        missing = expected_question_ids - result_question_ids
        if missing:
            warnings.append(f"Missing grading results for: {', '.join(sorted(missing))}")
        
        for result in results:
            q_id = result["question_id"]
            score = result.get("score", 0)
            max_score = result.get("max_score", 0)
            
            try:
                GradingValidator.validate_score(score, max_score, q_id)
            except ValidationError as e:
                warnings.append(str(e))
        
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "total_results": len(results),
            "expected_results": len(expected_question_ids)
        }
