import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import ErrorBoundary from './components/ErrorBoundary';
import ChatPage from './pages/ChatPage';
import Login from './pages/Login';
import Profile from './pages/Profile';
import VerifyOtp from './pages/VerifyOtp';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ChatProvider>
            <div className="h-screen flex flex-col bg-black">
              <Routes>
                <Route path="/" element={<Navigate to="/login" replace />} />
                <Route path="/login" element={<Login />} />
                <Route path="/verify-otp" element={<VerifyOtp />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/profile" element={<Profile />} />
              </Routes>
            </div>
          </ChatProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
