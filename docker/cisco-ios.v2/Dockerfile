# https://github.com/fedora-cloud/Fedora-Dockerfiles/blob/master/systemd/systemd/Dockerfile

#FROM docker.io/fedora
FROM rastasheep/ubuntu-sshd:18.04

RUN useradd cisco
RUN echo "cisco:redhat1234" | chpasswd
COPY bashrc /home/cisco/.bashrc
RUN chown -R cisco:cisco /home/cisco
COPY home.cisco.bin /home/cisco/bin
RUN chmod +x /home/cisco/bin/*
RUN chown -R cisco:cisco /home/cisco/bin
