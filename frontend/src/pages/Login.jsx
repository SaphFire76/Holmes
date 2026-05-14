import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../services/authService';

function Login() {
    // 1. State for our form inputs
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    
    // 2. State for UI feedback
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    // Add parameters with default values
    const handleLogin = async (manualEmail = null, manualPassword = null) => {
        setIsLoading(true);
        setError(null);

        // Use the passed arguments if they exist; otherwise, use state
        const loginEmail = manualEmail || email;
        const loginPassword = manualPassword || password;

        try {
            // Use the local constants here, not the state variables
            const data = await loginUser(loginEmail, loginPassword);

            localStorage.setItem('access_token', data.access_token);
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <h1>HOLMES</h1>
            <div className="auth-menu">
                <h2>Login</h2>
                
                {/* Display error messages if they exist (e.g., wrong password) */}
                {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

                <form className="auth-form" onSubmit={(e) => {
                    e.preventDefault();
                    handleLogin();
                }}>
                    <div>
                        <input 
                            type="email" 
                            required
                            value={email}
                            placeholder='Email'
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <input 
                            type="password" 
                            required
                            value={password}
                            placeholder='Password'
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    
                    {/* Disable the button while it's fetching */}
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Logging in...' : 'Login'}
                    </button>
                </form>
                <div className="auth-redirect">
                    <button onClick={() => navigate('/register')}>Don't have an account? Register</button>
                </div>
                <div className="guest-login">
                    <button onClick={async () => {
                        await handleLogin('test@test.com', 'password');
                    }}>
                        Continue as Guest
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Login;