import { useState, useRef, useEffect } from 'react'; // Added useRef and useEffect
import api from './api';
import './App.css';

function App() {
  const [emailText, setEmailText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Ref to access the actual DOM element of the textarea
  const textareaRef = useRef(null);

  // Function to handle auto-expansion
  const handleInput = (e) => {
    setEmailText(e.target.value);
    autoResize(e.target);
  };

  const autoResize = (element) => {
    element.style.height = 'auto'; // Reset height to recalculate
    element.style.height = `${element.scrollHeight}px`; // Set to new content height
  };

  const handleAnalyse = async () => {
    if (!emailText.trim()) return;

    setLoading(true);
    setResult(null);
    setError('');

    try {
      const response = await api.post('/analyse', {
        email: emailText
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      setError('Could not reach Holmes. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">Holmes</h1>

      <div className="content-wrapper">
        <div className="input-container">
          <textarea
            ref={textareaRef}
            className="email-input"
            placeholder="paste email here"
            value={emailText}
            onChange={handleInput}
            rows={1} // Start with 1 row
          />
          <button 
            className="send-button" 
            onClick={handleAnalyse}
            disabled={loading}
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>

        {error && <p className="error-msg">{error}</p>}
        
        {result && (
          <div className={`result-box ${result.is_phishing ? 'danger' : 'safe'}`}>
            <h2>{result.is_phishing ? '🚨 Phishing Detected' : '✅ Legitimate Email'}</h2>
            <p><strong>Risk:</strong> {result.risk_level}</p>
            <p>{result.explanation}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;