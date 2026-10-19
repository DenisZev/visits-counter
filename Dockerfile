FROM python:3.12-alpine
WORKDIR /app
RUN pip install redis
COPY backend.py .
EXPOSE 8000
CMD ["python", "backend.py"]
