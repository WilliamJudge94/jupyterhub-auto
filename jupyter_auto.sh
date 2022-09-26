current_dir="$PWD"

echo "Is Conda Installed? (y/n)"
read conda_answer

# Installing Conda
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


# Make Sure User Has Set The Localsettings File
printf "\n"
echo "Have You Edited The localsettings.py File? (y/n)"
read localsettings_answ


if [ $localsettings_answ == "n" ]
then
	echo "Please Edit The localsettings.py File"
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

# Installing Packages
printf "\n"
echo "Install Packages? y/n"
read install_answer
if [ $install_answer == "y" ]
then
	sudo apt-get install python3
	sudo apt-get install python3-pip
	sudo python3 -m pip install jupyterlab
	sudo python3 -m pip install jupyterhub
	sudo python3 -m pip install psutil
	sudo python3 -m pip install jupyterlab-system-monitor
	sudo python3 -m pip install --upgrade --force-reinstall pyzmg
	sudo apt install nodejs npm
	sudo npm install -g configurable-http-proxy
	sudo python3 -m pip install --upgrade autopep8
	# Install Extensions
	
	# Install github
	sudo python3 -m pip install --upgrade jupyterlab jupyterlab-git
	# Install spreadsheets
	sudo jupyter labextension install jupyterlab-spreadsheet
	# Execution Time
	sudo python3 -m pip install jupyterlab_execute_time
	# Install Dark Mode
	sudo python3 -m pip install jupyterlab_theme_solarized_dark
	
	# Install TOC
	# Instal collapsable headings
	# Install plotly
	# Install matplotlib
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
new_default_url='c.JupyterHub.default_url = ""'

sed_script_default_url=${initial_sed}${default_url}'|'${new_default_url}
sudo sed -i "${sed_script_default_url}${ending_sed}" ${file_sed} 

# Default Logout
default='c.JupyterHub.shutdown_on_logout = False'
new_default='c.JupyterHub.shutdown_on_logout = True'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed} 

# Default Certs
default='c.JupyterHub.ssl_cert = '
new_default='c.JupyterHub.ssl_cert = "/opt/jupyterhub/ssl-certs/jhub.cert" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}

# Default Keys
default='c.JupyterHub.ssl_key = '
new_default='c.JupyterHub.ssl_key = "/opt/jupyterhub/ssl-certs/jhub.key" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}



# Install SystemDSpawner

# Set Default Spawner

# Read Localsettings

# Create Main Dir
cd $current_dir
creation_dir=$(sed '13!d;q' ./localsettings.py)
creation_dir2=${creation_dir:12:-1}
if [ -d ${creation_dir2} ]
then
	echo ${creation_dir2}" exists"
else
	sudo mkdir -p ${creation_dir2}
fi

# Set Permissions In Main Dir
user_groups=$(sed '6!d;q' ./localsettings.py)
user_groups2=${user_groups:14:-1}
creation_dir3=$(echo "$creation_dir2" | cut -d "/" -f2)
creation_dir4="/$creation_dir3/"
sudo groupadd ${user_groups2}
sudo chown -R root:${user_groups2} ${creation_dir4}
sudo chmod -R 775 ${creation_dir4} 

# Copy Localsettings To Spawner

# Copy Ascii To Spawner


# Allow the User to select main dir for all users

# Allow the User to set up the groupnames for SharedFiles

# Allow the User to setup the ASCII characters

# Allow the User to setup the RAM and CPU limits

# Allow the User to setup manager name


# Copy Anaconda To Shared Directory


# Making JupyterHub A Service
sudo cp ./jupyterhub /etc/init.d/. 
sudo chmod +x /etc/init.d/jupyterhub

sudo systemctl daemon-reload
sudo service jupyterhub start
sudo service jupyterhub restart


