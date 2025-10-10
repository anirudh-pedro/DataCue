import { useState, useRef, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { FiSend, FiUpload, FiUser } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    };

    setMessages([...messages, newMessage]);
    setInputMessage('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Simulate AI response
    setIsTyping(true);
    setTimeout(() => {
      const aiResponse = {
        role: 'assistant',
        content: generateAIResponse(inputMessage),
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 2000);
  };

  const generateAIResponse = (userInput) => {
    if (userInput.toLowerCase().includes('hello') || userInput.toLowerCase().includes('hi')) {
      return "Hello! I'm your AI data analytics assistant. Upload a dataset or ask me anything about data analysis!";
    }
    
    return `I understand you're asking about "${userInput}". I can help you with data analysis, visualization, predictions, and more. Would you like to upload a dataset to get started?`;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (e) => {
    setInputMessage(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      <Sidebar />
      
      <div className="flex-1 flex flex-col relative">
        {messages.length === 0 ? (
          // Empty State - Centered Input
          <div className="flex-1 flex flex-col items-center justify-center px-4">
            <div className="w-full max-w-3xl">
              {/* Welcome Message */}
              <div className="text-center mb-8">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gray-900 flex items-center justify-center">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Welcome to DataCue</h2>
                <p className="text-gray-400">Your AI-powered data analytics assistant</p>
              </div>
              
              {/* Centered Input Box */}
              <div className="relative flex items-end gap-2 bg-gray-900 rounded-3xl px-4 py-3 border border-gray-800 focus-within:border-gray-700 transition-colors shadow-lg">
                {/* Upload Button */}
                <button
                  className="flex-shrink-0 p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
                  title="Upload file"
                >
                  <FiUpload className="text-xl" />
                </button>
                
                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder="Message DataCue"
                  rows="1"
                  className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2"
                  style={{
                    maxHeight: '200px',
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#4B5563 transparent'
                  }}
                />
                
                {/* Send Button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim()}
                  className={`flex-shrink-0 p-2 rounded-lg transition-all ${
                    inputMessage.trim()
                      ? 'bg-white text-black hover:bg-gray-200'
                      : 'text-gray-600 cursor-not-allowed'
                  }`}
                  title="Send message"
                >
                  <FiSend className="text-xl" />
                </button>
              </div>
              
              {/* Footer Text */}
              <div className="text-center mt-3 text-xs text-gray-500">
                DataCue can make mistakes. Check important info.
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Messages Container - After First Message */}
            <div className="flex-1 overflow-y-auto" style={{ scrollbarWidth: 'thin', scrollbarColor: '#4B5563 #000000' }}>
              <div className="w-full px-4 py-6 space-y-6">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${msg.role === 'assistant' ? 'justify-start' : 'justify-end'}`}
                  >
                    {/* AI Avatar - Left */}
                    {msg.role === 'assistant' && (
                      <div className="flex-shrink-0 w-8 h-8">
                        <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
                          <HiSparkles className="text-white text-lg" />
                        </div>
                      </div>
                    )}
                    
                    {/* Message Content */}
                    <div className={`max-w-[70%] ${
                      msg.role === 'assistant' 
                        ? 'bg-gray-900 rounded-2xl rounded-tl-sm' 
                        : 'bg-gray-800 rounded-2xl rounded-tr-sm'
                    } px-4 py-3 border border-gray-800`}>
                      <div className="text-white text-base leading-7 whitespace-pre-wrap break-words">
                        {msg.content}
                      </div>
                    </div>
                    
                    {/* User Avatar - Right */}
                    {msg.role === 'user' && (
                      <div className="flex-shrink-0 w-8 h-8">
                        <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
                          <FiUser className="text-white text-lg" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0 w-8 h-8">
                      <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center">
                        <HiSparkles className="text-white text-lg" />
                      </div>
                    </div>
                    <div className="max-w-[70%] bg-gray-900 rounded-2xl rounded-tl-sm px-4 py-3 border border-gray-800">
                      <div className="flex space-x-1">
                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area - Bottom (After First Message) */}
            <div className="border-t border-gray-900 bg-black">
              <div className="max-w-3xl mx-auto px-4 py-4">
                <div className="relative flex items-end gap-2 bg-gray-900 rounded-3xl px-4 py-3 border border-gray-800 focus-within:border-gray-700 transition-colors">
                  {/* Upload Button */}
                  <button
                    className="flex-shrink-0 p-2 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-gray-800"
                    title="Upload file"
                  >
                    <FiUpload className="text-xl" />
                  </button>
                  
                  {/* Textarea */}
                  <textarea
                    ref={textareaRef}
                    value={inputMessage}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    placeholder="Message DataCue"
                    rows="1"
                    className="flex-1 bg-transparent text-white placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2"
                    style={{
                      maxHeight: '200px',
                      scrollbarWidth: 'thin',
                      scrollbarColor: '#4B5563 transparent'
                    }}
                  />
                  
                  {/* Send Button */}
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim()}
                    className={`flex-shrink-0 p-2 rounded-lg transition-all ${
                      inputMessage.trim()
                        ? 'bg-white text-black hover:bg-gray-200'
                        : 'text-gray-600 cursor-not-allowed'
                    }`}
                    title="Send message"
                  >
                    <FiSend className="text-xl" />
                  </button>
                </div>
                
                {/* Footer Text */}
                <div className="text-center mt-2 text-xs text-gray-500">
                  DataCue can make mistakes. Check important info.
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
