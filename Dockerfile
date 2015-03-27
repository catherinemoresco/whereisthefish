# Creates an image with the required set up for Fish Plays Pokémon to run.
FROM phusion/baseimage:0.9.15
MAINTAINER Patrick Facheris <plfacheris@gmail.com>
ENV HOME /root
ENV DISPLAY :0

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# Update Repository Listings
RUN apt-add-repository multiverse && apt-get -qq update && apt-get -qq -y install \
    git \
    zip \
    unzip \
    wget \
    xvfb \
    pulseaudio \
    xdotool \
    python python-dev python-distribute python-pip \
    build-essential pkg-config libasound2-dev libcdio-dev libsdl1.2-dev libsdl-net1.2-dev libsndfile1-dev zlib1g-dev \
    libtiff5-dev libjpeg8-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk && \
    apt-get -qq -y clean


# Install OpenCV
WORKDIR /tmp
RUN git clone https://github.com/jayrambhia/Install-OpenCV.git && chmod +x /tmp/Install-OpenCV/*/*.sh
WORKDIR /tmp/Install-OpenCV/Ubuntu
RUN /bin/bash ./2.4/opencv2_4_9.sh
WORKDIR /

# Install FFMPEG
RUN add-apt-repository ppa:jon-severinsson/ffmpeg && apt-get -qq update && apt-get -qq -y install \
    ffmpeg && apt-get -qq -y clean

# Configure XVFB
RUN mkdir /etc/service/xvfb
ADD environment/xvfb.sh /etc/service/xvfb/run
RUN chmod +x /etc/service/xvfb/run

# Configure PulseAudio
RUN mkdir /etc/service/pulseaudio
ADD environment/pulseaudio.sh /etc/service/pulseaudio/run
RUN chmod +x /etc/service/pulseaudio/run

# Install Gambatte
WORKDIR /tmp
ADD environment/gambatte gambatte
WORKDIR /tmp/gambatte
RUN pip install --egg SCons
RUN ./build_sdl.sh
WORKDIR /
RUN mv /tmp/gambatte/gambatte_sdl/gambatte_sdl /usr/bin/gambatte

# Copy Application Files
RUN mkdir /whereisthefish
COPY . /whereisthefish/

# Install Python Requirements
WORKDIR /whereisthefish
RUN pip install -r requirements.txt

# Clean Unused
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
