import socket
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class BlogGraphQLProxyView(View):
    def dispatch(self, request, *args, **kwargs):
        # BLOG_HOST = '172.20.0.9'
        BLOG_HOST = 'blog_service'
        BLOG_PORT = 8002

        # Get original request body as is (don't parse)
        body = request.body
        content_type = request.headers.get('Content-Type', '')
        auth_header = request.headers.get('Authorization', '')

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((BLOG_HOST, BLOG_PORT))
            
            # Forward the request EXACTLY as received
            http_request = (
                f"POST /graphql/ HTTP/1.1\r\n"
                f"Host: {BLOG_HOST}:{BLOG_PORT}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Authorization: {auth_header}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )
            # Send headers + body
            sock.sendall(http_request.encode() + body)

            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            sock.close()

            header_end = response.find(b'\r\n\r\n')
            response_body = response[header_end + 4:]

            return HttpResponse(response_body, content_type='application/json')

        except Exception as e:
            print(f"❌ Error: {e}")
            return HttpResponse(
                b'{"errors":[{"message":"Blog service unavailable: ' + str(e).encode() + b'"}]}',
                status=503,
                content_type='application/json'
            )