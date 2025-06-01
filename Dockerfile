FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app

WORKDIR /app
RUN uv sync --frozen --no-cache

EXPOSE 8000

ENV OPENAPI_SPEC_URL=http://localhost:8080/openapi.json

ENTRYPOINT ["/app/.venv/bin/mcp-proxy"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
