FROM python:3.12-slim AS base

WORKDIR /app

ARG APP_DIR=app1-recipes

# Install shared module
COPY shared/ ./shared/
RUN pip install --no-cache-dir ./shared

# Install app dependencies
COPY ${APP_DIR}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ${APP_DIR}/ ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
