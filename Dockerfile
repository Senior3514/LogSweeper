FROM python:3.12-slim AS backend

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/logsweeper/ ./logsweeper/
COPY config/ ./config/

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "logsweeper.app:app"]

# ---

FROM node:20-alpine AS ui-build

WORKDIR /app
COPY src/ui/package.json src/ui/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install --ignore-scripts
COPY src/ui/ .
RUN npm run build

# ---

FROM nginx:alpine AS ui

COPY --from=ui-build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
