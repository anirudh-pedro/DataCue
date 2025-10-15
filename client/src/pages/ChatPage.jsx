import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Navbar from '../components/Navbar';
import ChartMessage from '../components/ChartMessage';
import { FiSend, FiUpload, FiUser } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi2';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const STAGE_LABELS = {
  upload_received: '📁 Upload received. Preparing analysis…',
  reading_csv: '🔍 Reading CSV and validating columns…',
  ingestion_complete: '🧼 Data ingestion complete. Cleaning dataset…',
  ingestion_failed: '❌ Ingestion failed. Please review your dataset.',
  generating_summary: '📊 Generating summary statistics…',
  summary_ready: '📈 Summary ready. Crafting dashboards…',
  computing_insights: '� Computing insights and recommendations…',
  insights_ready: '💡 Insights generated. Finalising presentation…',
  training_model: '�🧮 Training regression model…',
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
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const appendMessage = (message) => {
    setMessages((prev) => [...prev, message]);
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
    if (!inputMessage.trim() || isUploading) return;

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
        body: JSON.stringify({ question: userContent, request_chart: true }),
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
    if (isUploading) return;
    fileInputRef.current?.click();
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const handleViewDashboard = () => {
    const data = JSON.parse(sessionStorage.getItem('dashboardData') || '{}');
    if (data.charts && data.charts.length > 0) {
      navigate('/dashboard', { state: { dashboardData: data } });
    }
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    event.target.value = '';

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
      
      // Store dashboard data and show button in chat (maintain chat history)
      const dashboardData = pipelineResult?.steps?.dashboard;
      if (dashboardData && dashboardData.charts && dashboardData.charts.length > 0) {
        // Store dashboard data in sessionStorage for navigation
        sessionStorage.setItem('dashboardData', JSON.stringify({
          charts: dashboardData.charts,
          dataset_name: datasetName,
          summary: dashboardData.summary,
          quality_indicators: dashboardData.quality_indicators,
          metadata_summary: dashboardData.metadata_summary,
          layout: dashboardData.layout,
          filters: dashboardData.filters,
        }));
        
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
      const friendly = error?.message || 'Unknown error.';
      setUploadStatusMessage(`⚠️ ${friendly}`);
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
        {isUploading && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/70 backdrop-blur-sm">
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
                  disabled={isUploading}
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
                  disabled={!inputMessage.trim() || isUploading}
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
                {messages.map((msg, index) => {
                  // Render charts with ChartMessage component
                  if (msg.role === 'chart') {
                    return (
                      <ChartMessage
                        key={index}
                        chart={msg.chart}
                        timestamp={msg.timestamp}
                      />
                    );
                  }
                  
                  // Render regular messages
                  return (
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
                    disabled={isUploading}
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
                    disabled={!inputMessage.trim() || isUploading}
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
    </div>
  );
};

export default ChatPage;
