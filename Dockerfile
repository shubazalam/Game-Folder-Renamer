FROM python:3.11-slim

WORKDIR /app

# Install dos2unix for line ending fixes
RUN apt-get update && apt-get install -y dos2unix && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY game_renamer.py .
COPY rename_games.py .
COPY entrypoint.sh .

# Fix line endings and make script executable
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Run the interactive entrypoint
ENTRYPOINT ["./entrypoint.sh"] 