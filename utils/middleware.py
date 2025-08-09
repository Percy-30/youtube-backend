# utils/middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict, deque
import re

from config import Config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter avanzado con ventanas deslizantes"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Verifica si la IP puede hacer más requests"""
        current_time = time.time()
        
        # Verificar si la IP está bloqueada temporalmente
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return False
            else:
                del self.blocked_ips[client_ip]
        
        # Limpiar requests antiguos (ventana de 1 minuto)
        while (self.requests[client_ip] and 
               current_time - self.requests[client_ip][0] > 60):
            self.requests[client_ip].popleft()
        
        # Verificar límite por minuto
        if len(self.requests[client_ip]) >= Config.MAX_REQUESTS_PER_MINUTE:
            # Bloquear por 5 minutos si excede mucho el límite
            if len(self.requests[client_ip]) > Config.MAX_REQUESTS_PER_MINUTE * 1.5:
                self.blocked_ips[client_ip] = current_time + 300  # 5 minutos
                logger.warning(f"IP {client_ip} bloqueada por 5 minutos por exceso de requests")
            return False
        
        # Registrar el request
        self.requests[client_ip].append(current_time)
        return True
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del rate limiter"""
        current_time = time.time()
        active_ips = len([ip for ip, reqs in self.requests.items() if reqs])
        blocked_ips = len([ip for ip, block_time in self.blocked_ips.items() if current_time < block_time])
        
        return {
            "active_ips": active_ips,
            "blocked_ips": blocked_ips,
            "total_requests_last_minute": sum(len(reqs) for reqs in self.requests.values())
        }

class SecurityValidator:
    """Validador de seguridad para URLs y requests"""
    
    BLOCKED_DOMAINS = [
        'localhost', '127.0.0.1', '0.0.0.0',
        '192.168.', '10.', '172.16.', '172.17.',
        '172.18.', '172.19.', '172.20.', '172.21.',
        '172.22.', '172.23.', '172.24.', '172.25.',
        '172.26.', '172.27.', '172.28.', '172.29.',
        '172.30.', '172.31.'
    ]
    
    SUSPICIOUS_PATTERNS = [
        r'file://', r'ftp://', r'data:',
        r'javascript:', r'vbscript:',
        r'\.\./.*\.\./.*',  # Path traversal
        r'<script.*>.*</script>',  # XSS básico
    ]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Valida que la URL sea segura"""
        if not url or not isinstance(url, str):
            return False
        
        url_lower = url.lower()
        
        # Verificar dominios bloqueados
        for blocked in cls.BLOCKED_DOMAINS:
            if blocked in url_lower:
                logger.warning(f"URL bloqueada por dominio: {url}")
                return False
        
        # Verificar patrones sospechosos
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, url_lower):
                logger.warning(f"URL bloqueada por patrón sospechoso: {url}")
                return False
        
        # Verificar que sea una URL de YouTube válida
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/playlist\?list=',
            r'youtube\.com/channel/',
            r'youtube\.com/user/',
            r'youtube\.com/c/'
        ]
        
        if not any(re.search(pattern, url_lower) for pattern in youtube_patterns):
            logger.warning(f"URL no es de YouTube: {url}")
            return False
        
        return True
    
    @classmethod
    def validate_query(cls, query: str) -> bool:
        """Valida que el query de búsqueda sea seguro"""
        if not query or len(query) > 200:
            return False
        
        # Verificar patrones sospechosos en queries
        suspicious_in_query = [
            r'<script.*>.*</script>',
            r'javascript:',
            r'data:',
            r'file://'
        ]
        
        query_lower = query.lower()
        for pattern in suspicious_in_query:
            if re.search(pattern, query_lower):
                return False
        
        return True

class RequestMonitor:
    """Monitor de requests para análisis y debugging"""
    
    def __init__(self):
        self.request_log = deque(maxlen=1000)  # Últimos 1000 requests
        self.error_count = defaultdict(int)
        self.response_times = deque(maxlen=100)  # Últimos 100 tiempos
    
    def log_request(self, request: Request, response_time: float, status_code: int):
        """Registra un request"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host,
            'user_agent': request.headers.get('user-agent', ''),
            'response_time': response_time,
            'status_code': status_code
        }
        
        self.request_log.append(log_entry)
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_count[status_code] += 1
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de monitoring"""
        if not self.response_times:
            avg_response_time = 0
        else:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        return {
            'total_requests': len(self.request_log),
            'avg_response_time': round(avg_response_time, 3),
            'error_counts': dict(self.error_count),
            'requests_last_hour': len([
                r for r in self.request_log 
                if (datetime.now() - datetime.fromisoformat(r['timestamp'])).seconds < 3600
            ])
        }

# Instancias globales
rate_limiter = RateLimiter()
request_monitor = RequestMonitor()

async def security_middleware(request: Request, call_next):
    """Middleware de seguridad"""
    start_time = time.time()
    
    # Verificar rate limiting
    if Config.ENABLE_RATE_LIMITING:
        if not rate_limiter.is_allowed(request.client.host):
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "error": f"Maximum {Config.MAX_REQUESTS_PER_MINUTE} requests per minute",
                    "retry_after": 60,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Validar parámetros de URL si contiene 'url'
    if hasattr(request, 'query_params') and 'url' in request.query_params:
        url_param = request.query_params['url']
        if not SecurityValidator.validate_url(url_param):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Invalid URL",
                    "error": "The provided URL is not valid or not supported",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Validar query de búsqueda si existe
    if hasattr(request, 'query_params') and 'q' in request.query_params:
        query_param = request.query_params['q']
        if not SecurityValidator.validate_query(query_param):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Invalid search query",
                    "error": "The search query contains invalid characters",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    # Procesar request
    try:
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Agregar headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Process-Time"] = str(round(response_time, 4))
        response.headers["X-API-Version"] = "2.0.0"
        response.headers["X-RateLimit-Remaining"] = str(max(0, 
            Config.MAX_REQUESTS_PER_MINUTE - len(rate_limiter.requests[request.client.host])
        ))
        
        # Registrar en monitor
        request_monitor.log_request(request, response_time, response.status_code)
        
        return response
        
    except Exception as e:
        response_time = time.time() - start_time
        request_monitor.log_request(request, response_time, 500)
        logger.error(f"Error en middleware: {e}")
        raise

# Funciones de utilidad para exportar
def get_rate_limiter_stats():
    return rate_limiter.get_stats()

def get_monitor_stats():
    return request_monitor.get_stats()