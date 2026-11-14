FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535
WORKDIR /app
COPY --chown=65534:65534 . .
RUN pip install --no-build-isolation --no-cache-dir .
USER 65534:65534
ENTRYPOINT ["trajectoryforge"]
