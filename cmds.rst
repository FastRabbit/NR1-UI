
# get code

git clone http://github.com/theshepherdmatt/NR1-UI.git

# install and compile
bash NR1-UI/install.sh


# restart service

sudo systemctl restart nr1uibuster.service
sudo systemctl restart volumio.service

# stop service

sudo systemctl stop nr1uibuster.service



# Service Status

sudo systemctl status nr1uibuster.service
sudo systemctl status volumio.service


# Activae logs

sudo journalctl -fu nr1uibuster.service


sudo nano test.py
sudo nano nr1ui.py


# test if IO Expander is working

sudo i2cdetect -y 1


# run hw test script

sudo python3 test.py
