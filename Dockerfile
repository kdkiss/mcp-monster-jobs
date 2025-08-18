FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y git
RUN pip install -r requirements.txt

CMD ["uvicorn", "monster_server:mcp", "--host", "0.0.0.0", "--port", "8000"]
