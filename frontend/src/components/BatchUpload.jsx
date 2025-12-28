import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Users, Download } from 'lucide-react';
import { getExams, uploadBatchPapers, gradeBatch, getBatchStatus, exportBatchCSV } from '../services/api';

export default function BatchUpload() {
  const navigate = useNavigate();
  const [exams, setExams] = useState([]);
  const [selectedExam, setSelectedExam] = useState('');
  const [file, setFile] = useState(null);
  const [batchId, setBatchId] = useState(null);
  const [batchStatus, setBatchStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [grading, setGrading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      const data = await getExams();
      setExams(data);
    } catch (error) {
      console.error('Failed to load exams:', error);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.zip')) {
        setMessage({ type: 'error', text: 'Please select a ZIP file' });
        return;
      }
      setFile(selectedFile);
      setMessage({ type: '', text: '' });
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!selectedExam) {
      setMessage({ type: 'error', text: 'Please select an exam' });
      return;
    }

    if (!file) {
      setMessage({ type: 'error', text: 'Please select a ZIP file' });
      return;
    }

    setUploading(true);
    setMessage({ type: 'info', text: 'Uploading and extracting batch...' });

    try {
      const formData = new FormData();
      formData.append('exam_id', selectedExam);
      formData.append('file', file);

      const result = await uploadBatchPapers(formData);
      
      setBatchId(result.batch_id);
      setMessage({ 
        type: 'success', 
        text: `Batch uploaded: ${result.uploaded} students ready, ${result.failed} failed` 
      });

      // Load batch status
      loadBatchStatus(result.batch_id);
    } catch (error) {
      console.error('Upload error:', error);
      const detail = error.response?.data?.detail;
      if (typeof detail === 'object' && detail.warnings) {
        setMessage({ 
          type: 'error', 
          text: `Upload failed: ${detail.warnings.join(', ')}` 
        });
      } else {
        setMessage({ 
          type: 'error', 
          text: `Upload failed: ${detail || error.message}` 
        });
      }
    } finally {
      setUploading(false);
    }
  };

  const loadBatchStatus = async (id) => {
    try {
      const status = await getBatchStatus(id);
      setBatchStatus(status);
    } catch (error) {
      console.error('Failed to load batch status:', error);
    }
  };

  const handleGrade = async () => {
    if (!batchId) {
      setMessage({ type: 'error', text: 'Please upload batch first' });
      return;
    }

    setGrading(true);
    setMessage({ type: 'info', text: 'Grading all students... This may take several minutes.' });

    try {
      const result = await gradeBatch(batchId);
      
      setMessage({ 
        type: 'success', 
        text: `Grading complete! ${result.report.successful} successful, ${result.report.failed} failed` 
      });

      // Reload batch status
      loadBatchStatus(batchId);
    } catch (error) {
      console.error('Grading error:', error);
      setMessage({ 
        type: 'error', 
        text: `Grading failed: ${error.response?.data?.detail || error.message}` 
      });
    } finally {
      setGrading(false);
    }
  };

  const handleExportCSV = async () => {
    if (!batchId) return;

    try {
      setMessage({ type: 'info', text: 'Generating CSV...' });
      await exportBatchCSV(batchId);
      setMessage({ type: 'success', text: 'CSV downloaded successfully' });
    } catch (error) {
      console.error('Export error:', error);
      setMessage({ 
        type: 'error', 
        text: `Export failed: ${error.response?.data?.detail || error.message}` 
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#16a34a';
      case 'failed':
        return '#dc2626';
      case 'uploaded':
        return '#2563eb';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Batch Upload</h1>
        <p>Upload multiple student papers at once</p>
      </div>

      {message.text && (
        <div className={`message message-${message.type}`}>
          <AlertCircle size={20} />
          <span>{message.text}</span>
        </div>
      )}

      {/* Instructions */}
      <div className="form-section" style={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)' }}>
        <h3>How to Prepare Your ZIP File</h3>
        <ol style={{ marginLeft: '1.5rem', color: 'var(--text-secondary)', lineHeight: '1.8' }}>
          <li>Create a folder for each student named with their Student ID (e.g., MSDS24001, MSDS24002)</li>
          <li>Place all answer sheet images for that student inside their folder</li>
          <li>Compress all student folders into a single ZIP file</li>
          <li>Upload the ZIP file below</li>
        </ol>
        <div style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          background: 'var(--bg-secondary)', 
          borderRadius: '8px',
          fontFamily: 'monospace',
          fontSize: '0.875rem'
        }}>
          <div>class_papers.zip</div>
          <div style={{ marginLeft: '1rem' }}>├── MSDS24001/</div>
          <div style={{ marginLeft: '2rem' }}>│   ├── page1.jpg</div>
          <div style={{ marginLeft: '2rem' }}>│   └── page2.jpg</div>
          <div style={{ marginLeft: '1rem' }}>├── MSDS24002/</div>
          <div style={{ marginLeft: '2rem' }}>│   ├── page1.jpg</div>
          <div style={{ marginLeft: '2rem' }}>│   └── page2.jpg</div>
          <div style={{ marginLeft: '1rem' }}>└── MSDS24003/</div>
          <div style={{ marginLeft: '2rem' }}>    └── page1.jpg</div>
        </div>
      </div>

      <form onSubmit={handleUpload}>
        <div className="form-section">
          <h3>Batch Details</h3>
          
          <div className="form-group">
            <label>Select Exam</label>
            <select
              value={selectedExam}
              onChange={(e) => setSelectedExam(e.target.value)}
              required
            >
              <option value="">Choose an exam...</option>
              {exams.map((exam) => (
                <option key={exam.id} value={exam.id}>
                  {exam.exam_name} ({exam.total_marks} marks)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-section">
          <h3>Upload ZIP File</h3>
          <div className="file-upload-area">
            <Upload size={48} />
            <p><strong>Click to upload</strong> or drag and drop</p>
            <p className="text-muted">ZIP file containing student folders</p>
            <input
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              id="batch-file-input"
            />
            <label htmlFor="batch-file-input" className="btn-primary" style={{ marginTop: '1rem', cursor: 'pointer' }}>
              Select ZIP File
            </label>
          </div>

          {file && (
            <div className="file-list">
              <div className="file-item">
                <FileText size={20} />
                <span className="file-item-name">{file.name}</span>
                <CheckCircle size={20} style={{ color: 'var(--success)' }} />
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '2rem' }}>
          <button
            type="submit"
            disabled={uploading || grading}
            className="btn-primary btn-lg"
          >
            {uploading ? (
              <>
                <div className="loading" />
                Uploading...
              </>
            ) : (
              <>
                <Upload size={20} />
                Upload Batch
              </>
            )}
          </button>

          {batchId && batchStatus?.status === 'uploaded' && (
            <button
              type="button"
              onClick={handleGrade}
              disabled={uploading || grading}
              className="btn-success btn-lg"
            >
              {grading ? (
                <>
                  <div className="loading" />
                  Grading...
                </>
              ) : (
                <>
                  <CheckCircle size={20} />
                  Grade All Students
                </>
              )}
            </button>
          )}

          {batchId && batchStatus?.status === 'completed' && (
            <button
              type="button"
              onClick={handleExportCSV}
              className="btn-secondary btn-lg"
            >
              <Download size={20} />
              Export CSV
            </button>
          )}
        </div>
      </form>

      {/* Batch Status */}
      {batchStatus && (
        <div className="form-section">
          <h3>Batch Status</h3>
          
          <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            <div className="stat-card">
              <div className="stat-icon">
                <Users size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{batchStatus.total_students}</div>
                <div className="stat-title">Total Students</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: '#dcfce7', color: '#16a34a' }}>
                <CheckCircle size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{batchStatus.successful_students}</div>
                <div className="stat-title">Successful</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: '#fee2e2', color: '#dc2626' }}>
                <AlertCircle size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value">{batchStatus.failed_students}</div>
                <div className="stat-title">Failed</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon" style={{ background: '#dbeafe', color: '#2563eb' }}>
                <FileText size={24} />
              </div>
              <div className="stat-content">
                <div className="stat-value" style={{ textTransform: 'capitalize' }}>
                  {batchStatus.status}
                </div>
                <div className="stat-title">Status</div>
              </div>
            </div>
          </div>

          {/* Student List */}
          {batchStatus.submissions && batchStatus.submissions.length > 0 && (
            <div style={{ marginTop: '2rem' }}>
              <h4>Student Details</h4>
              <div style={{ 
                maxHeight: '400px', 
                overflowY: 'auto',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                marginTop: '1rem'
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead style={{ 
                    position: 'sticky', 
                    top: 0, 
                    background: 'var(--bg-secondary)',
                    borderBottom: '2px solid var(--border-color)'
                  }}>
                    <tr>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Student ID</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Status</th>
                      <th style={{ padding: '1rem', textAlign: 'right' }}>Score</th>
                      <th style={{ padding: '1rem', textAlign: 'left' }}>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batchStatus.submissions.map((sub, index) => (
                      <tr 
                        key={index}
                        style={{ 
                          borderBottom: '1px solid var(--border-color)',
                          background: index % 2 === 0 ? 'var(--bg-primary)' : 'var(--bg-secondary)'
                        }}
                      >
                        <td style={{ padding: '1rem' }}>
                          <strong>{sub.student_id}</strong>
                        </td>
                        <td style={{ padding: '1rem' }}>
                          <span style={{ 
                            padding: '0.25rem 0.75rem',
                            borderRadius: '12px',
                            fontSize: '0.875rem',
                            background: `${getStatusColor(sub.status)}20`,
                            color: getStatusColor(sub.status),
                            fontWeight: 500
                          }}>
                            {sub.status}
                          </span>
                        </td>
                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                          {sub.total_score !== null ? (
                            <strong>{sub.total_score}</strong>
                          ) : (
                            <span style={{ color: 'var(--text-secondary)' }}>-</span>
                          )}
                        </td>
                        <td style={{ padding: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                          {sub.error_message || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
