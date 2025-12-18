/**
 * Custom hook for managing chat messages and API interactions.
 */

import { useState, useCallback } from 'react';
import { apiGet, apiPost, apiPatch, apiPostForm, API_BASE_URL } from '../lib/api';

// Upload stage labels
export const STAGE_LABELS = {
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

export const DEFAULT_STAGE_MESSAGE = 'Backend processing in progress…';

/**
 * Generate a unique message ID.
 */
export const generateMessageId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2, 12);
};

/**
 * Build a timestamp string.
 */
export const buildTimestamp = () => 
  new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

/**
 * Normalize LLM response to extract the answer text.
 */
export const normalizeAnswer = (payload) => {
  if (!payload || typeof payload !== 'object') {
    return 'I was not able to interpret the server response.';
  }

  if (payload.error) return payload.error;
  if (typeof payload.answer === 'string' && payload.answer.trim()) return payload.answer;
  if (typeof payload.response === 'string' && payload.response.trim()) return payload.response;
  if (typeof payload.message === 'string' && payload.message.trim()) return payload.message;
  if (payload.summary && typeof payload.summary === 'string') return payload.summary;

  const stringField = Object.values(payload).find(
    (value) => typeof value === 'string' && value.trim()
  );
  if (stringField) return stringField;

  return `Here is what I received:\n\n\`\`\`json\n${JSON.stringify(payload, null, 2)}\n\`\`\``;
};

/**
 * Generate a chat title from the first message.
 */
export const generateChatTitle = (message) => {
  let title = message.trim();
  if (title.length < 3) {
    title = 'New Chat';
  } else if (title.length > 50) {
    title = title.substring(0, 47) + '...';
  }
  return title;
};

/**
 * Hook for managing chat messages.
 */
export function useChatMessages(sessionId, currentUser) {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [hasDashboard, setHasDashboard] = useState(false);

  // Persist message to backend
  const persistMessage = useCallback(async (message, retries = 3) => {
    if (!sessionId || !currentUser) return;

    for (let attempt = 1; attempt <= retries; attempt++) {
      try {
        const response = await apiPost(`/chat/sessions/${sessionId}/messages`, {
          id: message.id,
          role: message.role,
          content: message.content,
          timestamp: message.timestamp,
          chart: message.chart,
          metadata: message.metadata,
          showDashboardButton: Boolean(message.showDashboardButton),
        });
        
        if (response.ok) return;
        
        if (attempt === retries) {
          throw new Error(`Failed to persist message after ${retries} attempts`);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      } catch (error) {
        if (attempt === retries) {
          console.error('Failed to persist chat message:', error);
        }
      }
    }
  }, [sessionId, currentUser]);

  // Append a message to the chat
  const appendMessage = useCallback((message, options = {}) => {
    const messageWithId = message.id ? message : { ...message, id: generateMessageId() };
    setMessages((prev) => [...prev, messageWithId]);

    if (options.persist !== false) {
      persistMessage(messageWithId);
    }

    return messageWithId;
  }, [persistMessage]);

  // Load chat history from backend
  const loadHistory = useCallback(async (activeSessionId) => {
    try {
      const response = await apiGet(`/chat/sessions/${activeSessionId}/messages`);
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
      
      const hasDashboardButton = history.some((msg) => msg.showDashboardButton);
      setHasDashboard(hasDashboardButton);
      
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
  }, []);

  // Update session title
  const updateSessionTitle = useCallback(async (title) => {
    if (!sessionId) return;
    
    try {
      await apiPatch(`/chat/sessions/${sessionId}/title`, { title });
    } catch (error) {
      console.error('Failed to update session title:', error);
    }
  }, [sessionId]);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
    setHasDashboard(false);
  }, []);

  return {
    messages,
    setMessages,
    isTyping,
    setIsTyping,
    hasDashboard,
    setHasDashboard,
    appendMessage,
    persistMessage,
    loadHistory,
    updateSessionTitle,
    clearMessages,
  };
}

/**
 * Hook for handling file uploads and pipeline processing.
 */
