/**
 * Hooks index - Re-export all custom hooks
 */

export { useAuthSession, useHealthCheck } from './useAuthSession';
export { 
  useChatMessages, 
  useFileUpload,
  STAGE_LABELS,
  DEFAULT_STAGE_MESSAGE,
  generateMessageId,
  buildTimestamp,
  normalizeAnswer,
  generateChatTitle,
} from './useChatMessages';
