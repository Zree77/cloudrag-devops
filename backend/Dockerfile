FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Remove pip's bundled third-party SBOM.
# The SBOM contains outdated versions of packages installed separately
# in this image and can cause inaccurate vulnerability findings.
RUN rm -f /usr/local/lib/python3.12/site-packages/pip/_vendor/bom.cdx.json

COPY backend/app/ /app/app/

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]