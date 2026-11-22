FROM python:3.13-slim

WORKDIR /app

RUN python -m pip install --upgrade pip \
    && python -m pip install "ruff>=0.5,<1" "mypy>=1.8,<2"

# Keep the workspace clean: don't write __pycache__ anywhere
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["bash"]
