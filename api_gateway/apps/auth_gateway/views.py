import socket
import json
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class AuthGraphQLProxyView(View):
    def dispatch(self, request, *args, **kwargs):
        AUTH_HOST = 'auth_service' 
        # AUTH_HOST = '172.20.0.7'  # Fixed IP
        AUTH_PORT = 8001

        body = request.body.decode('utf-8') if request.body else ''
        auth_header = request.headers.get('Authorization', '')

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((AUTH_HOST, AUTH_PORT))
            
            http_request = (
                f"POST /graphql/ HTTP/1.1\r\n"
                f"Host: {AUTH_HOST}:{AUTH_PORT}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Authorization: {auth_header}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{body}"
            )
            sock.sendall(http_request.encode())

            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            sock.close()

            header_end = response.find(b'\r\n\r\n')
            response_body = response[header_end + 4:]

            try:
                data = json.loads(response_body.decode('utf-8'))
                return JsonResponse(data, safe=False)
            except:
                return HttpResponse(response_body, content_type='application/json')

        except Exception as e:
            print(f"❌ Error: {e}")
            return JsonResponse(
                {'errors': [{'message': f'Auth service unavailable: {str(e)}'}]},
                status=503
            )