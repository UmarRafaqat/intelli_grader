"""
Batch Processing Module for Multiple Student Papers
Handles ZIP file extraction, grouping, and batch grading
"""
import os
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import json


class BatchProcessor:
    """Handles batch processing of multiple student papers"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.batch_dir = self.upload_dir / "batches"
        self.batch_dir.mkdir(exist_ok=True)
    
    def extract_zip(self, zip_path: str, batch_id: int) -> Path:
        """
        Extract ZIP file to batch directory
        Returns path to extracted directory
        """
        extract_path = self.batch_dir / f"batch_{batch_id}"
        extract_path.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            return extract_path
        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid ZIP file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract ZIP: {str(e)}")
    
    def group_files_by_student(self, extract_path: Path) -> Dict[str, List[str]]:
        """
        Group image files by student ID from folder structure
        Expected structure: batch_dir/STUDENT_ID/page1.jpg, page2.jpg, ...
        Returns: {student_id: [image_paths]}
        """
        student_papers = {}
        
        # Iterate through subdirectories (each is a student)
        for student_dir in extract_path.iterdir():
            if not student_dir.is_dir():
                continue
            
            student_id = student_dir.name
            
            # Skip system directories
            if student_id.startswith('.') or student_id.startswith('__'):
                continue
            
            # Collect all image files for this student
            image_files = []
            for file_path in student_dir.iterdir():
                if file_path.is_file() and self._is_image_file(file_path):
                    image_files.append(str(file_path))
            
            if image_files:
                # Sort files to maintain page order
                image_files.sort()
                student_papers[student_id] = image_files
        
        return student_papers
    
    def _is_image_file(self, file_path: Path) -> bool:
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        return file_path.suffix.lower() in image_extensions
    
    def validate_batch_structure(self, student_papers: Dict[str, List[str]]) -> Tuple[bool, List[str]]:
        """
        Validate batch structure and return warnings
        Returns: (is_valid, warnings)
        """
        warnings = []
        
        if not student_papers:
            return False, ["No student folders found in ZIP file"]
        
        # Check each student has at least one image
        for student_id, images in student_papers.items():
            if not images:
                warnings.append(f"Student {student_id}: No images found")
        
        # Check for valid student IDs
        for student_id in student_papers.keys():
            if not student_id.strip():
                warnings.append(f"Invalid student ID: '{student_id}'")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    def cleanup_batch(self, batch_id: int):
        """Clean up batch directory after processing"""
        batch_path = self.batch_dir / f"batch_{batch_id}"
        if batch_path.exists():
            try:
                shutil.rmtree(batch_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup batch {batch_id}: {str(e)}")
    
    def generate_batch_report(self, batch_results: List[Dict]) -> Dict:
        """
        Generate summary report for batch processing
        """
        total = len(batch_results)
        successful = sum(1 for r in batch_results if r['status'] == 'completed')
        failed = sum(1 for r in batch_results if r['status'] == 'failed')
        
        # Calculate statistics for successful submissions
        scores = [r['total_score'] for r in batch_results if r['status'] == 'completed']
        
        report = {
            'total_students': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / total * 100), 2) if total > 0 else 0,
        }
        
        if scores:
            report['statistics'] = {
                'average_score': round(sum(scores) / len(scores), 2),
                'highest_score': max(scores),
                'lowest_score': min(scores),
            }
        
        # Failed students details
        failed_students = [
            {
                'student_id': r['student_id'],
                'error': r.get('error_message', 'Unknown error')
            }
            for r in batch_results if r['status'] == 'failed'
        ]
        
        if failed_students:
            report['failed_students'] = failed_students
        
        return report
    
    def export_to_csv(self, batch_results: List[Dict], exam_name: str, total_marks: float) -> str:
        """
        Export batch results to CSV format
        Returns CSV content as string
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Student ID',
            'Status',
            'Total Score',
            'Total Marks',
            'Percentage',
            'Grade',
            'Submission ID',
            'Error Message'
        ])
        
        # Data rows
        for result in batch_results:
            if result['status'] == 'completed':
                percentage = round((result['total_score'] / total_marks * 100), 2)
                grade = self._calculate_letter_grade(percentage)
                
                writer.writerow([
                    result['student_id'],
                    'Success',
                    result['total_score'],
                    total_marks,
                    f"{percentage}%",
                    grade,
                    result['submission_id'],
                    ''
                ])
            else:
                writer.writerow([
                    result['student_id'],
                    'Failed',
                    '',
                    '',
                    '',
                    '',
                    '',
                    result.get('error_message', 'Unknown error')
                ])
        
        return output.getvalue()
    
    def _calculate_letter_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 80:
            return 'A-'
        elif percentage >= 75:
            return 'B+'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 65:
            return 'B-'
        elif percentage >= 60:
            return 'C+'
        elif percentage >= 55:
            return 'C'
        elif percentage >= 50:
            return 'C-'
        elif percentage >= 45:
            return 'D'
        else:
            return 'F'
