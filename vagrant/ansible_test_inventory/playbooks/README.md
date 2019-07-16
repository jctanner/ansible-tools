tower-cli inventory create -n containers --organization=Default
tower-cli inventory_script create -n docker_script --script=@makeinv.py --organization=Default
tower-cli inventory_source create --name="containers_source" --source-script="docker_script" --inventory="containers" --source="custom"                                                                                                                                  
tower-cli inventory_source update "containers_source" --monitor
tower-cli host list --inventory="containers"
