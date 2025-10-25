import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { onAuthStateChanged } from 'firebase/auth';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import ChartMessage from '../components/ChartMessage';
import { FiSend, FiUpload, FiUser } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';
import { auth } from '../firebase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const STAGE_LABELS = {
  upload_received: '📁 Upload received. Preparing analysis…',
  reading_csv: '🔍 Reading CSV and validating columns…',
  ingestion_complete: '🧼 Data ingestion complete. Cleaning dataset…',
  ingestion_failed: '❌ Ingestion failed. Please review your dataset.',
  generating_summary: '📊 Generating summary statistics…',
  summary_ready: '📈 Summary ready. Crafting dashboards…',
  computing_insights: '💡 Computing insights and recommendations…',
  insights_ready: '✨ Insights generated. Finalising presentation…',
  training_model: '🧮 Training regression model…',
  computing_shap: '🧠 Computing SHAP explanations…',
  prediction_ready: '🤖 Predictions ready. Wrapping up…',
  pipeline_complete: '✅ Analysis complete — visualizations ready!',
  error: '⚠️ An error occurred while processing the dataset.'
};
const DEFAULT_STAGE_MESSAGE = 'Backend processing in progress…';

const ChatPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatusMessage, setUploadStatusMessage] = useState('');
  const [hasDashboard, setHasDashboard] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('chatSessionId'));
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [healthWarning, setHealthWarning] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const isInitializingRef = useRef(false); // Prevent race condition
  const sessionReady = Boolean(sessionId && currentUser && !isLoadingHistory);

  const generateMessageId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2, 12);
  };

  const persistMessage = async (message) => {
    if (!sessionId || !currentUser) {
      return;
    }

    try {
      await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: message.id,
          role: message.role,
          content: message.content,
          timestamp: message.timestamp,
          chart: message.chart,
          metadata: message.metadata,
          showDashboardButton: Boolean(message.showDashboardButton),
        }),
      });
    } catch (error) {
      console.error('Failed to persist chat message:', error);
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      const otpVerified = sessionStorage.getItem('otpVerified') === 'true';
      if (!user) {
        navigate('/login', { replace: true });
        setCurrentUser(null);
        return;
      }

      if (!otpVerified) {
        if (user.email) {
          sessionStorage.setItem('otpEmail', user.email);
        }
        navigate('/verify-otp', { replace: true, state: { email: user.email } });
        setCurrentUser(null);
        return;
      }

      setCurrentUser(user);
    });

    return () => unsubscribe();
  }, [navigate]);

  // Health check monitoring
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/health`);
        if (!response.ok) {
          setHealthWarning('⚠️ Backend service is experiencing issues');
          return;
        }
        const health = await response.json();
        if (health.status === 'degraded') {
          if (health.services?.mongodb === 'unreachable') {
            setHealthWarning('⚠️ Database connection lost - chat history may not save');
          } else {
            setHealthWarning('⚠️ Some services are degraded');
          }
        } else {
          setHealthWarning('');
        }
      } catch (error) {
        setHealthWarning('⚠️ Unable to reach backend service');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadHistory = async (activeSessionId) => {
      try {
        const response = await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions/${activeSessionId}/messages`);
        if (!response.ok) {
          throw new Error('Failed to load chat history.');
        }
        const payload = await response.json();
        const history = Array.isArray(payload.messages)
          ? payload.messages.map((message) => ({
              id: message.id || generateMessageId(),
              role: message.role,
              content: message.content,
              timestamp: message.timestamp,
              chart: message.chart,
              metadata: message.metadata || {},
              showDashboardButton: Boolean(message.showDashboardButton),
            }))
          : [];

        setMessages(history);
        
        // Check if dashboard data exists in MongoDB
        const hasDashboardButton = history.some((message) => message.showDashboardButton);
        setHasDashboard(hasDashboardButton);
        
        return true;
      } catch (error) {
        console.error('Failed to load chat history:', error);
        setMessages([]);
        setHasDashboard(false);
        localStorage.removeItem('chatSessionId');
        localStorage.removeItem('chatSessionUserId');
        return false;
      }
    };

    const createNewSession = async (user) => {
      const response = await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.uid,
          email: user.email,
          display_name: user.displayName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create chat session.');
      }

      const payload = await response.json();
      const newSessionId = payload.session_id;
      localStorage.setItem('chatSessionId', newSessionId);
      localStorage.setItem('chatSessionUserId', user.uid);
      setSessionId(newSessionId);
      setMessages([]);
      setHasDashboard(false);
    };

    const initialiseSession = async (user) => {
      // Prevent multiple simultaneous initialization calls
      if (isInitializingRef.current) {
        return;
      }
      
      isInitializingRef.current = true;
      setIsLoadingHistory(true);
      
      try {
        const storedSessionId = localStorage.getItem('chatSessionId');
        const storedUserId = localStorage.getItem('chatSessionUserId');

        if (storedSessionId && storedUserId === user.uid) {
          const loaded = await loadHistory(storedSessionId);
          if (loaded) {
            setSessionId(storedSessionId);
            return;
          }
        }

        await createNewSession(user);
      } catch (error) {
        console.error('Failed to initialise chat session:', error);
      } finally {
        setIsLoadingHistory(false);
        isInitializingRef.current = false;
      }
    };

    if (currentUser) {
      initialiseSession(currentUser);
    } else {
      setSessionId(null);
      setMessages([]);
      setIsLoadingHistory(false);
      isInitializingRef.current = false;
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const appendMessage = (message, options = {}) => {
    const messageWithId = message.id ? message : { ...message, id: generateMessageId() };
    setMessages((prev) => [...prev, messageWithId]);

    if (options.persist !== false) {
      persistMessage(messageWithId);
    }

    return messageWithId;
  };

  const buildTimestamp = () => new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const normaliseAnswer = (payload) => {
    if (!payload || typeof payload !== 'object') {
      return 'I was not able to interpret the server response.';
    }

    if (payload.error) {
      return payload.error;
    }

    if (typeof payload.answer === 'string' && payload.answer.trim()) {
      return payload.answer;
    }

    if (typeof payload.response === 'string' && payload.response.trim()) {
      return payload.response;
    }

    if (typeof payload.message === 'string' && payload.message.trim()) {
      return payload.message;
    }

    if (payload.summary && typeof payload.summary === 'string') {
      return payload.summary;
    }

    const stringField = Object.values(payload).find((value) => typeof value === 'string' && value.trim());
    if (stringField) {
      return stringField;
    }

    return `Here is what I received:\n\n\`\`\`json\n${JSON.stringify(payload, null, 2)}\n\`\`\``;
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isUploading || !sessionReady) return;

    const userContent = inputMessage;
    const userMessage = {
      role: 'user',
      content: userContent,
      timestamp: buildTimestamp(),
    };

    appendMessage(userMessage);
    setInputMessage('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    setIsTyping(true);
    try {
      // Use ask-visual endpoint to get both text and optional chart
      const response = await fetch(`${API_BASE_URL}/knowledge/ask-visual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userContent,
          request_chart: true,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        let message = 'Request failed';
        try {
          const maybeJson = await response.json();
          message = maybeJson?.detail || maybeJson?.error || message;
        } catch (_) {
          try {
            const text = await response.text();
            if (text) message = text;
          } catch (_) {}
        }
        // Provide a friendlier hint when analysis hasn't run yet
        if (response.status === 400 && /analy[sz]e_dataset/i.test(message)) {
          message = 'Please upload a dataset and wait for analysis to complete before asking questions.';
        }
        throw new Error(message);
      }

      const payload = await response.json();
      
      // Append text answer
      const assistantMessage = {
        role: 'assistant',
        content: normaliseAnswer(payload),
        timestamp: buildTimestamp(),
      };
      appendMessage(assistantMessage);
      
      // If there's a chart, append it separately
      if (payload.chart && payload.chart.figure) {
        appendMessage({
          role: 'chart',
          chart: payload.chart,
          timestamp: buildTimestamp(),
        });
      }
    } catch (error) {
      appendMessage({
        role: 'assistant',
        content: `I could not reach the analytics service. ${error.message || 'Unknown error.'}`,
        timestamp: buildTimestamp(),
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleInputChange = (event) => {
    setInputMessage(event.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleUploadClick = () => {
    if (isUploading || !sessionReady) return;
    fileInputRef.current?.click();
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const handleViewDashboard = async () => {
    if (!sessionId) return;
    
    try {
      // Fetch dashboard data from MongoDB (canonical source)
      const response = await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions/${sessionId}/dashboard`);
      if (!response.ok) {
        console.error('No dashboard data found for this session');
        return;
      }
      
      const dashboardData = await response.json();
      if (dashboardData.charts && dashboardData.charts.length > 0) {
        navigate('/dashboard', { state: { dashboardData } });
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    event.target.value = '';

    if (!sessionReady) {
      return;
    }

    setIsUploading(true);
    setUploadStatusMessage('📁 Uploading dataset…');
    setIsTyping(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('dashboard_type', 'auto');
      formData.append('include_advanced_charts', 'true');
      formData.append('generate_dashboard_insights', 'true');
      formData.append('knowledge_generate_insights', 'true');
      formData.append('knowledge_generate_recommendations', 'true');
      if (sessionId) {
        formData.append('chat_session_id', sessionId);
      }

      const sessionResponse = await fetch(`${API_BASE_URL}/orchestrator/pipeline/session`, {
        method: 'POST',
        body: formData,
      });

      if (!sessionResponse.ok) {
        const errorText = await sessionResponse.text();
        throw new Error(errorText || 'Unable to create processing session.');
      }

      const sessionPayload = await sessionResponse.json();
      const sessionId = sessionPayload?.session_id;
      if (!sessionId) {
        throw new Error('Pipeline session ID missing from server response.');
      }

      const pipelineResult = await new Promise((resolve, reject) => {
  const streamUrl = `${API_BASE_URL.replace(/\/+$/, '')}/orchestrator/pipeline/session/${sessionId}/stream`;
        const eventSource = new EventSource(streamUrl);

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (!data || !data.stage) {
              return;
            }

            const stageMessage = STAGE_LABELS[data.stage] || DEFAULT_STAGE_MESSAGE;
            setUploadStatusMessage(stageMessage);

            // Skip chart_ready events during upload (charts only shown in dashboard)
            // Charts will still appear in chat when user asks specific questions
            if (data.stage === 'pipeline_complete') {
              eventSource.close();
              resolve(data.payload);
            } else if (data.stage === 'ingestion_failed' || data.stage === 'error') {
              eventSource.close();
              const errorMessage = typeof data.payload === 'object' && data.payload?.message
                ? data.payload.message
                : 'Pipeline failed. Please try again.';
              reject(new Error(errorMessage));
            }
          } catch (parseError) {
            console.error('Failed to parse pipeline event', parseError);
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          reject(new Error('Connection lost while receiving analysis updates.'));
        };
      });

      const datasetName = pipelineResult?.dataset_name || file.name;
      setUploadStatusMessage(STAGE_LABELS.pipeline_complete);
      
      // Store dashboard data in MongoDB (canonical source)
      const dashboardData = pipelineResult?.steps?.dashboard;
      if (dashboardData && dashboardData.charts && dashboardData.charts.length > 0) {
        // Store in MongoDB via backend API
        try {
          await fetch(`${API_BASE_URL.replace(/\/+$/, '')}/chat/sessions/${sessionId}/dashboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              charts: dashboardData.charts,
              dataset_name: datasetName,
              summary: dashboardData.summary,
              quality_indicators: dashboardData.quality_indicators,
              metadata_summary: dashboardData.metadata_summary,
              layout: dashboardData.layout,
              filters: dashboardData.filters,
            }),
          });
        } catch (error) {
          console.error('Failed to store dashboard data:', error);
        }
        
        await sleep(500);
        
        // Enable dashboard button
        setHasDashboard(true);
        
        // Show message with dashboard button (don't auto-navigate)
        appendMessage({
          role: 'assistant',
          content: `✅ Analysis complete! I generated ${dashboardData.charts.length} visualizations for "${datasetName}".\n\n🎨 Your dashboard is ready with:\n• ${dashboardData.charts.filter(c => c.type === 'histogram').length} Distribution Charts\n• ${dashboardData.charts.filter(c => c.type === 'bar').length} Bar Charts\n• ${dashboardData.charts.filter(c => c.type === 'scatter').length} Scatter Plots\n• ${dashboardData.charts.filter(c => c.type === 'heatmap').length} Correlation Heatmap\n• ${dashboardData.charts.filter(c => c.type === 'sankey').length} Flow Diagram\n\nClick "View Dashboard" below to explore all visualizations, or ask me questions about the data!`,
          timestamp: buildTimestamp(),
          showDashboardButton: true,
        });
      } else {
        // Fallback to chat message if no charts generated
        appendMessage({
          role: 'assistant',
          content: `I have processed "${datasetName}". Ask me anything about this dataset!`,
          timestamp: buildTimestamp(),
        });
        await sleep(900);
      }
    } catch (error) {
      let friendly;
      if (error?.message?.includes('Connection lost while receiving analysis updates')) {
        friendly = '🔌 Connection lost during analysis. Please check your network or try again.';
      } else if (error?.message?.includes('Unable to create processing session')) {
        friendly = '🛠️ Backend error: Unable to start analysis. Please try again later.';
      } else if (error?.message?.includes('Pipeline failed')) {
        friendly = '❌ Data processing failed. Please check your file format or try a different dataset.';
      } else if (error?.message?.includes('Pipeline session ID missing')) {
        friendly = '⚠️ Server did not return a session ID. Please try again.';
      } else if (error?.name === 'TypeError' && error?.message?.includes('Failed to fetch')) {
        friendly = '🌐 Network error: Unable to reach the server. Please check your internet connection.';
      } else {
        friendly = `⚠️ ${error?.message || 'Unknown error.'}`;
      }
      setUploadStatusMessage(friendly);
      appendMessage({
        role: 'assistant',
        content: `Failed to process the uploaded file. ${friendly}`,
        timestamp: buildTimestamp(),
      });
      await sleep(1100);
    } finally {
      setIsUploading(false);
      setUploadStatusMessage('');
      setIsTyping(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-black">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        <div className="relative flex flex-1 flex-col">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={handleFileChange}
        />
        
        {/* Health Warning Banner */}
        {healthWarning && (
          <div className="absolute top-0 left-0 right-0 z-30 bg-yellow-900/90 border-b border-yellow-700 px-4 py-2 text-center">
            <p className="text-sm text-yellow-100">{healthWarning}</p>
          </div>
        )}
        
        {isLoadingHistory && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="w-12 h-12 border-4 border-gray-700 border-t-white rounded-full animate-spin" aria-hidden="true" />
            <p className="mt-4 text-sm text-gray-300">Loading your conversation…</p>
          </div>
        )}
        {isUploading && (
          <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="w-12 h-12 border-4 border-gray-700 border-t-white rounded-full animate-spin" aria-hidden="true" />
            <p className="mt-4 text-sm text-gray-300 text-center whitespace-pre-line">
              {uploadStatusMessage || DEFAULT_STAGE_MESSAGE}
            </p>
          </div>
        )}
        
        {/* Floating Dashboard Button */}
        {hasDashboard && !isUploading && (
          <button
            onClick={handleViewDashboard}
            className="absolute top-4 right-4 z-20 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <HiSparkles className="text-lg" />
            View Dashboard
          </button>
        )}
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
                  onClick={handleUploadClick}
                  disabled={isUploading || !sessionReady}
                  className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
                    sessionReady ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-600 cursor-not-allowed'
                  }`}
                  title={sessionReady ? 'Upload file' : 'Waiting for chat session'}
                >
                  <FiUpload className="text-xl" />
                </button>
                
                {/* Textarea */}
                <textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder={sessionReady ? 'Message DataCue' : 'Loading your conversation…'}
                  rows="1"
                  disabled={!sessionReady}
                  className={`flex-1 bg-transparent placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2 ${
                    sessionReady ? 'text-white' : 'text-gray-500 cursor-not-allowed'
                  }`}
                  style={{
                    maxHeight: '200px',
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#4B5563 transparent'
                  }}
                />
                
                {/* Send Button */}
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isUploading || !sessionReady}
                  className={`flex-shrink-0 p-2 rounded-lg transition-all ${
                    inputMessage.trim() && sessionReady
                      ? 'bg-white text-black hover:bg-gray-200'
                      : 'text-gray-600 cursor-not-allowed'
                  }`}
                  title={sessionReady ? 'Send message' : 'Waiting for chat session'}
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
                {messages.map((msg, index) => {
                  // Render charts with ChartMessage component
                  if (msg.role === 'chart') {
                    return (
                      <ChartMessage
                        key={msg.id || index}
                        chart={msg.chart}
                        timestamp={msg.timestamp}
                        messageId={msg.id}
                      />
                    );
                  }
                  
                  // Render regular messages
                  return (
                    <div
                      key={msg.id || index}
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
                        
                        {/* Dashboard Button */}
                        {msg.showDashboardButton && (
                          <button
                            onClick={handleViewDashboard}
                            className="mt-3 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
                          >
                            <HiSparkles className="text-lg" />
                            View Dashboard
                          </button>
                        )}
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
                  );
                })}
                
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
                    onClick={handleUploadClick}
                    disabled={isUploading || !sessionReady}
                    className={`flex-shrink-0 p-2 rounded-lg transition-colors ${
                      sessionReady ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-600 cursor-not-allowed'
                    }`}
                    title={sessionReady ? 'Upload file' : 'Waiting for chat session'}
                  >
                    <FiUpload className="text-xl" />
                  </button>
                  
                  {/* Textarea */}
                  <textarea
                    ref={textareaRef}
                    value={inputMessage}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    placeholder={sessionReady ? 'Message DataCue' : 'Loading your conversation…'}
                    rows="1"
                    disabled={!sessionReady}
                    className={`flex-1 bg-transparent placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2 ${
                      sessionReady ? 'text-white' : 'text-gray-500 cursor-not-allowed'
                    }`}
                    style={{
                      maxHeight: '200px',
                      scrollbarWidth: 'thin',
                      scrollbarColor: '#4B5563 transparent'
                    }}
                  />
                  
                  {/* Send Button */}
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isUploading || !sessionReady}
                    className={`flex-shrink-0 p-2 rounded-lg transition-all ${
                      inputMessage.trim() && sessionReady
                        ? 'bg-white text-black hover:bg-gray-200'
                        : 'text-gray-600 cursor-not-allowed'
                    }`}
                    title={sessionReady ? 'Send message' : 'Waiting for chat session'}
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
    </div>
  );
};

export default ChatPage;
