FROM selenium/standalone-chrome:98.0-20250303

USER root

RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py scraper.py ./

CMD ["python3", "bot.py"]
