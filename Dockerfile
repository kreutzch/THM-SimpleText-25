FROM python:3.9.21-slim

RUN apt-get update && apt-get install -y \
	git \
	openjdk-17-jdk \
    	build-essential \
	zlib1g-dev \
	curl \
    	&& rm -rf /var/lib/apt/lists/*

# Set Java path for PyTerrier
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="$JAVA_HOME/bin:$PATH"
ENV JVM_PATH=$JAVA_HOME/lib/server/libjvm.so

WORKDIR /workspace
ADD . /workspace

RUN pip install --upgrade pip
RUN pip install -U pip setuptools wheel
RUN pip install -r requirements
RUN pip install -U git+https://github.com/terrier-org/pyterrier.git#egg=python-terrier
RUN pip install -U git+https://github.com/feralvam/easse.git
RUN pip install -q google-generativeai


