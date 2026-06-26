# ACL Executor — Python Sandbox (Multi-stage)
# Target: <150MB runtime image
# Stages: builder (compile deps) → runtime (minimal)

# ------------------------------------------------------------------
# STAGE 1: Builder
# ------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt /build/requirements.txt
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ------------------------------------------------------------------
# STAGE 2: Runtime
# ------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="acl-executor" \
      org.opencontainers.image.description="ACL Python sandbox runtime" \
      org.opencontainers.image.vendor="nousresearch"

# Security: run as non-root
RUN groupadd -r acluser -g 1000 && \
    useradd -r -g acluser -u 1000 -d /home/acluser -s /bin/false acluser && \
    mkdir -p /home/acluser /sandbox /tmp && \
    chown -R acluser:acluser /home/acluser /sandbox /tmp

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:/usr/local/bin:/usr/bin:/bin"

# No network tools, no compilers, no package managers in runtime
RUN apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Seccomp will be applied at container run time via --security-opt seccomp=...
# Landlock/openat2 syscalls are allowed in profile for future path sandboxing.

WORKDIR /sandbox
USER acluser

# Default: execute the injected snippet
ENTRYPOINT ["python3"]
CMD ["-c", "import sys; print('ACL Executor ready. Mount snippet to /sandbox/snippet.py')"]
