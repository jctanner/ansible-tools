# IOS simulator

## Building

Copy the sources to your docker host and build the container:

	# docker build --rm -t <username>/cisco-ios .

## Running

```shell
ansible-playbook -v -i inventory -e "total_nodes=10" build_network.yml
```

```yaml
# build_network.yml
- hosts: localhost
  gather_facts: False
  vars:
      container_image: jctanner:cisco-ios
      container_ssh_password: redhat1234
  tasks:
      - debug: var=total_nodes
      - name: run the containers
        docker_container:
            name: "{{ item }}"
            image: "{{ container_image }}"
            state: started
        with_sequence: start=0 end={{ total_nodes|default('100') }} format=switch_%02x
```
