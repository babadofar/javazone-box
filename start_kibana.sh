. ~/.nvm/nvm.sh
cd kibana
cat .node-version
nvm install $(cat .node-version)
bin/kibana --dev

