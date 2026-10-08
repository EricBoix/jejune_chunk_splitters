FROM python:3.10-buster

RUN set -ex \
    && git clone https://github.com/EricBoix/jejune_chunk_splitters.git \
    # Rename archive for clear context when debugging/fixing in container
    && mv jejune_chunk_splitters/ jejune_chunk_splitters.git

WORKDIR /jejune_chunk_splitters.git
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3"]
