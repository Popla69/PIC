# Multi-stage build for PIC v1
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy source files
COPY pyproject.toml setup.py MANIFEST.in README.md requirements.txt ./
COPY src/ ./src/

# Build wheel
RUN python -m build --wheel

# Final stage
FROM python:3.9-slim

# Create non-root user
RUN useradd -m -u 1000 pic && \
    mkdir -p /var/lib/pic /var/log/pic && \
    chown -R pic:pic /var/lib/pic /var/log/pic

# Set working directory
WORKDIR /app

# Copy wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install PIC
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm /tmp/*.whl

# Switch to non-root user
USER pic

# Expose API port
EXPOSE 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8443/health')" || exit 1

# Default command
CMD ["pic", "start"]
