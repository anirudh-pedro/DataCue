import { useState } from 'react';
import { FiCopy, FiCheck, FiUser } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

const MessageBubble = ({ message, isBot, timestamp, children }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex items-start space-x-3 group animate-fadeIn ${!isBot && 'flex-row-reverse space-x-reverse'}`}>
      {/* Avatar */}
      <div className={`
        w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
        ${isBot ? 'bg-gray-800' : 'bg-gray-700'}
      `}>
        {isBot ? (
          <HiSparkles className="text-white text-lg" />
        ) : (
          <FiUser className="text-white text-lg" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${!isBot && 'flex flex-col items-end'}`}>
        <div className={`
          rounded-2xl p-4 ${isBot ? 'rounded-tl-none' : 'rounded-tr-none'}
          ${isBot ? 'bg-gray-900 border border-gray-800' : 'bg-gray-800 border border-gray-700'}
          relative
        `}>
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 p-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
            title="Copy message"
          >
            {copied ? (
              <FiCheck className="text-green-400 text-sm" />
            ) : (
              <FiCopy className="text-gray-400 text-sm" />
            )}
          </button>

          {/* Message Text */}
          <p className="text-white text-sm leading-relaxed whitespace-pre-wrap break-words pr-8">
            {message}
          </p>

          {/* Children (for charts, cards, etc.) */}
          {children && (
            <div className="mt-3">
              {children}
            </div>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && (
          <p className="text-xs text-gray-500 mt-1 px-2">
            {timestamp}
          </p>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
