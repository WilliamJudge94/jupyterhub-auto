echo "Is Conda Installed? (y/n)"
read conda_answer


if [ $conda_answer != "y" ]
then
    echo "Anaconda Year"
    read conda_year
    echo "Anaconda Month"
    read conda_month
    total_conda1="https://repo.continuum.io/archive/"
    total_conda2="Anaconda3-"${conda_year}"."${conda_month}"-Linux-x86_64.sh"
    total_conda=$total_conda1$total_conda2
    wget $total_conda
    bash $total_conda2
    echo "Please Initilize Conda Now With source ~/.bashrc Then Re-Run This Script"
    exit 0 
fi

# Creating opt dir
if [ -d "/opt/jupyterhub/" ]
then
    echo "/opt/jupyterhub exists"
else
    mkdir /opt/jupyterhub/
fi


sudo apt-get install python3
sudo apt-get install python3-pip
sudo python3 -m pip install jupyterlab
sudo python3 -m pip install jupyterhub
sudo python3 -m pip install psutil
# install systemdspawner here
sudo python3 -m pip install jupyterlab-system-monitor
sudo python3 -m pip install --upgrade --force-reinstall pyzmg
sudo apt install nodejs npm
sudo npm install -g configurable-http-proxy
