/**
 * Message list component for rendering chat messages.
 */

import { useRef, useEffect } from 'react';
import { FiUser } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';
import ChartMessage from '../ChartMessage';

const MessageList = ({
  messages,
  isTyping,
  uploadStatusMessage,
  hasDashboard,
  onViewDashboard,
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-purple-100 to-indigo-100 mb-4">
            <HiSparkles className="w-8 h-8 text-purple-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            Welcome to DataCue!
          </h2>
          <p className="text-gray-500 max-w-md">
            Upload a CSV or Excel file to get started. I'll analyze your data
            and generate interactive visualizations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            hasDashboard={hasDashboard}
            onViewDashboard={onViewDashboard}
          />
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
              <HiSparkles className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              {uploadStatusMessage ? (
                <p className="text-gray-600 text-sm">{uploadStatusMessage}</p>
              ) : (
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

/**
 * Individual message bubble component.
 */
const MessageBubble = ({ message, hasDashboard, onViewDashboard }) => {
  const isUser = message.role === 'user';
  const hasChart = message.chart && Object.keys(message.chart).length > 0;

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-gradient-to-br from-gray-600 to-gray-700'
            : 'bg-gradient-to-br from-purple-500 to-indigo-600'
        }`}
      >
        {isUser ? (
          <FiUser className="w-4 h-4 text-white" />
        ) : (
          <HiSparkles className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div
        className={`max-w-[80%] ${
          isUser
            ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-2xl rounded-tr-md'
            : 'bg-white border border-gray-100 rounded-2xl rounded-tl-md shadow-sm'
        } px-4 py-3`}
      >
        {/* Text Content */}
        {message.content && (
          <p
            className={`text-sm whitespace-pre-wrap ${
              isUser ? 'text-white' : 'text-gray-700'
            }`}
          >
            {message.content}
          </p>
        )}

        {/* Chart */}
        {hasChart && (
          <div className="mt-3">
            <ChartMessage chart={message.chart} />
          </div>
        )}

        {/* Dashboard Button */}
        {message.showDashboardButton && hasDashboard && (
          <button
            onClick={onViewDashboard}
            className="mt-3 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-medium rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all shadow-md"
          >
            📊 View Dashboard
          </button>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <p
            className={`text-xs mt-2 ${
              isUser ? 'text-purple-200' : 'text-gray-400'
            }`}
          >
            {message.timestamp}
          </p>
        )}
      </div>
    </div>
  );
};

export default MessageList;
