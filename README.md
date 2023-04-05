# NozNum_Visualization_Tool
Interactive Visualization Tool for Fit-bit Watch data.

# Description
This is a simple interactive application that displays a map and plots from data collected from a connected watch (Fit-bit Watch) datafile (.tcx file).

## The project
**todo**

## The Data
**todo**

## Pre-requisites
OS : `Windows`  
Language : `Python 3`

# How to run the application
You just need to download the executable file `NozNumApp.exe` and run it.





# Installation
To be able to run the python program, you'll need to install a few packages. You can use the already existing anaconda environment made during the development of the application which contains all the necessary packages, or you can install them individually.

## 1 . Using the Conda Environment
The conda environment used for developing the program is in the `/env` file and it's called `environment.yml`.
You can create an environment on your machine from this environment.yml file in a few steps :

1. Create the environment from the `environment.yml` file:  
`conda env create -f environment.yml`  
The name of the environment is written on the firsts line of the yml file. You can freely change it.

2. Activate the new environment:  
`conda activate noznum_env`  
In case you have changed the name of the environment in the yml file to `your_env`, you'll have to change `noznum_env` to `your_env`.

3. Verify that the new environment was installed correclty:  
`conda env list`  
Or you can also use `conda info --envs`  


## 2 . Install Packages
If you don't want to use the given conda environment, you can install the packages yourself using the `pip` package installer.  
- Pandas : `pip install pandas`
- Folium : `pip install folium`
- PyQt5 : `pip install PyQt5`
- PyQt5 Web Engine : `pip install PyQtWebEngine`
- ElementTree : `pip install elementpath`
- Matplotlib : `pip install matplotlib`

# Create a new executable for the application
If you want to make a new executable from your modified version of the program, you can use `pyinstaller` (How to install : `pip install pyinstaller`).  
To get a single executable file from `main.py`, run this command :  
`pyinstaller --name "custom_app_name" --onefile --noconsole main.py`  
You can give a custom name to your application by changing `"custom_app_name"`. 


# License
MIT License