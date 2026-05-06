import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../services/authService';

function Register() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    const handleRegister = async () => {
        setError(null);
        setIsLoading(true); 

        try {
            // 1. Call the service function
            const data = await registerUser(email, username, password);

            // 2. Success! Save the token
            localStorage.setItem('access_token', data.access_token);
            
            // 3. Redirect
            navigate('/');

        } catch (err) {
            // 4. If the service threw an error, display it in the UI
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <h1>HOLMES</h1>
            <div className="auth-menu">
                <h2>Register</h2>
                
                {/* Display error messages if they exist */}
                {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

                <form className="auth-form" onSubmit={(e) => {
                    e.preventDefault();
                    handleRegister();
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
                            type="text" 
                            required
                            value={username}
                            placeholder='Username'
                            onChange={(e) => setUsername(e.target.value)}
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
                    
                    {/* Disable the button while the request is running so they don't double-click */}
                    <button type="submit" disabled={isLoading}>
                        {isLoading ? 'Registering...' : 'Register'}
                    </button>
                </form>
                <div className="auth-redirect">
                    <button onClick={() => navigate('/login')}>Already have an account? Login</button>
                </div>
            </div>
        </div>
    );
}

export default Register;