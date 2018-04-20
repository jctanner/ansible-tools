# https://github.com/fedora-cloud/Fedora-Dockerfiles/blob/master/systemd/systemd/Dockerfile

#FROM docker.io/fedora
FROM fedora:rawhide
MAINTAINER http://fedoraproject.org/wiki/Cloud

# Atomic RUN label, enables the atomic cli
LABEL RUN='docker run --name ssh -d -p 2200:22 $IMAGE'

EXPOSE 22

RUN dnf -y install systemd && dnf clean all && \
(cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;


RUN dnf -y install openssh-server
RUN dnf -y install openssh-clients
RUN systemctl enable sshd
RUN dnf -y install rsyslog 
RUN systemctl enable rsyslog

RUN dnf -y install passwd
RUN dnf -y install iproute
RUN dnf -y install procps-ng
RUN dnf -y install which
RUN dnf -y install python2
RUN dnf -y install snoopy
RUN dnf -y install net-tools
RUN dnf -y install bind-utils
RUN dnf -y install iproute

RUN echo "root:redhat1234" | chpasswd
RUN useradd cisco
RUN echo "cisco:redhat1234" | chpasswd
COPY bashrc /home/cisco/.bashrc
RUN chown -R cisco:cisco /home/cisco
COPY home.cisco.bin /home/cisco/bin
RUN chmod +x /home/cisco/bin/*
RUN chown -R cisco:cisco /home/cisco/bin

COPY snoopy.ini /etc/snoopy.ini
RUN /usr/sbin/snoopy-enable

#COPY entrypoint.sh /entrypoint.sh
#ENTRYPOINT ["/entrypoint.sh"]
#ENV LD_PRELOAD=/usr/lib64/libsnoopy.so
#CMD ["/usr/sbin/sshd", "-D"]

CMD rm -f /var/run/nologin
VOLUME [ "/sys/fs/cgroup", "/tmp", "/run" ]
CMD ["/usr/sbin/init"]
