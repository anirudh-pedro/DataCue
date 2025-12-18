/**
 * Session Manager - Handles authentication session persistence
 * Sessions last for 4 days and are stored in localStorage
 */

const SESSION_DURATION_DAYS = 4;
const SESSION_DURATION_MS = SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000;

class SessionManager {
  constructor() {
    this.STORAGE_KEYS = {
      OTP_VERIFIED: 'datacue_otp_verified',
      OTP_EMAIL: 'datacue_otp_email',
      SESSION_TIMESTAMP: 'datacue_session_timestamp',
      SESSION_EXPIRY: 'datacue_session_expiry',
    };
  }

  /**
   * Create a new session after OTP verification
   * @param {string} email - User's email
   */
  createSession(email) {
    const now = Date.now();
    const expiryTime = now + SESSION_DURATION_MS;

    localStorage.setItem(this.STORAGE_KEYS.OTP_VERIFIED, 'true');
    localStorage.setItem(this.STORAGE_KEYS.OTP_EMAIL, email);
    localStorage.setItem(this.STORAGE_KEYS.SESSION_TIMESTAMP, now.toString());
    localStorage.setItem(this.STORAGE_KEYS.SESSION_EXPIRY, expiryTime.toString());
  }

  /**
   * Check if current session is valid
   * @returns {boolean} - True if session exists and hasn't expired
   */
  isSessionValid() {
    const otpVerified = localStorage.getItem(this.STORAGE_KEYS.OTP_VERIFIED);
    const expiryTime = localStorage.getItem(this.STORAGE_KEYS.SESSION_EXPIRY);

    if (!otpVerified || otpVerified !== 'true') {
      return false;
    }

    if (!expiryTime) {
      // Old session without expiry - clear it
      this.clearSession();
      return false;
    }

    const now = Date.now();
    const expiry = parseInt(expiryTime, 10);

    if (now >= expiry) {
      this.clearSession();
      return false;
    }

    return true;
  }

  /**
   * Get the stored email from session
   * @returns {string|null} - User's email or null
   */
  getEmail() {
    return localStorage.getItem(this.STORAGE_KEYS.OTP_EMAIL);
  }

  /**
   * Get session expiry information
   * @returns {Object} - Expiry time and remaining time
   */
  getSessionInfo() {
    const expiryTime = localStorage.getItem(this.STORAGE_KEYS.SESSION_EXPIRY);
    const createdTime = localStorage.getItem(this.STORAGE_KEYS.SESSION_TIMESTAMP);

    if (!expiryTime || !createdTime) {
      return null;
    }

    const now = Date.now();
    const expiry = parseInt(expiryTime, 10);
    const created = parseInt(createdTime, 10);
    const remainingMs = expiry - now;

    return {
      created: new Date(created),
      expires: new Date(expiry),
      remainingMs: remainingMs,
      remainingDays: Math.floor(remainingMs / (24 * 60 * 60 * 1000)),
      remainingHours: Math.floor((remainingMs % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000)),
      isValid: remainingMs > 0,
    };
  }

  /**
   * Extend current session by 4 days
   */
  extendSession() {
    if (!this.isSessionValid()) {
      return false;
    }

    const now = Date.now();
    const newExpiry = now + SESSION_DURATION_MS;

    localStorage.setItem(this.STORAGE_KEYS.SESSION_EXPIRY, newExpiry.toString());
    return true;
  }

  /**
   * Clear all session data
   */
  clearSession() {
    localStorage.removeItem(this.STORAGE_KEYS.OTP_VERIFIED);
    localStorage.removeItem(this.STORAGE_KEYS.OTP_EMAIL);
    localStorage.removeItem(this.STORAGE_KEYS.SESSION_TIMESTAMP);
    localStorage.removeItem(this.STORAGE_KEYS.SESSION_EXPIRY);
    
    // Also clear old sessionStorage if it exists
    sessionStorage.removeItem('otpVerified');
    sessionStorage.removeItem('otpEmail');
  }

  /**
   * Migrate old sessionStorage to new localStorage system
   */
  migrateOldSession() {
    const oldOtpVerified = sessionStorage.getItem('otpVerified');
    const oldEmail = sessionStorage.getItem('otpEmail');

    if (oldOtpVerified === 'true' && oldEmail) {
      this.createSession(oldEmail);
      sessionStorage.removeItem('otpVerified');
      sessionStorage.removeItem('otpEmail');
    }
  }

  /**
   * Check if session will expire soon (within 24 hours)
   * @returns {boolean}
   */
  isExpiringSoon() {
    const info = this.getSessionInfo();
    if (!info || !info.isValid) {
      return false;
    }

    const oneDay = 24 * 60 * 60 * 1000;
    return info.remainingMs < oneDay;
  }
}

// Export singleton instance
export const sessionManager = new SessionManager();
export default sessionManager;
