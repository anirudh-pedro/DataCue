import { useState, useEffect } from 'react';
import { FiMessageSquare, FiFile, FiPlus, FiTrash2, FiChevronLeft, FiChevronRight, FiMenu } from 'react-icons/fi';
import { auth } from '../firebase';
import { apiGet, apiDelete } from '../lib/api';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [activeChat, setActiveChat] = useState(null);
  const [hoveredChat, setHoveredChat] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch user's chat sessions (disabled - new backend has no session persistence yet)
  useEffect(() => {
    const fetchSessions = async () => {
      const user = auth.currentUser;
      if (!user) return;

      // New backend doesn't persist chat sessions; use local storage only
      const currentSessionId = localStorage.getItem('sessionId');
      if (currentSessionId) {
        setActiveChat(currentSessionId);
        setChatHistory([{
          session_id: currentSessionId,
          title: 'Current Chat',
          has_dashboard: false,
          message_count: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }]);
      } else {
        setChatHistory([]);
      }
    };

    fetchSessions();
  }, []);

  const handleDeleteChat = async (id, e) => {
    if (e) {
      e.stopPropagation();
    }
    
    if (!confirm('Are you sure you want to delete this chat session? This cannot be undone.')) {
      return;
    }

    // Clear local state only (new backend has no session persistence)
    setChatHistory(prev => prev.filter(chat => chat.session_id !== id));
    
    // If deleted session was active, clear it
    if (activeChat === id) {
      setActiveChat(null);
      localStorage.removeItem('sessionId');
      localStorage.removeItem('datasetId');
      window.location.reload(); // Reload to create new session
    }
  };

  const handleNewChat = () => {
    // Clear session and navigate to create a fresh chat
    localStorage.removeItem('sessionId');
    localStorage.removeItem('sessionUserId');
    localStorage.removeItem('datasetId');
    window.location.href = '/chat';
  };

  return (
    <>
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="md:hidden fixed top-3 left-3 z-50 p-2 bg-gray-900 hover:bg-gray-800 rounded-lg text-white transition-colors cursor-pointer"
      >
        <FiMenu className="text-xl" />
      </button>

      {isMobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40 cursor-pointer"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <div 
        className={`
          bg-black border-r border-gray-800 flex flex-col transition-all duration-300
          fixed md:relative top-16 md:top-0 bottom-0 md:bottom-auto left-0 z-40
          ${isCollapsed ? 'w-14' : 'w-60'}
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div className={`
          p-3 border-b border-gray-800 flex items-center
          ${isCollapsed ? 'justify-center' : 'justify-between'}
        `}>
          {!isCollapsed && (
            <h2 className="text-sm font-semibold text-white">Chats</h2>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 hover:bg-gray-900 rounded-lg transition-colors text-white flex items-center justify-center cursor-pointer"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <FiChevronRight className="text-base" />
            ) : (
              <FiChevronLeft className="text-base" />
            )}
          </button>
        </div>

        <div className="p-2">
          <button 
            onClick={handleNewChat}
            className={`
              w-full flex items-center justify-center gap-2
              bg-white hover:bg-gray-200 text-black 
              rounded-xl font-medium transition-all cursor-pointer
              ${isCollapsed ? 'h-12 w-12' : 'px-4 py-3'}
            `}
            title="New Chat"
          >
            <FiPlus className={`${isCollapsed ? 'text-xl' : 'text-xl'}`} strokeWidth={2} />
            {!isCollapsed && <span className="text-sm">New Chat</span>}
          </button>
        </div>

        <div 
          className="flex-1 overflow-y-auto px-2"
          style={{ 
            scrollbarWidth: 'thin', 
            scrollbarColor: '#4B5563 #000000' 
          }}
        >
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-gray-700 border-t-white rounded-full animate-spin" />
            </div>
          ) : chatHistory.length === 0 ? (
            <div className="text-center py-8 px-4">
              <p className="text-sm text-gray-400">No chat history</p>
              <p className="text-xs text-gray-500 mt-1">Start a new chat to begin</p>
            </div>
          ) : (
            chatHistory.map((chat) => (
              <div
                key={chat.session_id}
                onClick={() => {
                  localStorage.setItem('sessionId', chat.session_id);
                  setActiveChat(chat.session_id);
                  setIsMobileOpen(false);
                  window.location.reload();
                }}
                onMouseEnter={() => setHoveredChat(chat.session_id)}
                onMouseLeave={() => setHoveredChat(null)}
                className={`
                  group relative mb-2 rounded-lg cursor-pointer transition-all
                  ${activeChat === chat.session_id 
                    ? 'bg-gray-900 border border-gray-700' 
                    : 'hover:bg-gray-900/50 border border-transparent'
                  }
                `}
              >
                <div className={`
                  flex items-center p-3
                  ${isCollapsed ? 'justify-center' : ''}
                `}>
                  <div className={`
                    flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center
                    ${chat.has_dashboard ? 'bg-purple-900/30' : 'bg-gray-800'}
                  `}>
                    {chat.has_dashboard ? (
                      <FiFile className="text-purple-400 text-sm" />
                    ) : (
                      <FiMessageSquare className="text-white text-sm" />
                    )}
                  </div>

                  {!isCollapsed && (
                    <div className="ml-3 flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {chat.title || 'Untitled Chat'}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {new Date(chat.updated_at).toLocaleDateString()} • {chat.message_count || 0} messages
                      </p>
                    </div>
                  )}

                  {!isCollapsed && hoveredChat === chat.session_id && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteChat(chat.session_id);
                      }}
                      className="ml-2 p-1.5 hover:bg-red-900/20 rounded transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                    >
                      <FiTrash2 className="text-red-500 text-sm" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {!isCollapsed && (
          <div className="p-3 border-t border-gray-800">
            <p className="text-xs text-gray-400 text-center">
              {chatHistory.length} conversations
            </p>
          </div>
        )}
      </div>
    </>
  );
};

export default Sidebar;
