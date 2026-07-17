FROM alpine:3.19
RUN apk add --no-cache python3 py3-pip
WORKDIR /app
COPY backend/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
