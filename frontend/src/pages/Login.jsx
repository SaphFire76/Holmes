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

    const handleLogin = async () => {
        setIsLoading(true);
        setError(null);

        try {
            // 1. Call the service file to do the heavy lifting
            const data = await loginUser(email, password);

            // 2. Success! Save the JWT to the browser
            localStorage.setItem('access_token', data.access_token);
            
            // 3. The Magic Routing Trick! 
            // We redirect to the Dashboard, smuggling the history data in the router state
            navigate('/');

        } catch (err) {
            // 4. Catch the error thrown by the service file
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="login">
            <h2>Login</h2>
            
            {/* Display error messages if they exist (e.g., wrong password) */}
            {error && <div style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

            <form className="login-form" onSubmit={(e) => {
                e.preventDefault();
                handleLogin();
            }}>
                <div>
                    <label>Email:</label>
                    <input 
                        type="email" 
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>
                <div>
                    <label>Password:</label>
                    <input 
                        type="password" 
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                
                {/* Disable the button while it's fetching */}
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Logging in...' : 'Login'}
                </button>
            </form>
        </div>
    );
}

export default Login;