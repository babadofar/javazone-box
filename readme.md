#Fabric provisioned vagrant box with Ubuntu 15.4, Elasticsearch 2.0 beta 1 debian and Kibana from source.

Requires fabric
```
pip install fabric
```

To provision Vagrant dev image:

`fab vagrant provision_server`

You need to do a few manual steps to kick off everything.
Log on to the box and install nvm and stuf

    vagrant ssh
    sudo service elasticsearch start
    cd kibana
    nvm install $(cat .node-version)
    bin/kibana --dev
