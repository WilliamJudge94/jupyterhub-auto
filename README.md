# jupyterhub-auto

Automatic Lab JupyterHub
========================

This bash script helps someone install a JupyterHub instance with RAM and CPU resorce managment. Once can also use this script to auto install conda, as well as customize their JupyterHub login page.


Motivation & Features
---------------------

- Insall conda
- Install JupyterHub
- Install systemdspawner for resource managment
- Customize resource managment
- Create shared drive space
- Customize the look of JupyterHub
- SSL encryption of traffic
- Creates a jupyterhub service

BASIC Installation
------------------

- cd ./repo/path/
- bash jupyter_auto.sh

- Is Conda Installed? n
- Anaconda Year (2021) 2021
- Anaconda Month (11) 11
- Pleas answer 'yes' or 'no' yes
- [/home/username/anaconda3] Enter
- Do you want the installer to initialize Anaconda3? yes
- source ~/.bashrc
- bash jupyer_auto.sh
- Is Conda Installed? y
- Have You Edited The localsettings.py File y
- Have You Edited The teamplates/ Folder Files y
- Install Packages y
-      Type Y for any package that requires a responce from install
-      Type blanks answers or actual answers into ssl-keygen responces
- Please Type In The First Two Digits of Python X.YY.Z   X.YY


Editing Settings
-----------------


Editing Templates
------------------


Add yourself to the GROUP_NAME
------------------------------

- sudo usermod -a -G GROUP_NAME username
- Logout and Back In Again


Add manager users to MANAGER group
----------------------------------

- sudo usermod -a -G MANAGER username