import sys
import os

from fabric.context_managers import cd

from fabric.contrib.console import confirm
from fabric.network import disconnect_all
from fabric.operations import sudo, run, put, local
from fabric.state import env
from fabric.utils import error

ANACONDA_MD5 = 'c3100392685b5a62c8509c0588ce9376'
ANACONDA_URL = 'https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda-2.3.0-Linux-x86_64.sh'
ANACONDA_FN = 'Anaconda-2.3.0-Linux-x86_64.sh'
ANACONDA_INSTALL_PATH = '/opt/anaconda'

ESLIB_INSTALL_PATH = '/opt/eslib'


def provision_server():
    sudo('apt-get update -qq -y > /dev/null')
    install_debian_packages(['screen', 'unzip'])
    install_elasticsearch()
    install_kibana()


def restart_server():
    sudo('shutdown -r now')


def anaconda_downloaded():
    r = run('test -f %s' % ANACONDA_FN, quiet=True)

    if getattr(r, 'return_code') != 0:
        return False

    r = run('md5sum %s' % ANACONDA_FN)
    md5, _ = getattr(r, 'stdout').split()

    if md5 != ANACONDA_MD5:
        if confirm("Anaconda archive corrupt. Delete?"):
            run('rm %s' % ANACONDA_FN)
        else:
            disconnect_all()
            sys.exit(1)

    return True


def anaconda_installed():
    r = run('test -d %s' % ANACONDA_INSTALL_PATH, quiet=True)

    if getattr(r, 'return_code') != 0:
        return False

    return True


def install_anaconda():
    if not anaconda_downloaded():
        run('wget --quiet %s' % ANACONDA_URL)
    if not anaconda_installed():
        sudo('bash %s -b -p %s' % (ANACONDA_FN, ANACONDA_INSTALL_PATH))
        sudo('echo "export PATH=/opt/anaconda/bin:$PATH" > /etc/profile.d/anaconda.sh')


def package_installed(pkg):
    r = run("dpkg-query -W -f='${Status}' %s 2>/dev/null | grep -c \"ok installed\"" % pkg, quiet=True)

    if getattr(r, 'return_code') != 0:
        return False

    return True


def install_java():
    if not package_installed('default-jre'):
        sudo('apt-get install -y -qq default-jre')


def install_elasticsearch():
    install_java()

    if not package_installed('elasticsearch'):
        run('wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -')
        run('wget -q http://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.0.0-beta1/elasticsearch-2.0.0-beta1.deb')
        #run('echo "deb http://packages.elastic.co/elasticsearch/1.5/debian stable main" | sudo tee -a /etc/apt/sources.list')
        sudo('apt-get update -qq -y > /dev/null')
        sudo('dpkg -i elasticsearch-2.0.0-beta1.deb')
        sudo ('apt-get -fy install')
#       put('provision/elasticsearch.yml', '/etc/elasticsearch/elasticsearch.yml', use_sudo=True)
        #sudo('/usr/share/elasticsearch/bin/plugin -i elasticsearch/marvel/latest')
        sudo('update-rc.d elasticsearch defaults 95 10')
        sudo('service elasticsearch start')



def install_logstash():

    if not package_installed('logstash'):
        sudo('apt-get install logstash -yq')


def install_neo4j():
    if not file_exists(NEO4J_FN):
        run('wget -q %s -O %s' % (NEO4J_URL, NEO4J_FN))

    sudo('adduser --home /home/neo4j --system --shell /bin/bash neo4j')
    sudo('(cd /home/neo4j; tar zxf ~/%s)' % NEO4J_FN, user='neo4j')
    sudo('yes neo4j|(HEADLESS=true; /home/neo4j/%s/bin/neo4j-installer install)' % NEO4J_FOLDER)
    sudo('echo "neo4j   soft    nofile  40000" > /etc/security/limits.conf')
    sudo('echo "neo4j   hard    nofile  40000" >> /etc/security/limits.conf')
    sudo('echo "session required pam_limits.so" > /etc/pam.d/common-session')
    sudo('echo "session required pam_limits.so" > /etc/pam.d/common-session-noninteractive')
    put('provision/neo4j-server.properties', '.')
    sudo('mv neo4j-server.properties /home/neo4j/%s/conf/neo4j-server.properties' % NEO4J_FOLDER)
    sudo('chown neo4j /home/neo4j/%s/conf/neo4j-server.properties' % NEO4J_FOLDER)
    sudo('chmod 644 /home/neo4j/%s/conf/neo4j-server.properties' % NEO4J_FOLDER)
    sudo('service neo4j-service start')


def install_neo4j_user():
    put('provision/auth', '.')
    sudo('mv auth /home/neo4j/neo4j-community-2.2.2/data/dbms/auth')
    sudo('chown neo4j /home/neo4j/neo4j-community-2.2.2/data/dbms/auth')
    sudo('chmod 600 /home/neo4j/neo4j-community-2.2.2/data/dbms/auth')
    sudo('service neo4j-service restart')


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
            run('source /home/vagrant/.bashrc && nvm install "$(cat .node-version)"')
            run('npm install -g npm@3.2')
            run('source /home/vagrant/.bashrc && npm install')


def install_eslib():
    if file_exists(ESLIB_INSTALL_PATH):
        return

    install_debian_packages(['git', 'python-dev'])

    sudo('(git clone https://github.com/comperiosearch/elasticsearch-eslib.git %s)' % ESLIB_INSTALL_PATH)
    sudo('pip install -e /opt/eslib')
    sudo('(chmod -R a+w %s)' % ESLIB_INSTALL_PATH)


def install_self():
    local('git archive master -o master.zip --format zip --prefix twitter-analysis-lab/')
    put('master.zip', '.')
    sudo('unzip master')

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


def place_credentials():
    boto_fn = 'config/boto'

    if not os.path.exists(boto_fn):
        error('Could not find boto configuration file ...')

    put(boto_fn, '.')
    sudo('mv boto .boto')

def provision_data():
    with cd('twitter-analysis-lab'):
        sudo('PYTHONPATH=. python bin/provision_data.py')