
# requirement in windows wsl:
# $ sudo apt-get install virtualenv
# $ sudo apt-get install unzip

cd "$(dirname $0)"
if [ ! -e tne_env/ ]; then
    virtualenv -p python3 tne_env
fi

. tne_env/bin/activate
pip install -r requirements.txt

mkdir font/
cd font/
wget 'https://noto-website-2.storage.googleapis.com/pkgs/NotoSerifCJKtc-hinted.zip'
unzip NotoSerifCJKtc-hinted.zip
