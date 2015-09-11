#Fabric provisioned vagrant box with Ubuntu 15.4, Elasticsearch 2.0 beta 1 debian and Kibana from source.

Requires fabric, vagrant and virtualbox. Install and download vagrant and virtualbox, and python.  Recommended Anaconda Python from here http://continuum.io/downloads
After installing python, vagrant and virtualbox, open a terminal and install fabric like this
```
pip install fabric
```

Now provision Vagrant box:

    vagrant up
    fab vagrant provision_server

You need to do a few manual steps to kick off everything.
Log on to the box like this:

    vagrant ssh

Start up elasticsearch

    sudo service elasticsearch start

Run script for downloading Vinmonopolet data

    sh getProdukter.sh

Run Logstash 

    /opt/logstash/bin/logstash agent --verbose -f vinMonopoletCsvFileLogstash.conf

It should take a couple of minutes, stop it afterwards.


Start up Kibana

    sh start_kibana.sh

This will start Kibana running in the foreground. 


To make Kibana use the vinmopolet index do:

* Create new index pattern (this will be the Kibana start screen on first use)
* Unselect the checkbox "Index contains time-based events"
* type in "vinmonopolet" for index name
* ENTER and you should see some 15 000-ish hits on the Discovery tab.
