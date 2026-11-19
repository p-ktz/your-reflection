FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY launch_demo.py ./
COPY vendor ./vendor
COPY dist ./dist

# The launcher refreshes the QR SVG inside dist/assets when it starts.
RUN useradd --uid 10001 --create-home app && chown -R app:app /app/dist
USER app

EXPOSE 8765

ENTRYPOINT ["python", "launch_demo.py"]
CMD ["--no-browser", "--bind", "0.0.0.0", "--port", "8765"]
