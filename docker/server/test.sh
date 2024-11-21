T=$'\t'
env_vars=()
env_vars+=('-e' "ADB_USERS=crawler${T}12crawl@47+ee${T}rag${T}towel\$GPT2879")
env_vars+=('-e' 'DB_USER=admin')
env_vars+=('-e' 'DB_PASS=admin')
env_vars+=('-e' 'DB_HOST=localhost')
env_vars+=('-e' 'DB_PORT=55535')
env_vars+=('-e' 'ADB_PORT=55535')
docker run -it --rm "${env_vars[@]}" aperturedb-with-loading
