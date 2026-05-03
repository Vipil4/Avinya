FROM python:3.11-slim
WORKDIR /app
COPY avinya_server.py .
EXPOSE 3000
CMD ["python", "avinya_server.py"]
