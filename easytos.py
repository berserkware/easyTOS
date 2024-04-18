#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk
import os
import sys
import requests
import subprocess
import configparser

def get_iso():
    """Downloads the TempleOS ISO."""
    print("Downloading TempleOS ISO...")
    response = requests.get(GlobalConfig.get_global_config().iso_source)
    with open('/var/lib/easytos/TempleOS.ISO', mode='wb') as file:
        file.write(response.content)
    print("ISO written to /var/lib/easytos.")

def get_or_create_config():
    """Gets the config, creates it if it doesn't exist."""
    if not os.path.exists('/var/lib/easytos/config.ini'):
        config = configparser.ConfigParser()
        config['Global'] = GlobalConfig.make_from_dict({}).make_dict()
        with open('/var/lib/easytos/config.ini', 'w') as configfile:
            config.write(configfile)
            
    config = configparser.ConfigParser()
    config.read('/var/lib/easytos/config.ini')
    return config


class GlobalConfig:
    """A structure to store global config data."""

    def __init__(self, iso_source):
        self.iso_source = iso_source

    @classmethod
    def get_global_config(cls):
        """Gets the global config."""
        config = get_or_create_config()['Global']
        
        return cls.make_from_dict(config)

    def save(self):
        """Sets the global config."""
        config = get_or_create_config()
        config['Global'] = self.make_dict()
        with open('/var/lib/easytos/config.ini', 'w') as configfile:
            config.write(configfile)
        
    @classmethod
    def make_from_dict(cls, config_dict: dict):
        """Makes a VMConfig from a dict gotten from the ini."""
        return cls(
            iso_source=config_dict.get(
                'ISOSource',
                'https://templeos.org/Downloads/TempleOS.ISO',
            ),
        )

    def make_dict(self):
        """Converts the config into a dict to put into the INI file."""
        config = {}
        config['ISOSource'] = self.iso_source
        return config
    

class VMConfig:
    """A structure to store VM config data."""

    def __init__(self, name, disc_filepath, mountpoint, vm_type, memory, storage, cpu_count):
        self.name = name
        self.disc_filepath = disc_filepath
        self.mountpoint = mountpoint
        self.vm_type = vm_type
        self.memory = memory
        self.storage = storage
        self.cpu_count = cpu_count

    @classmethod
    def get_all(cls):
        """Gets all the configured VMs."""
        vm_configs = []
        config = get_or_create_config()
        for section in config.sections():
            if section == 'Global':
                continue
            vm_configs.append(VMConfig.make_from_dict(config[section]))

        return vm_configs
            
    @classmethod
    def get_by_name(cls, name):
        """Gets a vm config by name."""
        config = get_or_create_config()
        return VMConfig.make_from_dict(config[name])

    def save(self):
        """Sets a vm config."""
        config = get_or_create_config()
        config[self.name] = self.make_dict()
        with open('/var/lib/easytos/config.ini', 'w') as configfile:
            config.write(configfile)
        
    @classmethod
    def make_from_dict(cls, config_dict: dict):
        """Makes a VMConfig from a dict gotten from the ini."""
        return cls(
            name=config_dict['Name'],
            disc_filepath=config_dict['DiscFilepath'],
            mountpoint=config_dict['Mountpoint'],
            vm_type=config_dict.get('Type', 'qemu'),
            memory=config_dict.get('Memory', 8096),
            storage=config_dict.get('Storage', 5),
            cpu_count=config_dict.get('CpuCount', 2),
        )

    def make_dict(self):
        """Converts the config into a dict to put into the INI file."""
        config = {}
        config['Name'] = self.name
        config['DiscFilepath'] = self.disc_filepath
        config['Mountpoint'] = self.mountpoint
        config['Type'] = self.vm_type
        config['Memory'] = self.memory
        config['Storage'] = self.storage
        config['CpuCount'] = self.cpu_count
        return config
        
    
class SudoNotice(tk.Frame):
    """The notice to tell the user they need to run as sudo."""
    
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.message = ttk.Label(
            self,
            text='easyTOS needs superuser permissions to run.',
        )
        self.message.pack()
    
        self.button = ttk.Button(
            self,
            text='Ok',
            command=args[0].destroy,
            width=40,
        )
        self.button.pack()


