FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ORVILLE_API_HOST=0.0.0.0
ENV ORVILLE_API_PORT=8787
ENV ORVILLE_STORAGE=sqlite
ENV ORVILLE_DB_PATH=/var/lib/orville/orville.db
WORKDIR /app
COPY pyproject.toml README.md ./
COPY orville_core ./orville_core
RUN python -m pip install --no-cache-dir --upgrade pip && python -m pip install --no-cache-dir ".[api,security]" && useradd --create-home --uid 10001 --shell /usr/sbin/nologin orville && mkdir -p /var/lib/orville && chown -R orville:orville /app /var/lib/orville
USER orville
EXPOSE 8787
CMD ["orville-api"]
