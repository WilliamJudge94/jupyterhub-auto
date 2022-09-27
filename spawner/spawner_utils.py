import os, sys, pwd, grp, \
        shutil, pickle, psutil, \
        logging, requests
#from ics import Calendar
from datetime import datetime, timezone
from . import localsettings as ls


# HPC_LOG_FILE = "/hpc_logins.log" 
# HPC_RESOURCES_FILE = "hpc_resources.pkl"
# RAM_DIVIDER = 1073741274
# GCAL_ICS = None
# GROUP_NAME = "SharedFiles"
# MAX_RAM = None
# MAX_CPU = None
# ASCII_ART_FILE = "./ascii_art.txt"


# # Main User Configurable Parameters
# MAIN_DIR = "/local/data/"
# SERVER_NAME = "ESPEON"
# SERVER_MANAGER = "test_user"
# MEMBERS_DICT = {

# "test_user": [False, 1.0, 4.0],

# }

logging.basicConfig(filename=ls.HPC_LOG_FILE,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

# Standard Locations
#path = '/local/data/'
#filename = 'hpc_resources.pkl'

def obtain_logger(logging=logging):
    return logging


def obtain_gcal():
    cal_url = ls.GCAL_ICS
    c = Calendar(requests.get(cal_url).text)
    return c


def get_events_that_end_after_current_time(calendar_object):
    cal_events = list(calendar_object.timeline)
    
    store_names = []
    
    for event in cal_events:
        delta_end = datetime.now(timezone.utc) - event.end
        day_end = delta_end.days
        
        delta_start = datetime.now(timezone.utc) - event.begin
        day_start = delta_start.days
        
        if day_end < 0:
            if day_start >= 0:
                store_names.append(event.name)
            
    return store_names

    
def check_if_name_in_cal(names_list, check_name):
    
    check = False
    
    for names in names_list:
        if check_name in names:
            check = True
            
    if check:
        pass
        
    else:
        raise ValueError(f'Current user "{check_name}" not found in {ls.SERVER_NAME} google calendar title.')
        
        
def google_cal_full_check(check_name):
    
    calendar = obtain_gcal()

    names_list = get_events_that_end_after_current_time(calendar)

    check_if_name_in_cal(names_list, check_name)
    

def check_dir_exists(username, path=ls.MAIN_DIR):
    total_path = f'{path}{username}/'
    access_mkdir = 0o2777

    if not os.path.isdir(total_path):
        os.mkdir(total_path, mode=access_mkdir)
        shutil.chown(total_path, user=None, group=ls.GROUP_NAME)
        

def get_current_users_resources(dic):
    store = '\n'
    for item in dic.keys():
        if dic[item][0] != 0:
            store += f"MAIN_USERS="f"{item}_{dic[item][0]}_RAM_and_{dic[item][1]}_CPU\n"
            
    return store


def check_dict_file(filename=ls.HPC_RESOURCES_FILE,
                    path=ls.MAIN_DIR):

    file = f'{path}{filename}'
    if not os.path.exists(file):
        empty_dict = {}

        with open(file, 'wb') as handle:
            pickle.dump(empty_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        shutil.chown(file, user=None, group=ls.GROUP_NAME)
        os.chmod(file, 0o666)


def read_dict_file(filename=ls.HPC_RESOURCES_FILE,
                    path=ls.MAIN_DIR):

    file = f'{path}{filename}'
    with open(file, 'rb') as handle:
        output = pickle.load(handle)

    logging.info('Reading Resources...')

    return output


def write_dict_file(dic,
                    filename=ls.HPC_RESOURCES_FILE,
                    path=ls.MAIN_DIR):

    file = f'{path}{filename}'

    with open(file, 'wb') as handle:
        pickle.dump(dic, handle, protocol=pickle.HIGHEST_PROTOCOL)

    logging.info('Removing/Updating User Resources...')
    logging.info(f"New Dict: {dic}")


def collect_current_ram_usage(dic):
    ram = []

    for person in dic:
        ram.append(dic[person][0])

    return sum(ram)


def collect_current_cpu_usage(dic):
    cpu = []

    for person in dic:
        cpu.append(dic[person][1])

    return sum(cpu)


def set_max_ram(ram_usage):
    total_ram = round(psutil.virtual_memory().total / ls.RAM_DIVIDER) - 4

    return total_ram - ram_usage


def set_max_cpu(cpu_usage):
    total_cpu = psutil.cpu_count() - 2

    return total_cpu - cpu_usage


def add_user_resources(user,
                        ram_chosen,
                        cpu_chosen,
                        filename=ls.HPC_RESOURCES_FILE,
                        path=ls.MAIN_DIR):

    file = f'{path}{filename}'
    

    dic = read_dict_file(path, filename)
    dic[user] = [ram_chosen, cpu_chosen]

    write_dict_file(path, filename, dic)

    logging.info(f'User Login: {user} - RAM: {ram_chosen} - CPU: {cpu_chosen}')
    print('Adding User Resources\n\n\n\n')


def remove_user_resources(user,
                            filename=ls.HPC_RESOURCES_FILE, 
                            path=ls.MAIN_DIR):

    file = f'{path}{filename}'

    dic = read_dict_file(path, filename)
    dic[user] = [0, 0]

    write_dict_file(path, filename, dic)

    logging.info(f'User Logout: {user}')
    
    print('Removing User Resources\n\n\n\n')

    return dic


def start_resource_check(filename=ls.HPC_RESOURCES_FILE,
                            reset=False,
                            path=ls.MAIN_DIR):

    if isinstance(reset, str):
        if reset == 'True':
            reset = True
        else:
            reset = False
    
    if reset == True:
        os.system(f'rm -f {path}{filename}')
        print(f'Resetting Resources - {reset} - {reset==True}')

    check_dict_file(path, filename)
    logging.info(f'Pulling Resources From: {path}{filename}')
    dic = read_dict_file(path, filename)

    ram_usage = collect_current_ram_usage(dic)
    cpu_usage = collect_current_cpu_usage(dic)

    max_ram = set_max_ram(ram_usage)
    max_cpu = set_max_cpu(cpu_usage)

    return max_ram, max_cpu, dic