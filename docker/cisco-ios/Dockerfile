FROM docker.io/fedora
MAINTAINER http://fedoraproject.org/wiki/Cloud

# Atomic RUN label, enables the atomic cli
LABEL RUN='docker run --name ssh -d -p 2200:22 $IMAGE'

EXPOSE 22

RUN dnf -y update && dnf -y install openssh-server passwd && dnf clean all
RUN dnf -y install procps-ng && dnf clean all
RUN dnf -y install which && dnf clean all
RUN dnf -y install python2 && dnf clean all
RUN dnf -y install snoopy && dnf clean all
#RUN dnf -y install rsync
#RUN dnf -y install ansible
#RUN rpm -e --nodeps ansible
#RUN dnf -y install python2-pip git
#RUN pip2 install git+https://github.com/ansible/ansible.git@devel
RUN echo "root:redhat1234" | chpasswd
RUN useradd cisco
RUN echo "cisco:redhat1234" | chpasswd
#RUN mkdir /home/cisco
COPY bashrc /home/cisco/.bashrc
RUN chown -R cisco:cisco /home/cisco
COPY home.cisco.bin /home/cisco/bin
RUN chmod +x /home/cisco/bin/*
RUN chown -R cisco:cisco /home/cisco/bin

COPY entrypoint.sh /entrypoint.sh
COPY snoopy.ini /etc/snoopy.ini
RUN /usr/sbin/snoopy-enable

ENTRYPOINT ["/entrypoint.sh"]
ENV LD_PRELOAD=/usr/lib64/libsnoopy.so
CMD ["/usr/sbin/sshd", "-D"]
