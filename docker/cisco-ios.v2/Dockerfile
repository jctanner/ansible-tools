# https://github.com/fedora-cloud/Fedora-Dockerfiles/blob/master/systemd/systemd/Dockerfile

#FROM docker.io/fedora
FROM rastasheep/ubuntu-sshd:18.04

RUN useradd cisco
RUN usermod --shell /bin/bash cisco
RUN echo "cisco:redhat1234" | chpasswd
COPY bashrc /home/cisco/.bashrc
COPY bashrc /home/cisco/.bash_profile
COPY home.cisco.bin /home/cisco/bin
RUN chmod +x /home/cisco/bin/*
RUN chown -R cisco:cisco /home/cisco
RUN ln -s /usr/bin/python3 /home/cisco/bin/python
