"""
Request/Response logging middleware for transparent backend tracking.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import json
from utils.logger import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with full transparency."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log all details."""
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else "unknown"
        
        # Get user ID from token if available
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                # Extract token (Bearer <token>)
                token = auth_header.replace("Bearer ", "")
                # Try to decode user from token (simplified - in production use proper JWT decode)
                # For now, just mark as authenticated
                user_id = "authenticated"
            except:
                pass
        
        # Log request start - BIG and VISIBLE
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"🔵 INCOMING REQUEST: {method} {path}")
        logger.info(f"   IP: {client_ip} | User: {user_id or 'anonymous'}")
        if query_params:
            logger.info(f"   Query Params: {query_params}")
        
        # Log request body for POST/PUT/PATCH (if available)
        # Use a wrapper to read body without breaking the stream
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # Check content type
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Read body once
                    body_bytes = await request.body()
                    if body_bytes:
                        try:
                            body_json = json.loads(body_bytes.decode())
                            # Mask sensitive fields
                            if isinstance(body_json, dict):
                                masked_body = {k: "***" if k.lower() in ["password", "token", "secret", "key"] else v 
                                             for k, v in body_json.items()}
                                logger.info(f"   Request Body: {json.dumps(masked_body, indent=2)}")
                            else:
                                logger.info(f"   Request Body: {str(body_json)[:200]}...")
                        except json.JSONDecodeError:
                            body_preview = body_bytes.decode()[:200] if body_bytes else ""
                            logger.info(f"   Request Body (raw): {body_preview}...")
                        except Exception:
                            logger.info(f"   Request Body: <binary or unreadable>")
                        
                        # Restore body for FastAPI to read
                        async def receive():
                            return {"type": "http.request", "body": body_bytes}
                        request._receive = receive
            except Exception as e:
                logger.debug(f"   Could not read request body: {str(e)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response - BIG and VISIBLE
            status_code = response.status_code
            if 200 <= status_code < 300:
                status_emoji = "✅"
                status_color = "SUCCESS"
            elif 300 <= status_code < 400:
                status_emoji = "⚠️"
                status_color = "REDIRECT"
            else:
                status_emoji = "❌"
                status_color = "ERROR"
            
            logger.info(f"🟢 OUTGOING RESPONSE: {method} {path}")
            logger.info(f"   Status: {status_code} {status_emoji} ({status_color})")
            logger.info(f"   Duration: {duration_ms:.2f}ms")
            logger.info(f"   User: {user_id or 'anonymous'}")
            
            # Try to log response body for small responses
            try:
                # Only log response body for small JSON responses
                if hasattr(response, 'body') and status_code < 400:
                    # Response body is a generator, we can't easily read it without breaking things
                    # So we'll skip response body logging for now
                    pass
            except:
                pass
            
            # Log error details if status >= 400
            if status_code >= 400:
                logger.warning("")
                logger.warning("=" * 80)
                logger.warning(f"⚠️ ERROR RESPONSE: {method} {path}")
                logger.warning(f"   Status: {status_code}")
                logger.warning(f"   Duration: {duration_ms:.2f}ms")
                logger.warning("=" * 80)
            
            logger.info("=" * 80)
            logger.info("")
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            
            # Log exception with full context - BIG and VISIBLE
            logger.error("")
            logger.error("=" * 80)
            logger.error(f"❌ REQUEST EXCEPTION: {method} {path}")
            logger.error(f"   Error Type: {type(e).__name__}")
            logger.error(f"   Error Message: {str(e)}")
            logger.error(f"   Duration: {duration_ms:.2f}ms")
            logger.error(f"   User: {user_id or 'anonymous'}")
            logger.error("=" * 80)
            logger.error("", exc_info=True)  # Stack trace
            logger.error("=" * 80)
            logger.error("")
            
            # Re-raise to let FastAPI handle it
            raise

