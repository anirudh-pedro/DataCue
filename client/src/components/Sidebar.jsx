﻿import { useState } from 'react';
import { FiMessageSquare, FiFile, FiPlus, FiTrash2, FiChevronLeft, FiChevronRight, FiMenu } from 'react-icons/fi';

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
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
          {chatHistory.map((chat) => (
            <div
              key={chat.id}
              onClick={() => {
                setActiveChat(chat.id);
                setIsMobileOpen(false);
              }}
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
              <div className={`
                flex items-center p-3
                ${isCollapsed ? 'justify-center' : ''}
              `}>
                <div className={`
                  flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center
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
                    className="ml-2 p-1.5 hover:bg-red-900/20 rounded transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                  >
                    <FiTrash2 className="text-red-500 text-sm" />
                  </button>
                )}
              </div>
            </div>
          ))}
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
