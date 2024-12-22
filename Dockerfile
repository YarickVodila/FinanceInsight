FROM python:3.10.16-slim
WORKDIR /app

COPY . ./

RUN --mount=type=cache,target=/root/.cache \
    pip install --upgrade pip \ 
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
RUN chmod +x apps/entrypoint.sh

ENTRYPOINT ["apps/entrypoint.sh"]
