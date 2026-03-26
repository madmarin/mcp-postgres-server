FROM python:3.12-slim

WORKDIR /app

# Copy only what's needed to install the package
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

ENTRYPOINT ["mcp-postgres-server"]
