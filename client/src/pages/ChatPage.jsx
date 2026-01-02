import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import ChartMessage from '../components/ChartMessage';
import { FiSend, FiUpload, FiUser, FiBarChart2, FiX } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';
import Plot from 'react-plotly.js';
import { auth } from '../firebase';
import sessionManager from '../utils/sessionManager';
import { apiPost, apiPostForm, API_BASE_URL } from '../lib/api';
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
  const [dashboardData, setDashboardData] = useState(null);
  const [showDashboardModal, setShowDashboardModal] = useState(false);
  const [isGeneratingDashboard, setIsGeneratingDashboard] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [datasetId, setDatasetId] = useState(() => localStorage.getItem('datasetId'));
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('chatSessionId'));
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [healthWarning, setHealthWarning] = useState('');
  const [isCheckingSession, setIsCheckingSession] = useState(true);
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

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        navigate('/login', { replace: true });
        setCurrentUser(null);
        return;
      }

      if (!sessionManager.isSessionValid()) {
        sessionManager.clearSession();
        try {
          await signOut(auth);
        } catch (error) {
          console.error('Error signing out expired session:', error);
        }
        navigate('/login', { replace: true });
        setCurrentUser(null);
        return;
      }

      setCurrentUser(user);
      setIsCheckingSession(false);
    });

    return () => unsubscribe();
  }, [navigate]);

  // Health check monitoring
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiGet('/health', { auth: false }); // Health check doesn't need auth
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
        // No persisted history in new backend; just clear and continue
        setMessages([]);
        setHasDashboard(false);
        return true;
      } catch (error) {
        console.error('Failed to load chat history:', error);
        setMessages([]);
        setHasDashboard(false);
        localStorage.removeItem('sessionId');
        localStorage.removeItem('chatSessionId');
        localStorage.removeItem('sessionUserId');
        localStorage.removeItem('chatSessionUserId');
        return false;
      }
    };

    const createNewSession = async (user) => {
      const newSessionId = crypto.randomUUID();
      localStorage.setItem('sessionId', newSessionId);
      localStorage.setItem('chatSessionId', newSessionId); // Backward compatibility
      localStorage.setItem('sessionUserId', user.uid);
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
        const storedSessionId = localStorage.getItem('sessionId') || localStorage.getItem('chatSessionId');
        const storedUserId = localStorage.getItem('sessionUserId') || localStorage.getItem('chatSessionUserId');

        if (storedSessionId && storedUserId === user.uid) {
          const loaded = await loadHistory(storedSessionId);
          if (loaded) {
            setSessionId(storedSessionId);
            // Update to new key format (keep both for compatibility)
            localStorage.setItem('sessionId', storedSessionId);
            localStorage.setItem('chatSessionId', storedSessionId);
            localStorage.setItem('sessionUserId', user.uid);
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
    // Note: Messages are stored in React state only (no backend persistence)
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

  const generateChatTitle = (userMessage) => {
    // Generate a title from the first user message
    // Take first 50 chars or up to first sentence
    let title = userMessage.trim();

    // Find first sentence ending
    const sentenceEnd = title.search(/[.!?]\s/);
    if (sentenceEnd > 0 && sentenceEnd < 60) {
      title = title.substring(0, sentenceEnd + 1);
    } else if (title.length > 50) {
      title = title.substring(0, 47) + '...';
    }

    return title;
  };

  const updateSessionTitle = (title) => {
    // Store title locally only (no backend persistence)
    if (!sessionId) return;
    const stored = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    const idx = stored.findIndex(s => s.id === sessionId);
    if (idx >= 0) {
      stored[idx].title = title;
      localStorage.setItem('chatSessions', JSON.stringify(stored));
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isUploading || !sessionReady) return;
    if (!datasetId) {
      appendMessage({
        role: 'assistant',
        content: 'Please upload a CSV first so I know which dataset to query.',
        timestamp: buildTimestamp(),
      }, { persist: false });
      return;
    }

    const userContent = inputMessage;
    const userMessage = {
      role: 'user',
      content: userContent,
      timestamp: buildTimestamp(),
    };

    appendMessage(userMessage);
    setInputMessage('');

    // Auto-generate title from first user message
    const isFirstMessage = messages.filter(m => m.role === 'user').length === 0;
    if (isFirstMessage) {
      const title = generateChatTitle(userContent);
      updateSessionTitle(title);
    }

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    setIsTyping(true);
    try {
      const response = await apiPost('/chat/query', {
        dataset_id: datasetId,
        session_id: sessionId,
        question: userContent,
        include_explanation: true,
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
          } catch (_) { }
        }
        // Provide a friendlier hint when analysis hasn't run yet
        if (response.status === 400 && /analy[sz]e_dataset/i.test(message)) {
          message = 'Please upload a dataset and wait for analysis to complete before asking questions.';
        }
        throw new Error(message);
      }

      const payload = await response.json();

      // Build assistant text from explanation or data summary
      const textParts = [];
      if (payload.explanation) textParts.push(payload.explanation);
      if (!payload.explanation && payload.data) {
        try {
          textParts.push(JSON.stringify(payload.data, null, 2));
        } catch {
          textParts.push(String(payload.data));
        }
      }
      if (textParts.length === 0 && payload.message) textParts.push(payload.message);
      const assistantMessage = {
        role: 'assistant',
        content: textParts.join('\n\n') || 'I received a response.',
        timestamp: buildTimestamp(),
      };
      appendMessage(assistantMessage, { persist: false });
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

  const handleViewDashboard = () => {
    if (dashboardData) {
      setShowDashboardModal(true);
    } else {
      appendMessage({
        role: 'assistant',
        content: 'No dashboard available yet. Upload a CSV file to generate one automatically.',
        timestamp: buildTimestamp(),
      }, { persist: false });
    }
  };

  const generateDashboard = async (datasetIdToUse, sessionIdToUse) => {
    setIsGeneratingDashboard(true);
    try {
      const dashboardResponse = await apiPost(
        `/dashboard/generate-from-schema?dataset_id=${encodeURIComponent(datasetIdToUse)}&session_id=${encodeURIComponent(sessionIdToUse)}`
      );
      
      if (dashboardResponse.ok) {
        const dashboardPayload = await dashboardResponse.json();
        if (dashboardPayload.success && dashboardPayload.data) {
          setDashboardData(dashboardPayload.data);
          setHasDashboard(true);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Dashboard generation failed:', error);
      return false;
    } finally {
      setIsGeneratingDashboard(false);
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

      const endpoint = sessionId
        ? `/ingestion/upload?session_id=${encodeURIComponent(sessionId)}`
        : '/ingestion/upload';

      const uploadResponse = await apiPostForm(endpoint, formData, { auth: false });
      if (!uploadResponse.ok) {
        const text = await uploadResponse.text();
        throw new Error(text || 'Upload failed');
      }

      const payload = await uploadResponse.json();
      const data = payload?.data || {};
      const newDatasetId = data.dataset_id;
      const newSessionId = data.session_id || sessionId || crypto.randomUUID();

      if (!newDatasetId) {
        throw new Error('Dataset ID missing from upload response');
      }

      setDatasetId(newDatasetId);
      localStorage.setItem('datasetId', newDatasetId);

      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
      localStorage.setItem('chatSessionId', newSessionId);

      setUploadStatusMessage('📊 Generating dashboard…');

      // Generate dashboard automatically
      const dashboardGenerated = await generateDashboard(newDatasetId, newSessionId);
      
      setUploadStatusMessage('✅ Upload complete. You can now ask questions about your data.');

      // Notify user with dashboard button if generated
      appendMessage({
        role: 'assistant',
        content: dashboardGenerated 
          ? `Dataset uploaded successfully! I've analyzed "${data.dataset_name || file.name}" and generated a professional dashboard for you. Click below to view your insights.`
          : `Dataset uploaded successfully. Ask me anything about "${data.dataset_name || file.name}".`,
        timestamp: buildTimestamp(),
        showDashboardButton: dashboardGenerated,
      }, { persist: false });
    } catch (error) {
      const friendly = `⚠️ ${error?.message || 'Upload failed.'}`;
      setUploadStatusMessage(friendly);
      appendMessage({
        role: 'assistant',
        content: `Failed to upload the file. ${friendly}`,
        timestamp: buildTimestamp(),
      }, { persist: false });
    } finally {
      setIsUploading(false);
      setUploadStatusMessage('');
      setIsTyping(false);
    }
  };

  // Show loading state while checking session
  if (isCheckingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0d1117]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-white border-r-transparent"></div>
          <p className="mt-4 text-sm text-slate-400">Checking session...</p>
        </div>
      </div>
    );
  }

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
          {isGeneratingDashboard && !isUploading && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
              <div className="w-12 h-12 border-4 border-gray-700 border-t-purple-500 rounded-full animate-spin" aria-hidden="true" />
              <p className="mt-4 text-sm text-gray-300 text-center">
                <span className="text-purple-400">📊</span> Generating AI-powered dashboard…
              </p>
            </div>
          )}

          {/* Removed floating dashboard button - only show in message */}
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
                    className={`flex-shrink-0 p-2 rounded-lg transition-colors ${sessionReady ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-600 cursor-not-allowed'
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
                    className={`flex-1 bg-transparent placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2 ${sessionReady ? 'text-white' : 'text-gray-500 cursor-not-allowed'
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
                    className={`flex-shrink-0 p-2 rounded-lg transition-all ${inputMessage.trim() && sessionReady
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
                        <div className={`max-w-[70%] ${msg.role === 'assistant'
                            ? 'bg-gray-900 rounded-2xl rounded-tl-sm'
                            : 'bg-gray-800 rounded-2xl rounded-tr-sm'
                          } px-4 py-3 border border-gray-800`}>
                          <div className="text-white text-base leading-7 whitespace-pre-wrap break-words">
                            {msg.content}
                          </div>

                          {/* Dashboard Buttons */}
                          {msg.showDashboardButton && (
                            <div className="mt-3 flex items-center gap-3">
                              <button
                                onClick={handleViewDashboard}
                                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
                              >
                                <HiSparkles className="text-lg" />
                                View Dashboard
                              </button>
                            </div>
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
                      className={`flex-shrink-0 p-2 rounded-lg transition-colors ${sessionReady ? 'text-gray-400 hover:text-white hover:bg-gray-800' : 'text-gray-600 cursor-not-allowed'
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
                      className={`flex-1 bg-transparent placeholder-gray-500 focus:outline-none resize-none overflow-y-auto text-base leading-6 py-2 ${sessionReady ? 'text-white' : 'text-gray-500 cursor-not-allowed'
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
                      className={`flex-shrink-0 p-2 rounded-lg transition-all ${inputMessage.trim() && sessionReady
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

          {/* Floating Dashboard Button when dashboard is available */}
          {hasDashboard && !showDashboardModal && (
            <button
              onClick={() => setShowDashboardModal(true)}
              className="fixed bottom-24 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-full shadow-lg transition-all hover:scale-105"
            >
              <FiBarChart2 className="text-xl" />
              <span className="font-medium">Dashboard</span>
            </button>
          )}
        </div>
      </div>

      {/* Dashboard Modal */}
      {showDashboardModal && dashboardData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="relative w-full h-full max-w-7xl max-h-[95vh] m-4 bg-[#0d1117] rounded-2xl border border-gray-800 overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gradient-to-r from-gray-900 to-[#0d1117]">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
                  <FiBarChart2 className="text-white text-xl" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">
                    {dashboardData.dashboard_title || 'Analytics Dashboard'}
                  </h2>
                  <p className="text-sm text-gray-400">
                    {dashboardData.successful_charts || 0} charts generated • Powered by AI
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDashboardModal(false)}
                className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
              >
                <FiX className="text-2xl" />
              </button>
            </div>

            {/* Modal Body - Scrollable Charts Grid */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {dashboardData.charts?.map((chart, index) => (
                  <div 
                    key={chart.chart_id || index} 
                    className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors"
                  >
                    {/* Chart Header */}
                    <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/80">
                      <h3 className="font-semibold text-white text-sm">
                        {chart.title || `Chart ${index + 1}`}
                      </h3>
                      {chart.description && (
                        <p className="text-xs text-gray-400 mt-1">{chart.description}</p>
                      )}
                    </div>
                    
                    {/* Chart Content */}
                    <div className="p-4">
                      {chart.figure ? (
                        <Plot
                          data={chart.figure.data || []}
                          layout={{
                            ...chart.figure.layout,
                            autosize: true,
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#e2e8f0', size: 11 },
                            margin: { t: 40, r: 20, b: 60, l: 60 },
                            xaxis: { 
                              ...chart.figure.layout?.xaxis,
                              gridcolor: '#374151',
                              tickfont: { color: '#9ca3af' }
                            },
                            yaxis: { 
                              ...chart.figure.layout?.yaxis,
                              gridcolor: '#374151',
                              tickfont: { color: '#9ca3af' }
                            },
                          }}
                          config={{ 
                            displayModeBar: false, 
                            responsive: true 
                          }}
                          style={{ width: '100%', height: '280px' }}
                          useResizeHandler={true}
                        />
                      ) : chart.data ? (
                        <Plot
                          data={[{
                            type: chart.chart_type === 'pie' ? 'pie' : 'bar',
                            x: chart.chart_type === 'pie' ? undefined : (chart.data.x || chart.data.labels || []),
                            y: chart.chart_type === 'pie' ? undefined : (chart.data.y || chart.data.values || []),
                            labels: chart.chart_type === 'pie' ? (chart.data.labels || chart.data.x || []) : undefined,
                            values: chart.chart_type === 'pie' ? (chart.data.values || chart.data.y || []) : undefined,
                            marker: { 
                              color: chart.chart_type === 'pie' 
                                ? ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444']
                                : '#3b82f6' 
                            },
                          }]}
                          layout={{
                            autosize: true,
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#e2e8f0', size: 11 },
                            margin: { t: 40, r: 20, b: 60, l: 60 },
                            xaxis: { gridcolor: '#374151', tickfont: { color: '#9ca3af' } },
                            yaxis: { gridcolor: '#374151', tickfont: { color: '#9ca3af' } },
                          }}
                          config={{ displayModeBar: false, responsive: true }}
                          style={{ width: '100%', height: '280px' }}
                          useResizeHandler={true}
                        />
                      ) : (
                        <div className="h-[280px] flex items-center justify-center text-gray-500">
                          <p>No chart data available</p>
                        </div>
                      )}
                    </div>

                    {/* Chart Footer with metadata */}
                    {(chart.sql_query || chart.row_count !== undefined) && (
                      <div className="px-4 py-2 border-t border-gray-800 bg-gray-900/30">
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>{chart.chart_type?.toUpperCase()}</span>
                          {chart.row_count !== undefined && (
                            <span>{chart.row_count} data points</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Empty State */}
              {(!dashboardData.charts || dashboardData.charts.length === 0) && (
                <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                  <FiBarChart2 className="text-5xl mb-4 opacity-50" />
                  <p className="text-lg font-medium">No charts generated</p>
                  <p className="text-sm">Try uploading a dataset with more columns</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
