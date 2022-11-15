import os
import pwd
import subprocess
from traitlets import (Bool, Unicode, List,
                        Dict, Int, default)

import asyncio
from tornado import web


from systemdspawner import systemd

from jupyterhub.spawner import Spawner
from jupyterhub.utils import random_port

from .spawner_utils import (obtain_gcal,
                        get_events_that_end_after_current_time, check_if_name_in_cal,
                        google_cal_full_check,
                        check_dir_exists,
                        simlink_shared_folder, 
                        get_current_users_resources,
                        check_dict_file,
                        read_dict_file,
                        write_dict_file,
                        collect_current_ram_usage,
                        collect_current_cpu_usage,
                        set_max_ram,
                        set_max_cpu,
                        add_user_resources,
                        remove_user_resources,
                        start_resource_check,
                        obtain_logger,
                        obtain_ascii_art,
                        obtain_localsettings,
)

from .ascii_art import obtain_ascii_art

# Added By Will
logging = obtain_logger()

class SystemdSpawner(Spawner):
    user_workingdir = Unicode(
        None,
        allow_none=True,
        help="""
        Path to start each notebook user on.

        {USERNAME} and {USERID} are expanded.

        Defaults to the home directory of the user.

        Not respected if dynamic_users is set to True.
        """
    ).tag(config=True)

    username_template = Unicode(
        '{USERNAME}',
        help="""
        Template for unix username each user should be spawned as.

        {USERNAME} and {USERID} are expanded.

        This user should already exist in the system.

        Not respected if dynamic_users is set to True
        """
    ).tag(config=True)

    default_shell = Unicode(
        os.environ.get('SHELL', '/bin/bash'),
        help='Default shell for users on the notebook terminal'
    ).tag(config=True)

    extra_paths = List(
        [],
        help="""
        Extra paths to prepend to the $PATH environment variable.

        {USERNAME} and {USERID} are expanded
        """,
    ).tag(config=True)

    unit_name_template = Unicode(
        'jupyter-{USERNAME}-singleuser',
        help="""
        Template to use to make the systemd service names.

        {USERNAME} and {USERID} are expanded}
        """
    ).tag(config=True)

    # FIXME: Do not allow enabling this for systemd versions < 227,
    # since that is when it was introduced.
    isolate_tmp = Bool(
        False,
        help="""
        Give each notebook user their own /tmp, isolated from the system & each other
        """
    ).tag(config=True)

    isolate_devices = Bool(
        False,
        help="""
        Give each notebook user their own /dev, with a very limited set of devices mounted
        """
    ).tag(config=True)

    disable_user_sudo = Bool(
        False,
        help="""
        Set to true to disallow becoming root (or any other user) via sudo or other means from inside the notebook
        """,
    ).tag(config=True)

    readonly_paths = List(
        None,
        allow_none=True,
        help="""
        List of paths that should be marked readonly from the user notebook.

        Subpaths maybe be made writeable by setting readwrite_paths
        """,
    ).tag(config=True)

    readwrite_paths = List(
        None,
        allow_none=True,
        help="""
        List of paths that should be marked read-write from the user notebook.

        Used to make a subpath of a readonly path writeable
        """,
    ).tag(config=True)

    unit_extra_properties = Dict(
        {},
        help="""
        Dict of extra properties for systemd-run --property=[...].

        Keys are property names, and values are either strings or
        list of strings (for multiple entries). When values are
        lists, ordering is guaranteed. Ordering across keys of the
        dictionary are *not* guaranteed.

        Used to add arbitrary properties for spawned Jupyter units.
        Read `man systemd-run` for details on per-unit properties
        available in transient units.
        """
    ).tag(config=True)

    dynamic_users = Bool(
        False,
        help="""
        Allocate system users dynamically for each user.

        Uses the DynamicUser= feature of Systemd to make a new system user
        for each hub user dynamically. Their home directories are set up
        under /var/lib/{USERNAME}, and persist over time. The system user
        is deallocated whenever the user's server is not running.

        See http://0pointer.net/blog/dynamic-users-with-systemd.html for more
        information.

        Requires systemd 235.
        """
    ).tag(config=True)

    slice = Unicode(
        None,
        allow_none=True,
        help="""
        Ensure that all users that are created are run within a given slice.
        This allow global configuration of the maximum resources that all users
        collectively can use by creating a a slice beforehand.
        """
    ).tag(config=True)



    @default('options_form')
    def _default_options_form(self):
        return """

        <pre class="pre-LG">
        {ascii_art}
        </pre>

        <br />

        <label for="username">Current User:</label>
        <input type="text" name="username" value='{username}' size="15"/>
        
        <label for="CPU_LIMIT">CPU (Threads):</label>
        <input type="number" name="CPU_LIMIT" value="0" style="width: 6em" />

        <label for="MEM_LIMIT">RAM (GB):</label>
        <input type="number" name="MEM_LIMIT" value="48" style="width: 6em" />

        <label for="RESET_RESOURCES">Reset Resources:</label>
        <input type="checkbox" name="RESET_RESOURCES" value=False />
        
        <br />
        <br />

        <div class="form-group">
            <label for="env">Available Resources RAM: {open_ram}GB  -  CPU: {threads} Threads   --   Current Active Users:</label>
            <textarea class="form-control" rows="5" name="env">{env}</textarea>
        </div>
        
        """.format(username=self.user.name,
                    ascii_art=obtain_ascii_art(),
                    open_ram=self.open_ram,
                    threads=self.open_cpu,
                    env=self.current_users_string)

    def options_from_form(self, formdata):
        """Turn options formdata into user_options"""
        options = {}

        print(formdata.keys())
        #print(type(formdata['env']))
        #print(formdata['env'])

        if 'username' in formdata:
            options['username'] = formdata['username'][0]
            #formdata['env']['username'] = formdata['username'][0]

        if 'CPU_LIMIT' in formdata:
            options['CPU_LIMIT'] = str(int(formdata['CPU_LIMIT'][0]))
            #formdata['env']['CPU_LIMIT'] = formdata['CPU_LIMIT'][0]

        if 'MEM_LIMIT' in formdata:
            options['MEM_LIMIT'] = str(int(formdata['MEM_LIMIT'][0]))+'G'
            #formdata['env']['MEM_LIMIT'] = formdata['MEM_LIMIT'][0]+'G'

        if 'RESET_RESOURCES' in formdata:
            options['RESET_RESOURCES'] = formdata['RESET_RESOURCES'][0]
            #formdata['env']['RESET_RESOURCES'] = formdata['RESET_RESOURCES'][0]
        else:
            options['RESET_RESOURCES'] = False

        return options

    def get_args(self):
        """Added By Will:
        Return arguments to pass to the notebook server"""
        argv = super().get_args()
        if self.user_options.get('argv'):
            argv.extend(self.user_options['argv'])
        return argv

    def get_env(self):
        """Added By Will"""
        env = super().get_env()
        if self.user_options.get('env'):
            env.update(self.user_options['env'])

        for key in self.user_options:
            env[key] = self.user_options[key]


        self.mem_limit = env['MEM_LIMIT']
        self.mem_guarantee = '1G'
        self.cpu_limit = float(env['CPU_LIMIT'])
        self.cpu_guarantee = float(1.0)

        return env

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All traitlets configurables are configured by now
        self.unit_name = self._expand_user_vars(self.unit_name_template)

        self.log.debug('user:%s Initialized spawner with unit %s', self.user.name, self.unit_name)

        # Added By Will
        try:
            dic = read_dict_file()
            logging.info(f'{self.user.name} - First Dictionary Entry Load {dic}')
        except Exception as ex:
            logging.info(f'Dictionary Error - {ex}')
        self.open_ram, self.open_cpu , dic = start_resource_check(reset=False)
        self.current_users_string = get_current_users_resources(dic)
        logging.info(f'{self.user.name} - Second Dictionarty Entry Load {dic}')

    def _expand_user_vars(self, string):
        """
        Expand user related variables in a given string

        Currently expands:
          {USERNAME} -> Name of the user
          {USERID} -> UserID
        """
        return string.format(
            USERNAME=self.user.name,
            USERID=self.user.id
        )

    def get_state(self):
        """
        Save state required to reconstruct spawner from scratch

        We save the unit name, just in case the unit template was changed
        between a restart. We do not want to lost the previously launched
        events.

        JupyterHub before 0.7 also assumed your notebook was dead if it
        saved no state, so this helps with that too!
        """
        state = super().get_state()
        state['unit_name'] = self.unit_name
        return state

    def load_state(self, state):
        """
        Load state from storage required to reinstate this user's server

        This runs after __init__, so we can override it with saved unit name
        if needed. This is useful primarily when you change the unit name template
        between restarts.

        JupyterHub before 0.7 also assumed your notebook was dead if it
        saved no state, so this helps with that too!
        """
        if 'unit_name' in state:
            self.unit_name = state['unit_name']

    async def start(self):
        self.port = random_port()
        self.log.debug('user:%s Using port %s to start spawning user server', self.user.name, self.port)

        # If there's a unit with this name running already. This means a bug in
        # JupyterHub, a remnant from a previous install or a failed service start
        # from earlier. Regardless, we kill it and start ours in its place.
        # FIXME: Carefully look at this when doing a security sweep.
        if await systemd.service_running(self.unit_name):
            self.log.info('user:%s Unit %s already exists but not known to JupyterHub. Killing', self.user.name, self.unit_name)
            await systemd.stop_service(self.unit_name)
            if await systemd.service_running(self.unit_name):
                self.log.error('user:%s Could not stop already existing unit %s', self.user.name, self.unit_name)
                raise Exception('Could not stop already existing unit {}'.format(self.unit_name))

        # If there's a unit with this name already but sitting in a failed state.
        # Does a reset of the state before trying to start it up again.
        if await systemd.service_failed(self.unit_name):
            self.log.info('user:%s Unit %s in a failed state. Resetting state.', self.user.name, self.unit_name)
            await systemd.reset_service(self.unit_name)

        env = self.get_env()


        ls = obtain_localsettings()

        group_checking = subprocess.check_output(['groups', self.user.name])
        str_group_checking = str(group_checking)

        if ls.GROUP_NAME in str_group_checking:
            pass
        else:
            err_msg = f"User: {self.user.name} not in Linux group: {ls.GROUP_NAME}"
            self.log.exception(err_msg)
            logging.info(err_msg)
            raise web.HTTPError(500, err_msg)

        if 'MANAGER' in str_group_checking:
            print(f'{self.user.name} has initiated a resource reset Pre-Check -- RAM: {self.open_ram}  CPU: {self.open_cpu}')
            self.open_ram, self.open_cpu, dic = start_resource_check(reset=env['RESET_RESOURCES'] )
            print(f'{self.user.name} has initiated a resource reset Post-Check -- RAM: {self.open_ram}  CPU: {self.open_cpu}')

        else:
            self.open_ram, self.open_cpu, dic = start_resource_check(reset=False)

        check_dir_exists(self.user.name)
        simlink_shared_folder(self.user.name)

        tot_min_ram = self.open_ram

        if self.mem_limit:
            env['MEM_LIMIT'] = str(self.mem_limit)
            if round(self.mem_limit / ls.RAM_DIVIDER) > tot_min_ram:
                # If the user is only trying to select a single RAM while maxed out - helps reset usage values
                if tot_min_ram <= 0 and round(self.mem_limit / ls.RAM_DIVIDER) <= 1.5:
                    pass
                else:
                    err_msg = f'User Selected - {round(self.mem_limit / ls.RAM_DIVIDER)}G Mem Limit ---  Available {tot_min_ram}G'
                    self.log.exception(err_msg)
                    logging.info(err_msg)
                    raise web.HTTPError(500, err_msg)

        if self.mem_guarantee:
            env['MEM_GUARANTEE'] = str(self.mem_guarantee)

        if self.cpu_limit:
            env['CPU_LIMIT'] = str(self.cpu_limit)
            if self.cpu_limit > self.open_cpu:
                # If the user is only trying to select a single Core while maxed out - helps reset usage values
                if self.open_cpu <= 0 and self.cpu_limit <= 1:
                    pass
                elif self.cpu_limit == 0:
                    pass
                else:
                    err_msg = f'User Selected - {round(self.cpu_limit)} Threads Mem Limit ---  Available {self.open_cpu}Threads'
                    self.log.exception(err_msg)
                    logging.info(err_msg)
                    raise web.HTTPError(500, err_msg)

        if self.cpu_guarantee:
            env['CPU_GUARANTEE'] = str(self.cpu_guarantee)

        if self.user.name in ls.MEMBERS_DICT:
            if ls.MEMBERS_DICT[self.user.name][0]:
                
                cpu_limits_float = ls.MEMBERS_DICT[self.user.name][1]
                ram_limits_int = int(ls.MEMBERS_DICT[self.user.name][2] * 1073741824)

                env['CPU_LIMIT'] = str(cpu_limits_float)
                env['MEM_LIMIT'] = str(ram_limits_int)
                env['MEM_GUARANTEE'] = str(ram_limits_int)
                self.cpu_limit = cpu_limits_float
                self.mem_limit = ram_limits_int

            else:
                err_msg = 'User Does Not Have Permission To Use This Server'
                self.log.exception(err_msg)
                logging.info(err_msg)
                raise web.HTTPError(500, err_msg)
        #google_cal_full_check(self.user.name)

        add_user_resources(self.user.name,
                            round(self.mem_limit/ls.RAM_DIVIDER),
                            self.cpu_limit)


        properties = {}

        if self.dynamic_users:
            properties['DynamicUser'] = 'yes'
            properties['StateDirectory'] = self._expand_user_vars('{USERNAME}')

            # HOME is not set by default otherwise
            env['HOME'] = self._expand_user_vars('/var/lib/{USERNAME}')
            # Set working directory to $HOME too
            working_dir = env['HOME']
            # Set uid, gid = None so we don't set them
            uid = gid = None
        else:
            try:
                unix_username = self._expand_user_vars(self.username_template)
                pwnam = pwd.getpwnam(unix_username)
            except KeyError:
                self.log.exception('No user named {} found in the system'.format(unix_username))
                raise
            uid = pwnam.pw_uid
            gid = pwnam.pw_gid
            if self.user_workingdir is None:
                working_dir = pwnam.pw_dir
            else:
                working_dir = self._expand_user_vars(self.user_workingdir)

        if self.isolate_tmp:
            properties['PrivateTmp'] = 'yes'

        if self.isolate_devices:
            properties['PrivateDevices'] = 'yes'

        if self.extra_paths:
            env['PATH'] = '{extrapath}:{curpath}'.format(
                curpath=env['PATH'],
                extrapath=':'.join(
                    [self._expand_user_vars(p) for p in self.extra_paths]
                )
            )

        env['SHELL'] = self.default_shell

        if self.mem_limit is not None:
            # FIXME: Detect & use proper properties for v1 vs v2 cgroups
            properties['MemoryAccounting'] = 'yes'
            properties['MemoryLimit'] = self.mem_limit

        if self.cpu_limit != 0:
            # FIXME: Detect & use proper properties for v1 vs v2 cgroups
            # FIXME: Make sure that the kernel supports CONFIG_CFS_BANDWIDTH
            #        otherwise this doesn't have any effect.
            properties['CPUAccounting'] = 'yes'
            properties['CPUQuota'] = '{}%'.format(int(self.cpu_limit * 100))

        if self.disable_user_sudo:
            properties['NoNewPrivileges'] = 'yes'

        if self.readonly_paths is not None:
            properties['ReadOnlyDirectories'] = [
                self._expand_user_vars(path)
                for path in self.readonly_paths
            ]

        if self.readwrite_paths is not None:
            properties['ReadWriteDirectories'] = [
                self._expand_user_vars(path)
                for path in self.readwrite_paths
            ]

        for property, value in self.unit_extra_properties.items():
            self.unit_extra_properties[property] = self._expand_user_vars(value)

        properties.update(self.unit_extra_properties)

        await systemd.start_transient_service(
            self.unit_name,
            cmd=[self._expand_user_vars(c) for c in self.cmd],
            args=[self._expand_user_vars(a) for a in self.get_args()],
            working_dir=working_dir,
            environment_variables=env,
            properties=properties,
            uid=uid,
            gid=gid,
            slice=self.slice,
        )

        for i in range(self.start_timeout):
            is_up = await self.poll()
            if is_up is None:
                return (self.ip or '127.0.0.1', self.port)
            await asyncio.sleep(1)

        return None

    async def stop(self, now=False):
        dic = remove_user_resources(self.user.name)
        await systemd.stop_service(self.unit_name)

    async def poll(self):
        if await systemd.service_running(self.unit_name):
            return None
        return 1
