# Creates an image with the required set up for Fish Plays Pokémon to run.
FROM phusion/baseimage:0.9.15
MAINTAINER Patrick Facheris <plfacheris@gmail.com>
ENV HOME /root
ENV DISPLAY :0

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN apt-get -qq update

# Update Repository Listings
RUN apt-add-repository multiverse && add-apt-repository ppa:jon-severinsson/ffmpeg && apt-get -qq update && apt-get -qq -y install \
    git \
    wget \
    ffmpeg \
    xvfb \
    pulseaudio \
    xdotool \
    python python-dev python-distribute python-pip \
    build-essential pkg-config libasound2-dev libcdio-dev libsdl1.2-dev libsdl-net1.2-dev libsndfile1-dev zlib1g-dev


# Install OpenCV
WORKDIR /tmp
RUN git clone https://github.com/jayrambhia/Install-OpenCV.git && chmod +x /tmp/Install-OpenCV/*/*.sh
WORKDIR /tmp/Install-OpenCV/Ubuntu
RUN /bin/bash ./opencv_latest.sh
WORKDIR /
RUN apt-get -qq -y install ffmpeg

# Configure XVFB
ADD environment/xvfb.sh /etc/init.d/xvfb
RUN chmod +x /etc/init.d/xvfb

# Install Mednafen
RUN wget -q -O mednafen.tar.bz2 http://downloads.sourceforge.net/project/mednafen/Mednafen/0.9.38.2/mednafen-0.9.38.2.tar.bz2?r=http%3A%2F%2Fmednafen.sourceforge.net%2Freleases%2F&ts=1424804576&use_mirror=iweb && \
    tar vxfj mednafen.tar.bz2 && rm mednafen.tar.bz2 && \
    cd mednafen && sed -i '1242iprintf("gb_mem:%04x:%02x\\n");' ./src/gb/gb.cpp && \
    ./configure && make && sudo make install

# Copy Application Files
RUN mkdir /whereisthefish
COPY . /whereisthefish/

# Install Python Requirements
WORKDIR /whereisthefish
RUN pip install -r requirements.txt

# Clean Unused
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