class CreateVM(tk.Toplevel):
    """A window for creating a VM."""
    
    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)

        self.wm_title("New Installation")
        self.wm_resizable(False, False)

        self.message = ttk.Label(
            self,
            text='New Installation',
            font=('Helvetica', 15),
        )
        self.message.grid(column=0, row=0, pady=5, padx=5, columnspan=2, stick='w')

        self.name_label = ttk.Label(
            self,
            text='Name:',
        )
        self.name_label.grid(column=0, row=1, padx=5, stick='e')

        self.vm_name = tk.StringVar()
        self.vm_name_textbox = ttk.Entry(self, textvariable=self.vm_name, width=20)
        self.vm_name_textbox.grid(column=1, row=1, padx=5)

        self.memory_label = ttk.Label(
            self,
            text='Memory (MB):',
        )
        self.memory_label.grid(column=0, row=2, padx=5, stick='e')

        self.vm_memory = tk.StringVar()
        self.vm_memory_textbox = ttk.Entry(self, textvariable=self.vm_memory, width=20)
        self.vm_memory_textbox.grid(column=1, row=2, padx=5)

        self.storage_label = ttk.Label(
            self,
            text='Storage (GB):',
        )
        self.storage_label.grid(column=0, row=3, padx=5, stick='e')

        self.vm_storage = tk.StringVar()
        self.vm_storage_textbox = ttk.Entry(self, textvariable=self.vm_storage, width=20)
        self.vm_storage_textbox.grid(column=1, row=3, padx=5)

        self.core_label = ttk.Label(
            self,
            text='Core Count:',
        )
        self.core_label.grid(column=0, row=4, padx=5, stick='e')

        self.vm_core = tk.StringVar()
        self.vm_core_textbox = ttk.Entry(self, textvariable=self.vm_core, width=20)
        self.vm_core_textbox.grid(column=1, row=4, padx=5)

        self.create_vm_frame = tk.Frame(
            self,
        )
        self.create_vm_frame.grid(column=0, row=5, columnspan=2, stick="e")
        
        self.hang_warning_label = ttk.Label(
            self.create_vm_frame,
            text="(May hang for a second)",
        )
        self.hang_warning_label.grid(column=0, row=0, stick="e")
        
        self.install_button = ttk.Button(
            self.create_vm_frame,
            text='Create',
            command=self.do_install,
            width=10,
        )
        self.install_button.grid(column=1, row=0, padx=5, pady=5, stick="e")

    def do_install(self):
        """Gets the TempleOS ISO, creates the QEMU Image, and runs it with the CD installed."""
        vm_name = self.vm_name.get().strip()
        vm_memory = self.vm_memory.get().strip()
        vm_storage = self.vm_storage.get().strip()
        vm_cores = self.vm_core.get().strip()
        
        if(
                vm_name == '' or
                vm_memory == '' or
                vm_storage == '' or
                vm_cores == '' or
                ' ' in vm_name
        ):
            return
        
        if not os.path.exists('/var/lib/easytos/TempleOS.ISO'):
            get_iso()
            
        print("Creating QEMU img...")
        os.system(f'sudo qemu-img create /var/lib/easytos/{vm_name}.qcow2 {vm_storage}G')
        print("Done.")

        print("Initial TempleOS boot...")
        os.system(
            f'sudo qemu-system-x86_64 -boot d -cdrom /var/lib/easytos/TempleOS.ISO -m {vm_memory} -smp {vm_cores} -drive file=/var/lib/easytos/{vm_name}.qcow2,format=raw'
        )

        vm_config = VMConfig(
            name=self.vm_name.get().strip(),
            mountpoint=f'/mnt/{vm_name}',
            disc_filepath=f'/var/lib/easytos/{vm_name}.qcow2',
            vm_type='qemu',
            memory=int(vm_memory),
            storage=int(vm_storage),
            cpu_count=int(vm_cores),
        )
        vm_config.save()

        self.master.vm_options = VMOptionFrame(self.master)
        self.master.vm_options.refresh()
        self.master.vm_options.grid(column=0, row=2)
        
        self.destroy()


