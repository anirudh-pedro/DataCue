import Navbar from './components/Navbar';
import ChatPage from './pages/ChatPage';

function App() {
  return (
    <div className="h-screen flex flex-col bg-black">
      <Navbar />
      <ChatPage />
    </div>
  );
}

export default App;
