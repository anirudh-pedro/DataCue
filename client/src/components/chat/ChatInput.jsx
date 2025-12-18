/**
 * Chat input component with file upload support.
 */

import { useRef, useEffect } from 'react';
import { FiSend, FiUpload } from 'react-icons/fi';

const ChatInput = ({
  inputMessage,
  setInputMessage,
  onSendMessage,
  onFileSelect,
  isUploading,
  isTyping,
  sessionReady,
}) => {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputMessage]);

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSendMessage();
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      event.target.value = ''; // Reset input
      onFileSelect(file);
    }
  };

  const isSendDisabled = !inputMessage.trim() || isUploading || !sessionReady;

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-end gap-3 bg-gray-50 rounded-2xl p-3 border border-gray-200 focus-within:border-purple-400 focus-within:ring-2 focus-within:ring-purple-100 transition-all">
          {/* File Upload Button */}
          <button
            onClick={handleFileClick}
            disabled={isUploading || !sessionReady}
            className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Upload CSV/Excel file"
          >
            <FiUpload className="w-5 h-5" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
            className="hidden"
          />

          {/* Text Input */}
          <textarea
            ref={textareaRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isUploading
                ? 'Processing file...'
                : 'Ask about your data or upload a CSV/Excel file...'
            }
            disabled={isUploading}
            rows={1}
            className="flex-1 bg-transparent resize-none border-none outline-none text-gray-700 placeholder-gray-400 max-h-32 disabled:opacity-50"
          />

          {/* Send Button */}
          <button
            onClick={onSendMessage}
            disabled={isSendDisabled}
            className="p-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg shadow-purple-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
          >
            <FiSend className="w-5 h-5" />
          </button>
        </div>

        {/* Helper Text */}
        <div className="text-center mt-2 text-xs text-gray-400">
          Press Enter to send • Shift+Enter for new line • Upload CSV/Excel files
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
