current_dir="$PWD"

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


opt_jupyter_ssl="/opt/jupyterhub/ssl-certs/"
opt_jupyter="/opt/jupyterhub/"

# Creating opt dir
if [ -d ${opt_jupyter_ssl} ]
then
	echo ${opt_jupyter_ssl}"exists"
else
	sudo mkdir ${opt_jupyter_ssl}
fi

echo "Install Packages? y/n"
read install_answer
if [ $install_answer == "y" ]
then
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
fi

# Generating Config File
cd $opt_jupyter
sudo jupyterhub --generate-config

# Generating SSL Certs
ssl_key=${opt_jupyter_ssl}jhub.key
ssl_cert=${opt_jupyter_ssl}jhub.cert
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ${ssl_key} -out ${ssl_cert}


# Changing JupyterHub Config File
initial_sed='s|# '
ending_sed="|g "
file_sed=${opt_jupyter}'jupyterhub_config.py'

# Default URL
default_url='c.JupyterHub.default_url = traitlets.Undefined'
new_default_url='c.JupyterHub.default_url = "/lab"'

sed_script_default_url=${initial_sed}${default_url}'|'${new_default_url}
sudo sed -i "${sed_script_default_url}${ending_sed}" ${file_sed} 

# Default Logout
default='c.JupyterHub.shutdown_on_logout = False'
new_default='c.JupyterHub.shutdown_on_logout = True'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed} 


# Default Certs
default='c.JupyterHub.ssl_cert = '
new_default='c.JupyterHub.ssl_cert = "/opt/jupyterhub/ssl-certs/jhub.crt" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}

# Default Certs
default='c.JupyterHub.ssl_key = '
new_default='c.JupyterHub.ssl_key = "/opt/jupyterhub/ssl-certs/jhub.key" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}


#sudo sed -i "s,# c.JupyterHub.default_url = traitlets.Undefined,c.JupyterHub.default_url = '/lab',g" /opt/jupyterhub/jupyterhub_config.py


#sudo sed -i "s,# c.JupyterHub.default_url = traitlets.Undefined,c.JupyterHub.default_url = '/lab',g" /opt/jupyterhub/jupyterhub_config.py





cd $current_dir


