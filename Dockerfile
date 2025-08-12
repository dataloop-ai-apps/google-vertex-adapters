FROM docker.io/dataloopai/dtlpy-agent:cpu.py3.10.opencv

USER 1000
COPY requirements.txt /tmp/
WORKDIR /tmp
ENV HOME=/tmp
RUN pip install --user -r /tmp/requirements.txt

# docker build -t gcr.io/viewo-g/piper/agent/runner/apps/google-vertex-adapters:0.1.1 .
# docker push gcr.io/viewo-g/piper/agent/runner/apps/google-vertex-adapters:0.1.1