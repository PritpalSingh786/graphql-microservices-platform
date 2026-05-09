import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class SimpleMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        logger.info(f"Auth Service - Request: {request.method} {request.path}")
        
        if 'HTTP_X_USER_ID' in request.META:
            request.gateway_user_id = request.META['HTTP_X_USER_ID']
        
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f"Auth Service - Response: {response.status_code} - Duration: {duration:.2f}s")
        
        return response