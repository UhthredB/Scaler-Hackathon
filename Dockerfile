FROM python:3.11-slim

# Create user with ID 1000 (required by HF Spaces)
RUN useradd -m -u 1000 user

# Set environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory
WORKDIR $HOME/app

# Copy and install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy environment code with proper ownership
COPY --chown=user . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER user

# Expose port (HF Spaces requires 7860)
EXPOSE 7860

# Run server (HF Spaces sets PORT env var)
CMD ["./entrypoint.sh"]
