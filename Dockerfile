FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
 && rm -rf /var/lib/apt/lists/*

ENV CMAKE_ARGS="-DGGML_AVX2=ON -DGGML_FMA=ON"
ENV FORCE_CMAKE=1

RUN pip install --no-cache-dir llama-cpp-python

WORKDIR /app
COPY . /app

CMD ["python", "app.py"]