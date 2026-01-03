"""
Test script for production safeguards
Tests rate limiting, timeouts, and retry logic

Note: These are standalone implementations to demonstrate the safeguards.
The actual implementations are in main.py.
"""

import asyncio
import time
import functools


# ============================================================================
# Standalone Implementations for Testing
# ============================================================================

class LLMTimeoutError(Exception):
    """Raised when LLM call exceeds timeout"""
    pass


def timeout_wrapper(timeout_seconds: int = 20):
    """
    Decorator to add timeout to sync functions.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # For sync functions, run in thread pool with timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs),
                        timeout=timeout_seconds
                    )
                )
            except asyncio.TimeoutError:
                raise LLMTimeoutError(f"LLM call timed out after {timeout_seconds}s")
            finally:
                loop.close()
        
        return wrapper
    
    return decorator


def retry_on_transient_errors(max_retries: int = 1, backoff_seconds: float = 1.0):
    """
    Decorator to retry LLM calls on transient failures.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except LLMTimeoutError as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_seconds * (2 ** attempt)
                        print(f"   ⚠️ LLM timeout, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Check for retryable errors (5xx, connection issues)
                    is_retryable = (
                        '500' in error_msg or '502' in error_msg or '503' in error_msg or '504' in error_msg or
                        'timeout' in error_msg or 'connection' in error_msg or 'network' in error_msg
                    )
                    
                    # Don't retry on client errors (4xx)
                    is_client_error = any(code in error_msg for code in ['400', '401', '403', '404', '429'])
                    
                    if is_retryable and not is_client_error and attempt < max_retries:
                        last_exception = e
                        wait_time = backoff_seconds * (2 ** attempt)
                        print(f"   ⚠️ Transient LLM error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    
                    # Non-retryable error, raise immediately
                    raise
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    
    return decorator


# ============================================================================
# Test 1: Timeout Wrapper
# ============================================================================

@timeout_wrapper(timeout_seconds=2)
def slow_function():
    """Simulates a slow LLM call"""
    time.sleep(5)  # Will timeout after 2s
    return "This should not be reached"


@timeout_wrapper(timeout_seconds=2)
def fast_function():
    """Simulates a fast LLM call"""
    time.sleep(0.5)
    return "Success"


def test_timeout():
    print("\n" + "="*60)
    print("TEST 1: Timeout Wrapper")
    print("="*60)
    
    # Test 1a: Function that times out
    print("\n1a. Testing function that exceeds timeout (5s > 2s)...")
    try:
        result = slow_function()
        print(f"   ❌ FAIL: Should have timed out but got: {result}")
    except LLMTimeoutError as e:
        print(f"   ✅ PASS: Correctly raised LLMTimeoutError: {e}")
    
    # Test 1b: Function that completes in time
    print("\n1b. Testing function that completes within timeout (0.5s < 2s)...")
    try:
        result = fast_function()
        print(f"   ✅ PASS: Function completed successfully: {result}")
    except LLMTimeoutError as e:
        print(f"   ❌ FAIL: Should not have timed out: {e}")


# ============================================================================
# Test 2: Retry Logic
# ============================================================================

call_count = 0

@retry_on_transient_errors(max_retries=2, backoff_seconds=0.5)
def flaky_function_transient():
    """Simulates transient failures (e.g., 503 Service Unavailable)"""
    global call_count
    call_count += 1
    
    if call_count < 3:  # Fail first 2 times
        raise Exception("503 Service Unavailable - transient error")
    
    return "Success after retries"


@retry_on_transient_errors(max_retries=2, backoff_seconds=0.5)
def flaky_function_client_error():
    """Simulates client errors (e.g., 400 Bad Request) - should NOT retry"""
    global call_count
    call_count += 1
    raise Exception("400 Bad Request - client error")


def test_retry():
    print("\n" + "="*60)
    print("TEST 2: Retry Logic")
    print("="*60)
    
    # Test 2a: Transient error - should retry
    global call_count
    call_count = 0
    
    print("\n2a. Testing transient error (503) - should retry...")
    try:
        result = flaky_function_transient()
        print(f"   ✅ PASS: Function succeeded after {call_count} attempts: {result}")
    except Exception as e:
        print(f"   ❌ FAIL: Should have succeeded after retries: {e}")
    
    # Test 2b: Client error - should NOT retry
    call_count = 0
    
    print("\n2b. Testing client error (400) - should NOT retry...")
    try:
        result = flaky_function_client_error()
        print(f"   ❌ FAIL: Should have raised exception: {result}")
    except Exception as e:
        if call_count == 1:
            print(f"   ✅ PASS: Correctly failed without retry (1 attempt): {e}")
        else:
            print(f"   ❌ FAIL: Retried {call_count} times but should not have")


# ============================================================================
# Test 3: Combined Timeout + Retry
# ============================================================================

attempt_count = 0

@retry_on_transient_errors(max_retries=1, backoff_seconds=0.5)
@timeout_wrapper(timeout_seconds=1)
def combined_function():
    """Simulates function that times out, then succeeds on retry"""
    global attempt_count
    attempt_count += 1
    
    if attempt_count == 1:
        time.sleep(2)  # First attempt times out
        return "Should not reach here"
    
    # Second attempt succeeds quickly
    return "Success on retry after timeout"


def test_combined():
    print("\n" + "="*60)
    print("TEST 3: Combined Timeout + Retry")
    print("="*60)
    
    global attempt_count
    attempt_count = 0
    
    print("\n3. Testing timeout on first attempt, success on retry...")
    try:
        result = combined_function()
        print(f"   ✅ PASS: Function succeeded on retry (attempt {attempt_count}): {result}")
    except Exception as e:
        print(f"   ❌ FAIL: Should have succeeded on retry: {e}")


# ============================================================================
# Test 4: Rate Limiting (Manual Test)
# ============================================================================

def test_rate_limiting_info():
    print("\n" + "="*60)
    print("TEST 4: Rate Limiting (Manual Test)")
    print("="*60)
    
    print("""
Rate limiting requires running the FastAPI server and making HTTP requests.

To test manually:

1. Start the backend server:
   cd backend_agents
   uvicorn main:app --reload --port 8001

2. Make 31 requests within 1 minute:
   for i in {1..31}; do
     curl -X POST http://localhost:8001/chat/query \\
       -H "Authorization: Bearer YOUR_TOKEN" \\
       -H "Content-Type: application/json" \\
       -d '{
         "dataset_id": "your-dataset-id",
         "question": "What is the total revenue?",
         "session_id": "your-session-id"
       }' && echo "Request $i"
   done

3. Expected behavior:
   - Requests 1-30: Should succeed (200 OK)
   - Request 31: Should fail with 429 Too Many Requests

4. Rate limit key:
   - Authenticated users: Limit per Firebase uid
   - Unauthenticated: Limit per IP address

5. Reset:
   - Rate limit window: 1 minute (rolling)
   - In-memory storage (clears on server restart)
    """)


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRODUCTION SAFEGUARDS TEST SUITE")
    print("="*60)
    
    test_timeout()
    test_retry()
    test_combined()
    test_rate_limiting_info()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nNote: Rate limiting requires manual testing with running server.")
    print("See TEST 4 output for instructions.\n")
