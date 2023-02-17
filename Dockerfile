FROM python:latest
COPY app /app
COPY requirements.txt .
RUN apt update
RUN apt install -y ffmpeg
RUN pip install -r requirements.txt

EXPOSE 8501
VOLUME /data
CMD streamlit run /app/01_🏠_Home.py
