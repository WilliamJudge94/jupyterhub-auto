check_command() {
    local cmd_name=$1
    local cmd_path

    # Find the full path of the command, suppressing errors if not found
    cmd_path=$(which "$cmd_name" 2>/dev/null)

    if [ -n "$cmd_path" ]; then
        if [[ "$cmd_path" != *"jupyterhub-auto"* ]]; then
            echo "Error: '$cmd_name' cannot be within the PATH outside of 'jupyterhub-auto'"
            exit 1
        fi
    fi
}

# Check for 'jupyter' and 'jupyterhub'
check_command "jupyter"
check_command "jupyterhub"

current_dir="$PWD"

echo "Is Conda Installed? (y/n)"
read conda_answer

# Installing Conda
if [ $conda_answer != "y" ]
then
	echo "Anaconda Year (2023)"
	read conda_year
	echo "Anaconda Month (03)"
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


# Make Sure User Has Set The login.html File
printf "\n"
echo "Have You Edited The templates/ Folder Files? (y/n)"
read localsettings_answ

if [ $localsettings_answ == "n" ]
then
	echo "Please Edit The templates/ Folder Files"
	exit 0 
fi


opt_jupyter_ssl="/opt/jupyterhub/ssl-certs/"
opt_jupyter="/opt/jupyterhub/"

# Creating opt dir
if [ -d ${opt_jupyter_ssl} ]
then
	echo ${opt_jupyter_ssl}"exists"
else
	sudo mkdir -p ${opt_jupyter_ssl}
fi

# Installing Packages
printf "\n"
echo "Install Packages? y/n"
read install_answer
if [ $install_answer == "y" ]
then
	printf "\n"
	echo "What is your python version for install - pythonX -m pip install?"
	read py_version_install

	sudo apt-get install python${py_version_install}
	sudo apt-get install python3-pip
	sudo apt install nodejs npm
	sudo npm install -g configurable-http-proxy

	sudo python${py_version_install} -m pip install --force-reinstall --no-cache-dir -r requirements.txt
	
fi

printf "\n"

# Generating Config File
cd $opt_jupyter
sudo jupyterhub --generate-config

printf "\n"
# Generating SSL Certs
echo "Install SSL Certs (y/n)"
read cert_answer

# Installing Conda
if [ $cert_answer == "y" ]
then
	ssl_key=${opt_jupyter_ssl}jhub.key
	ssl_cert=${opt_jupyter_ssl}jhub.cert
	sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout ${ssl_key} -out ${ssl_cert}
fi


# Changing JupyterHub Config File
initial_sed='s|# '
ending_sed="|g "
file_sed=${opt_jupyter}'jupyterhub_config.py'
sudo chmod 666 ${file_sed}
sudo echo "c.PAMAuthenticator.admin_groups = {'MANAGER'}" >> ${file_sed}

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

# Default Spawner
default="c.JupyterHub.spawner_class = 'jupyterhub.spawner.LocalProcessSpawner'"
new_default='c.JupyterHub.spawner_class = "systemdspawner.SystemdSpawner" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}


# Default Logo
default="c.JupyterHub.logo_file = "
new_default='c.JupyterHub.logo_file = "/opt/jupyterhub/templates/jhub_logo.png" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}

# Default Login Template
default="c.JupyterHub.template_paths = "
new_default='c.JupyterHub.template_paths =  ["/opt/jupyterhub/templates/"] #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}

printf "\n"
# Create Main Dir
cd $current_dir
creation_dir=$(sed '13!d;q' ./spawner/localsettings.py)
creation_dir2=${creation_dir:12:-1}
if [ -d ${creation_dir2} ]
then
	echo ${creation_dir2}" exists"
	printf "\n"
else
	sudo mkdir -p ${creation_dir2}
	
fi

shared_file_creation=${creation_dir2}'/shared/'
if [ -d ${shared_file_creation} ]
then
	echo ${shared_file_creation}" exists"
	printf "\n"
else
	sudo mkdir -p ${shared_file_creation}
	
fi

# Default Dir
default="c.Spawner.notebook_dir = ''"
new_default='c.Spawner.notebook_dir = "'${creation_dir2}'{username}" #'

sed_script_default=${initial_sed}${default}'|'${new_default}
sudo sed -i "${sed_script_default}${ending_sed}" ${file_sed}



# Set Permissions In Main Dir
user_groups=$(sed '6!d;q' ./spawner/localsettings.py)
user_groups2=${user_groups:14:-1}
creation_dir3=$(echo "$creation_dir2" | cut -d "/" -f2)
creation_dir4="/$creation_dir3/"
sudo groupadd ${user_groups2}
sudo groupadd MANAGER
printf "\n"
sudo chown -R root:${user_groups2} ${creation_dir4}
sudo chmod -R 775 ${creation_dir4} 

pyv="$(sudo python3 -V 2>&1)"
echo "Please Type In The First Two Digits of $pyv  It should be in the form of 3.10"
read pversion
sudo cp -r spawner/. /usr/local/lib/python${pversion}/dist-packages/systemdspawner/.

sudo cp -r spawner/. /usr/local/lib/python${pversion}/site-packages/systemdspawner/.

sudo cp -r templates /opt/jupyterhub/


# Making JupyterHub A Service
sudo cp ./jupyterhub /etc/init.d/. 
sudo chmod +x /etc/init.d/jupyterhub

sudo systemctl daemon-reload
sudo service jupyterhub start
sudo service jupyterhub restart
sudo service jupyerhub enable

printf "\n"
echo "Installation Complete!! Please, go to https://localhost:8000 in your browser"


