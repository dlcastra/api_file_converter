ARG PYTHON_VERSION=3.13.0
FROM python:${PYTHON_VERSION} as base

ENV DOCKERIZED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/usr/lib/libreoffice/program

# Install required libraries and build tools
RUN apt-get update \
    && apt-get install -y \
        libreoffice \
        python3-uno \
        supervisor \
        unoconv \
        net-tools \
        g++ \
        make \
        libpoppler-cpp-dev \
        libopencv-dev \
        imagemagick \
        libmagickwand-dev \
        libmagickcore-dev \
        libmagick++-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV UNO_PATH="/usr/lib/libreoffice/program"
ENV PYTHONPATH="/usr/lib/python3/dist-packages"

# Create a new user for the application
RUN useradd -ms /bin/bash admin
WORKDIR /usr/src/service
RUN mkdir -p uploads converted && chown -R admin:admin /usr/src/service

# Copy the source code and requirements file into the container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the cpp source code and other necessary files
COPY . .

# Compile the C++ file (convert_pdf.cpp)
# Створення директорії перед компіляцією
RUN mkdir -p /usr/src/app/services \
    && g++ convert_pdf.cpp -o /usr/src/app/services/pdf2smth \
    $(pkg-config --cflags --libs Magick++) \
    -I/usr/include/poppler/cpp \
    -I/usr/include/opencv4 \
    -L/usr/lib/x86_64-linux-gnu \
    -lpoppler-cpp \
    -std=c++11




COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN chmod +x /usr/bin/unoconv

# Expose the port that the application listens on.
EXPOSE 8080 2002

# Run the application using supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
