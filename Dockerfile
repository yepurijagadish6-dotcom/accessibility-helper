# Stage 5: container image for the Accessibility Helper API
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The history database will be stored here (mount a volume to keep it)
ENV A11Y_DB=/app/data/a11y_history.db
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
