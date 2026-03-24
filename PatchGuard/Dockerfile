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

# Create non-root user with home directory
RUN groupadd -r patchguard && useradd -r -m -g patchguard patchguard

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

# Default command
CMD ["python", "-m", "patchguard"]