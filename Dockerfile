FROM python:3
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    git \
    cmake \
    && rm -Rf /var/lib/apt/lists/*
RUN git clone https://gitlab.matrix.org/matrix-org/olm.git \
    && cd olm \
    && cmake . -Bbuild -DCMAKE_INSTALL_PREFIX=/usr \
    && cmake --build build --target install
WORKDIR /usr/src/app
COPY setup.py ./
COPY bot/ ./bot/
RUN pip install --no-cache-dir ./
CMD ["bot"]
