import { Navigate } from 'react-router-dom';

function ProtectedRoute({ children }) {
    // 1. Look for the hand-stamp in local storage
    const token = localStorage.getItem('access_token');

    // 2. If it's missing, redirect them to the login page!
    // (The 'replace' keyword means they can't hit the back button to return to the protected page)
    if (!token) {
        return <Navigate to="/login" replace />;
    }

    // 3. If they DO have the token, let them through to the component!
    return children;
}

export default ProtectedRoute;