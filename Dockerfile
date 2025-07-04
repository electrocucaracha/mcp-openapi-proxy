FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app/

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable && uvx pex -o mcp-proxy -c mcp-proxy --sh-boot --include-tools .

FROM python:3.12-slim

COPY --from=builder /app/mcp-proxy /opt/mcp-proxy

EXPOSE 8000

ENV OPENAPI_SPEC_URL=http://localhost:8080/openapi.json
ENV TRANSPORT=streamable-http
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PEX_TOOLS=1

ENTRYPOINT ["/opt/mcp-proxy"]
