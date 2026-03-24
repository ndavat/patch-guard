# Multi-stage Docker build for PatchGuard

# Builder stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy source code
COPY patchguard/ ./patchguard/
COPY tests/ ./tests/

# Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r patchguard && useradd -r -g patchguard patchguard

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/patchguard/.local

# Set working directory
WORKDIR /app

# Copy source code
COPY patchguard/ ./patchguard/
COPY tests/ ./tests/

# Change ownership to non-root user
RUN chown -R patchguard:patchguard /app

# Switch to non-root user
USER patchguard

# Add user's local bin to PATH
ENV PATH=/home/patchguard/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=2)" || exit 1

# Expose ports
EXPOSE 8080 8081

# Default command
CMD ["python", "-m", "patchguard"]