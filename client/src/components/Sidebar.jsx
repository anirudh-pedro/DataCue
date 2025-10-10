import { useState } from 'react';
import { FiMessageSquare, FiFile, FiPlus, FiTrash2, FiChevronLeft, FiChevronRight } from 'react-icons/fi';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeChat, setActiveChat] = useState(null);
  const [hoveredChat, setHoveredChat] = useState(null);

  const chatHistory = [
    { id: 1, name: 'sales_data.csv', type: 'file', lastMessage: 'Analyzed sales trends' },
    { id: 2, name: 'New Analysis', type: 'chat', lastMessage: 'What are the key metrics?' },
    { id: 3, name: 'finance_2023.csv', type: 'file', lastMessage: 'Generated forecast' },
    { id: 4, name: 'Customer Insights', type: 'chat', lastMessage: 'Show customer segments' },
    { id: 5, name: 'customer_analytics.csv', type: 'file', lastMessage: 'Created dashboard' },
  ];

  const handleDeleteChat = (id) => {
    console.log('Delete chat:', id);
  };

  return (
    <div 
      className={`bg-black border-r border-gray-800 flex flex-col transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        {!isCollapsed && (
          <h2 className="text-lg font-semibold text-white">Chats</h2>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-gray-900 rounded-lg transition-colors text-white"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <FiChevronRight /> : <FiChevronLeft />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button className="w-full flex items-center justify-center space-x-2 bg-white hover:bg-gray-200 text-black px-4 py-3 rounded-lg font-medium transition-all">
          <FiPlus className="text-lg" />
          {!isCollapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#4B5563 #000000' }}>
        {chatHistory.map((chat) => (
          <div
            key={chat.id}
            onClick={() => setActiveChat(chat.id)}
            onMouseEnter={() => setHoveredChat(chat.id)}
            onMouseLeave={() => setHoveredChat(null)}
            className={`
              group relative mb-2 rounded-lg cursor-pointer transition-all
              ${activeChat === chat.id 
                ? 'bg-gray-900 border border-gray-700' 
                : 'hover:bg-gray-900/50 border border-transparent'
              }
            `}
          >
            <div className="flex items-center p-3">
              <div className={`
                flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
                ${chat.type === 'file' ? 'bg-gray-800' : 'bg-gray-800'}
              `}>
                {chat.type === 'file' ? (
                  <FiFile className="text-white text-sm" />
                ) : (
                  <FiMessageSquare className="text-white text-sm" />
                )}
              </div>

              {!isCollapsed && (
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {chat.name}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {chat.lastMessage}
                  </p>
                </div>
              )}

              {!isCollapsed && hoveredChat === chat.id && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteChat(chat.id);
                  }}
                  className="ml-2 p-1.5 hover:bg-red-900/20 rounded transition-colors opacity-0 group-hover:opacity-100"
                >
                  <FiTrash2 className="text-red-500 text-sm" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-400 text-center">
            {chatHistory.length} conversations
          </p>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
