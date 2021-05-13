pip install -i https://${NEXUS_USERNAME}:${NEXUS_PASSWORD}@nexus.cor.corp.iotic/repository/py-group/simple --cert ${SSL_CERT_FILE} -r requirements.txt

### set these values
export HELPER_AUTH__RESOLVER_HOST=
export HELPER_AUTH__USER=
export HELPER_AUTH__SEED=
export HELPER_QAPI_URL=
export HELPER_QAPI_STOMP_URL=

### run this and the script will check if you actually want to do the delete
python delete_agents_twins.py
