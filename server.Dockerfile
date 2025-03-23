# Use a CUDA image that includes cuDNN
FROM python:3.13.2-alpine3.21
ARG DEBIAN_FRONTEND=noninteractive

EXPOSE 3000

WORKDIR /app

COPY ./server/requirements.txt ./requirements.txt

RUN python3 -m pip install --no-cache-dir -r ./requirements.txt

COPY ./server ./server
COPY ./shared ./shared
COPY ./run_server.py ./run_server.py

# Set unbuffered output for Python, facilitating real-time log output
CMD ["python3", "-u", "./run_server.py"]
