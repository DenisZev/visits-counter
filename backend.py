import os
import json
import redis
from http.server import BaseHTTPRequestHandler, HTTPServer

# ─── Подключение к Redis ──────────────────────────────────────────────
# Хост и порт берём из переменных окружения. В docker-compose.yml
# мы зададим REDIS_HOST=redis — это имя сервиса в compose, Docker
# резолвит его в IP контейнера через встроенный DNS.
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

# Создаём клиент Redis. decode_responses=True — чтобы возвращалось
# строками, а не байтами.
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


# ─── Обработчик HTTP-запросов ─────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # GET /  → возвращаем текущее значение счётчика
        if self.path == "/":
            visits = r.get("visits") or 0
            self._send_json({"visits": int(visits)})
        else:
            self._send_404()

    def do_POST(self):
        # POST /increment  → увеличиваем счётчик на 1
        if self.path == "/increment":
            new_value = r.incr("visits")   # Redis сам увеличит и вернёт новое
            self._send_json({"visits": new_value})
        else:
            self._send_404()

    # ─── Вспомогательные методы ───────────────────────────────────────
    def _send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")

    # По умолчанию BaseHTTPRequestHandler логирует каждый запрос
    # в stderr с некрасивым форматом. Переопределяем — логи будут
    # видны в `docker compose logs backend`.
    def log_message(self, format, *args):
        print(f"[backend] {self.address_string()} - {format % args}", flush=True)


# ─── Запуск сервера ───────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[backend] Listening on port {port}", flush=True)
    server.serve_forever()
