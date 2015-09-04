import sys
import os

from fabric.context_managers import cd

from fabric.contrib.console import confirm
from fabric.network import disconnect_all
from fabric.operations import sudo, run, put, local
from fabric.state import env
from fabric.utils import error



def provision_server():
    sudo('apt-get update -qq -y > /dev/null')
    install_debian_packages(['screen', 'unzip'])
    install_elasticsearch()
    install_kibana()
    install_logstash()
    put('provision/logstash/', 'logstash/')
    run('logstash/getProdukter.sh')
    run('/opt/logstash/bin/logstash agent -f logstash/vinMonopoletCsvFileLogstash.conf')


def restart_server():
    sudo('shutdown -r now')


def package_installed(pkg):
    r = run("dpkg-query -W -f='${Status}' %s 2>/dev/null | grep -c \"ok installed\"" % pkg, quiet=True)

    if getattr(r, 'return_code') != 0:
        return False

    return True


def install_java():
    if not package_installed('default-jre'):
        sudo('apt-get install -y -qq  openjdk-8-jdk')


def install_elasticsearch():
    install_java()

    if not package_installed('elasticsearch'):
        run('wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -')
        run('wget -q http://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.0.0-beta1/elasticsearch-2.0.0-beta1.deb')
        #run('echo "deb http://packages.elastic.co/elasticsearch/1.5/debian stable main" | sudo tee -a /etc/apt/sources.list')
        sudo('apt-get update -qq -y > /dev/null')
        sudo('dpkg -i elasticsearch-2.0.0-beta1.deb')
        sudo ('apt-get -fy install')
        put('provision/elasticsearch.yml', '/etc/elasticsearch/elasticsearch.yml', use_sudo=True)
        #sudo('/usr/share/elasticsearch/bin/plugin -i elasticsearch/marvel/latest')
        sudo('update-rc.d elasticsearch defaults 95 10')
        sudo('service elasticsearch start')



def install_logstash():
    if not package_installed('logstash'):
        sudo('echo "deb http://packages.elasticsearch.org/logstash/1.5/debian stable main" | sudo tee -a /etc/apt/sources.list')
        sudo('apt-get update -qq -y > /dev/null')
        run('wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -')
        sudo('apt-get install logstash -yq')


def file_exists(fn):
    r = run('test -f %s' %fn, quiet=True)

    if getattr(r, 'return_code') != 0:
        return False

    return True

def install_kibana():
    if not file_exists('/home/vagrant/kibana/.node-version'):
        run('git clone https://github.com/elastic/kibana.git')
        run('curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.26.1/install.sh | bash')
        with cd('kibana'):
            run('. ~/.nvm/nvm.sh && nvm install "$(cat .node-version)"')
            run('npm install -g npm@3.2')
            run('. ~/.nvm/nvm.sh && npm install')


def vagrant():
    env.user = 'vagrant'
    env.hosts = ['127.0.0.1:2222']
    env.key_filename = '.vagrant/machines/default/virtualbox/private_key'
    env.disable_known_hosts = True


def install_python_packages():
    requirements = [req.strip() for req in open('requirements.txt').readlines()]

    sudo('pip install %s' % ' '.join(requirements))


def install_debian_packages(packages=None):
    if packages and isinstance(packages, basestring):
        packages = [p.strip() for p in packages.split(';')]

    if packages:
        sudo('apt-get install -qq -y %s' % ' '.join(packages))


def provision_data():
    with cd('twitter-analysis-lab'):
        sudo('PYTHONPATH=. python bin/provision_data.py')