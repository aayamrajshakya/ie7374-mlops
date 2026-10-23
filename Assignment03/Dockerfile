# slim gives a smaller footprint version containing only core reqs
# apache/airflow:latest for newest stable prod img
FROM apache/airflow:slim-latest

# switch to root to install packages into system Python
USER root

# install uv by copying the binary from official distroless docker img
# https://docs.astral.sh/uv/guides/integration/docker/#available-images
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# copy project files
COPY pyproject.toml uv.lock ./

# install dependencies as root into system environment
## --frozen: strictly enforces using the exact versions in uv.lock
## --no-dev: excludes development deps (linters, debuggers, formatters)
RUN uv pip install --system --no-cache -r <(uv export --frozen --no-dev)

# switch back to airflow user for security and runtime
USER airflow
