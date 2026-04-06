FROM postgres:16

RUN apt-get update && apt-get install -y \
    postgresql-server-dev-16 \
    gcc \
    make \
    git \
    && git clone --branch v0.8.2 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make \
    && make install \
    && rm -rf /tmp/pgvector \
    && apt-get remove -y gcc make git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/init.sql