export function useFileUpload(sessionId, appendMessage, updateSessionTitle, setHasDashboard) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatusMessage, setUploadStatusMessage] = useState('');

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const handleFileUpload = useCallback(async (file, messages) => {
    setIsUploading(true);
    setUploadStatusMessage('📁 Uploading dataset…');

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

      const sessionResponse = await apiPostForm('/orchestrator/pipeline/session', formData);

      if (!sessionResponse.ok) {
        const errorText = await sessionResponse.text();
        throw new Error(errorText || 'Unable to create processing session.');
      }

      const sessionPayload = await sessionResponse.json();
      const pipelineSessionId = sessionPayload?.session_id;
      if (!pipelineSessionId) {
        throw new Error('Pipeline session ID missing from server response.');
      }

      // Stream processing updates
      const pipelineResult = await new Promise((resolve, reject) => {
        const streamUrl = `${API_BASE_URL.replace(/\/+$/, '')}/orchestrator/pipeline/session/${pipelineSessionId}/stream`;
        const eventSource = new EventSource(streamUrl);

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (!data || !data.stage) return;

            const label = STAGE_LABELS[data.stage] || DEFAULT_STAGE_MESSAGE;
            setUploadStatusMessage(label);

            if (data.stage === 'pipeline_complete' || data.final) {
              eventSource.close();
              resolve(data);
            } else if (data.stage === 'error') {
              eventSource.close();
              reject(new Error(data.error || 'Pipeline failed'));
            }
          } catch {
            // Ignore parse errors for progress updates
          }
        };

        eventSource.onerror = () => {
          eventSource.close();
          reject(new Error('Connection lost while receiving analysis updates'));
        };

        // Timeout after 5 minutes
        setTimeout(() => {
          eventSource.close();
          reject(new Error('Analysis timed out after 5 minutes'));
        }, 5 * 60 * 1000);
      });

      // Extract metadata from pipeline result
      const ingestionResult = pipelineResult?.steps?.ingestion;
      const gridfsId = ingestionResult?.gridfs_id;
      const datasetName = ingestionResult?.file_name || file.name;
      const datasetId = ingestionResult?.dataset_id;

      // Store metadata in localStorage
      if (gridfsId) {
        localStorage.setItem('datasetGridfsId', gridfsId);
        localStorage.setItem('datasetName', datasetName);
      }
      if (datasetId) {
        localStorage.setItem('datasetId', datasetId);
      }

      setUploadStatusMessage(STAGE_LABELS.pipeline_complete);

      // Auto-generate title from filename on first upload
      const isFirstMessage = messages.filter(m => m.role === 'user' || m.role === 'file').length === 0;
      if (isFirstMessage) {
        updateSessionTitle(`Analysis: ${datasetName}`);
      }

      // Store and show dashboard
      const dashboardData = pipelineResult?.steps?.dashboard;
      if (dashboardData?.charts?.length > 0) {
        await apiPost(`/chat/sessions/${sessionId}/dashboard`, {
          charts: dashboardData.charts,
          dataset_name: datasetName,
          gridfs_id: gridfsId,
          summary: dashboardData.summary,
          quality_indicators: dashboardData.quality_indicators,
          metadata_summary: dashboardData.metadata_summary,
          layout: dashboardData.layout,
          filters: dashboardData.filters,
        });

        await sleep(500);
        setHasDashboard(true);

        const chartCounts = {
          histogram: dashboardData.charts.filter(c => c.type === 'histogram').length,
          bar: dashboardData.charts.filter(c => c.type === 'bar').length,
          scatter: dashboardData.charts.filter(c => c.type === 'scatter').length,
          heatmap: dashboardData.charts.filter(c => c.type === 'heatmap').length,
          sankey: dashboardData.charts.filter(c => c.type === 'sankey').length,
        };

        appendMessage({
          role: 'assistant',
          content: `✅ Analysis complete! I generated ${dashboardData.charts.length} visualizations for "${datasetName}".\n\n🎨 Your dashboard is ready with:\n• ${chartCounts.histogram} Distribution Charts\n• ${chartCounts.bar} Bar Charts\n• ${chartCounts.scatter} Scatter Plots\n• ${chartCounts.heatmap} Correlation Heatmap\n• ${chartCounts.sankey} Flow Diagram\n\nClick "View Dashboard" below to explore all visualizations, or ask me questions about the data!`,
          timestamp: buildTimestamp(),
          showDashboardButton: true,
          metadata: { datasetId },
        });
      } else {
        appendMessage({
          role: 'assistant',
          content: `I have processed "${datasetName}". Ask me anything about this dataset!`,
          timestamp: buildTimestamp(),
        });
      }

      return { success: true, datasetName, datasetId, gridfsId };
    } catch (error) {
      let friendlyMessage;
      if (error?.message?.includes('Connection lost')) {
        friendlyMessage = '🔌 Connection lost during analysis. Please check your network or try again.';
      } else if (error?.message?.includes('Unable to create processing session')) {
        friendlyMessage = '🛠️ Backend error: Unable to start analysis. Please try again later.';
      } else if (error?.message?.includes('Pipeline failed')) {
        friendlyMessage = '❌ Data processing failed. Please check your file format or try a different dataset.';
      } else {
        friendlyMessage = `❌ Upload failed: ${error?.message || 'Unknown error'}`;
      }

      appendMessage({
        role: 'assistant',
        content: friendlyMessage,
        timestamp: buildTimestamp(),
      });

      return { success: false, error: friendlyMessage };
    } finally {
      setIsUploading(false);
    }
  }, [sessionId, appendMessage, updateSessionTitle, setHasDashboard]);

  return {
    isUploading,
    uploadStatusMessage,
    setUploadStatusMessage,
    handleFileUpload,
  };
}

export default useChatMessages;
