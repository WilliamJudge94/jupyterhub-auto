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

Follow the instructions!


Editing Settings
-----------------


Editing Templates
------------------


Add yourself to the GROUP_NAME
------------------------------

- sudo usermod -a -G GROUP_NAME username
- Logout and Back In Again