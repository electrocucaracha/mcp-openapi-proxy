FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app

WORKDIR /app
RUN uv sync --frozen --no-cache

EXPOSE 8000

ENV OPENAPI_SPEC_URL=http://localhost:8080/openapi.json
ENV TRANSPORT=streamable-http
ENV HOST=0.0.0.0
ENV PORT=8000

ENTRYPOINT ["/app/.venv/bin/mcp-proxy"]