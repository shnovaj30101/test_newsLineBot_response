cd "$(dirname $0)"
. ./tne_env/bin/activate

python app.py -mu root -mh localhost -md news_data -mP password
