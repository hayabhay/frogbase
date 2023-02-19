# Currently tested & workong for Python 3.11
FROM python:3.11-slim

# Run updates and install ffmpeg
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ffmpeg

# Copy the current directory contents into the container at /app
COPY app /app

# Copy and install the requirements
COPY ./requirements.txt /requirements.txt

# Pip install the dependencies
RUN pip install --upgrade pip
# For CPU only, you can use pip install git+https://github.com/MiscellaneousStuff/whisper.git
# in place of openai-whisper.
# Also, --extra-index-url https://download.pytorch.org/whl/cpu might be needed if you are using a CPU only machine
RUN pip install --no-cache-dir -r /requirements.txt

# Set the working directory to /app
WORKDIR /app

# Expose port 8501
EXPOSE 8501

# Mount the data volume
VOLUME /data

# Run the app
CMD streamlit run /app/01_🏠_Home.py