class VMOptionFrame(tk.Frame):
    """The frame that contains theVM options."""

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.first_separator = ttk.Separator(
            self,
            orient='horizontal'
        )

        configured_vms = [vm.name for vm in VMConfig.get_all()]
        self.chosen_vm = tk.StringVar(self)
        self.chosen_vm.set(configured_vms[0])
        
        self.vm_chooser = ttk.OptionMenu(
            self,
            self.chosen_vm,
            configured_vms[0],
            *configured_vms,
        )

        self.run_button = ttk.Button(
            self,
            text='RUN',
            command=self.do_run,
            width=30,
        )
            
        self.mount_button = ttk.Button(
            self,
            text='MOUNT',
            command=self.do_mount,
            width=30,
        )

        self.unmount_button = ttk.Button(
            self,
            text='UNMOUNT',
            command=self.do_unmount,
            width=30,
        )

        self.info_label = ttk.Label(
            self,
            text="X\nCores\nXMB RAM\nXGB Storage",
        )

    def refresh(self):
        """Updates the frame to only show the needed buttons."""

        self.first_separator.grid_remove()
        self.vm_chooser.grid_remove()
        self.run_button.grid_remove()
        self.mount_button.grid_remove()
        self.unmount_button.grid_remove()
        self.info_label.grid_remove()

        self.first_separator.grid(column=0, row=0, columnspan=2, pady=10, padx=20, sticky='ew')
            
        configured_vms = [vm.name for vm in VMConfig.get_all()]
        if self.chosen_vm is not None:
            chosen_vm = self.chosen_vm.get()
            configured_vms[configured_vms.index(chosen_vm)] = configured_vms[0]
            configured_vms[0] = chosen_vm
        self.chosen_vm = tk.StringVar(self)
        self.chosen_vm.set(configured_vms[0])
        
        self.vm_chooser = ttk.OptionMenu(
            self,
            self.chosen_vm,
            configured_vms[0],
            *configured_vms,
        )
        self.vm_chooser.grid(column=0,row=1,stick='ew')

        self.chosen_vm.trace("w", lambda *args: self.refresh())

        vm_config = VMConfig.get_by_name(self.chosen_vm.get())

        self.info_label['text'] = f"{vm_config.vm_type}\n{vm_config.cpu_count} Cores\n{vm_config.memory}MB RAM\n{vm_config.storage}GB Storage"
            
        if os.path.exists(vm_config.disc_filepath):
            self.run_button.grid(column=1,row=1)
            
        if(os.path.exists(vm_config.disc_filepath) and
           not os.path.exists(vm_config.mountpoint)):
            self.mount_button.grid(column=1,row=2,sticky="nw")
            
        if os.path.exists(vm_config.mountpoint):
            self.unmount_button.grid(column=1,row=2,sticky="nw")

        self.info_label.grid(column=0,row=2, padx=5)

    def do_run(self):
        """Runs TempleOS."""
        vm_config = VMConfig.get_by_name(self.chosen_vm.get())
        
        print("Starting TempleOS...")
        subprocess.Popen(
            f'sudo qemu-system-x86_64 -m {vm_config.memory} -smp {vm_config.cpu_count} -drive file={vm_config.disc_filepath},format=raw',
            shell=True,
        )

    def do_mount(self):
        """Mounts the QEMU disc."""
        vm_config = VMConfig.get_by_name(self.chosen_vm.get())
        
        if not os.path.exists(vm_config.mountpoint):
            os.mkdir(vm_config.mountpoint)

        print("Mounting drive...")
        os.system('modprobe nbd max_part=8')
        os.system(f'qemu-nbd --connect=/dev/nbd0 {vm_config.disc_filepath}')
        os.system(f'mount /dev/nbd0p1 {vm_config.mountpoint}')
        print(f"Mounted at {vm_config.mountpoint}.")
        
        self.refresh()
        
    def do_unmount(self):
        """Unmounts the QEMU disc."""
        vm_config = VMConfig.get_by_name(self.chosen_vm.get())
        
        print("Unmounting drive...")
        os.system(f'umount {vm_config.mountpoint}')
        os.system('qemu-nbd --disconnect /dev/nbd0')
        os.system('rmmod nbd')
        os.rmdir(vm_config.mountpoint)
        print("Done.")

        self.refresh()
        
    
class MainMenu(tk.Frame):
    """The main menu."""
    
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.message = ttk.Label(
            self,
            text='easyTOS!',
            font=('Helvetica', 30),
        )
        self.message.grid(column=0,row=0,pady=8,padx=30)

        self.new_installation_button = ttk.Button(
            self,
            text='NEW INSTALLATION',
            command=lambda: CreateVM(self),
        )
        self.new_installation_button.grid(column=0,row=1,sticky='ew')

        if len(VMConfig.get_all()) > 0:
            self.vm_options = VMOptionFrame(self)
            self.vm_options.refresh()
            self.vm_options.grid(column=0, row=2)

        self.second_separator = ttk.Separator(
            self,
            orient='horizontal'
        )
        self.second_separator.grid(column=0, row=3, pady=10, padx=20, sticky='ew')
            
        self.exit_button = ttk.Button(
            self,
            text='EXIT',
            command=args[0].destroy,
        )
        self.exit_button.grid(column=0,row=4,sticky='ew')

    
if __name__ == '__main__':
    root = tk.Tk()
    root.title('easyTOS');
    root.resizable(False, False)

    if os.geteuid() != 0:
        print("Superuser Privileges are needed to run easyTOS!")
        sudo_notice = SudoNotice(root)
        sudo_notice.pack(side="top", fill="both", expand=True)
    else:
        if not os.path.isdir('/var/lib/easytos'):
            os.mkdir('/var/lib/easytos')

        get_or_create_config()
            
        main_menu = MainMenu(root)
        main_menu.pack()
        
    root.mainloop()
