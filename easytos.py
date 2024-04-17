#!/usr/bin/python3
import tkinter as tk
from tkinter import ttk
import os
import sys
import requests
import subprocess
import configparser

# Edit these to modify the program
VM_MEMORY = 4096
VM_STORAGE = '5G'
CPU_COUNT = 2
MOUNT_POINT = '/mnt/templeos'
ISO_SOURCE = 'https://templeos.org/Downloads/TempleOS.ISO'

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

    def __init__(self, iso_source, mount_point):
        self.iso_source = iso_source
        self.mount_point = mount_point

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
            mount_point=config_dict.get(
                'MountPoint',
                '/mnt/templeos'
            ),
        )

    def make_dict(self):
        """Converts the config into a dict to put into the INI file."""
        config = {}
        config['ISOSource'] = self.iso_source
        config['MountPoint'] = self.mount_point
        return config
    

class VMConfig:
    """A structure to store VM config data."""

    def __init__(self, name, disc_filepath, vm_type, memory, storage, cpu_count):
        self.name = name
        self.disc_filepath = disc_filepath
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
            vm_type=config_dict.get('Type', 'qemu'),
            memory=config_dict.get('Memory', 8096),
            storage=config_dict.get('Storage', '5G'),
            cpu_count=config_dict.get('CpuCount', 2),
        )

    def make_dict(self):
        """Converts the config into a dict to put into the INI file."""
        config = {}
        config['Name'] = self.name
        config['DiscFilepath'] = self.disc_filepath
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

        self.wm_title("Create VM")
        self.wm_resizable(False, False)

        self.message = ttk.Label(
            self,
            text='Create VM',
            font=('Helvetica', 15),
        )
        self.message.grid(column=0, row=0, pady=4)

        self.name_label = ttk.Label(
            self,
            text='Name:',
        )
        self.name_label.grid(column=0, row=1)

        self.vm_name = tk.StringVar()
        self.vm_name_textbox = ttk.Entry(self, textvariable=self.vm_name)
        self.vm_name_textbox.grid(column=0, row=2, stick='ew')
        
        self.install_button = ttk.Button(
            self,
            text='Create',
            command=self.do_install,
            width=30,
        )
        self.install_button.grid(column=0, row=3)
        

    def do_install(self):
        """Gets the TempleOS ISO, creates the QEMU Image, and runs it with the CD installed."""
        if self.vm_name.get().strip() == '' or ' ' in self.vm_name.get().strip():
            return
        
        if not os.path.exists('/var/lib/easytos/TempleOS.ISO'):
            get_iso()

        if not os.path.exists(f'/var/lib/easytos/{self.vm_name.get().strip()}.qcow2'):
            print("Creating QEMU img...")
            os.system(f'sudo qemu-img create /var/lib/easytos/{self.vm_name.get().strip()}.qcow2 {VM_STORAGE}')
            print("Done.")

        print("Initial TempleOS boot...")
        os.system(
            f'sudo qemu-system-x86_64 -boot d -cdrom /var/lib/easytos/TempleOS.ISO -m {VM_MEMORY} -smp {CPU_COUNT} -drive file=/var/lib/easytos/{self.vm_name.get().strip()}.qcow2,format=raw'
        )

        vm_config = VMConfig(
            name=self.vm_name.get().strip(),
            disc_filepath=f'/var/lib/easytos/{self.vm_name.get().strip()}.qcow2',
            vm_type='qemu',
            memory=8096,
            storage='5G',
            cpu_count=2,
        )
        vm_config.save()

        self.master.run_button.grid(column=0,row=4)
        self.master.mount_button.grid(column=0,row=5)
        configured_vms = [vm.name for vm in VMConfig.get_all()]
        self.master.chosen_vm = tk.StringVar(self)
        self.master.chosen_vm.set(configured_vms[0])
        
        self.master.vm_chooser = ttk.OptionMenu(
            self.master,
            self.master.chosen_vm,
            configured_vms[0],
            *configured_vms,
        )
        self.master.vm_chooser.grid(column=0,row=3,stick='ew')
        
        self.master.first_separator.grid(
            column=0, row=2, pady=4, padx=20, columnspan=2, sticky='ew'
        )
        
        self.destroy()
        
    
class MainMenu(tk.Frame):
    """The main menu."""
    
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.message = ttk.Label(
            self,
            text='easyTOS!',
            font=('Helvetica', 30),
        )
        self.message.grid(column=0,row=0,pady=8)

        self.new_installation_button = ttk.Button(
            self,
            text='NEW INSTALLATION',
            command=lambda: CreateVM(self),
            width=30,
        )
        self.new_installation_button.grid(column=0,row=1)
        
        self.first_separator = ttk.Separator(
            self,
            orient='horizontal'
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

        if len(VMConfig.get_all()) > 0:
            self.first_separator.grid(column=0, row=2, pady=4, padx=20, columnspan=2, sticky='ew')
            
            configured_vms = [vm.name for vm in VMConfig.get_all()]
            self.chosen_vm = tk.StringVar(self)
            self.chosen_vm.set(configured_vms[0])
        
            self.vm_chooser = ttk.OptionMenu(
                self,
                self.chosen_vm,
                configured_vms[0],
                *configured_vms,
            )
            self.vm_chooser.grid(column=0,row=3,stick='ew')

            vm_config = VMConfig.get_by_name(self.chosen_vm.get())
            
            if os.path.exists(vm_config.disc_filepath):
                self.run_button.grid(column=0,row=4)
            
            if(os.path.exists(vm_config.disc_filepath) and
               not os.path.exists(GlobalConfig.get_global_config().mount_point)):
                self.mount_button.grid(column=0,row=5)
            
            if os.path.exists(GlobalConfig.get_global_config().mount_point):
                self.unmount_button.grid(column=0,row=6)

        self.second_separator = ttk.Separator(
            self,
            orient='horizontal'
        )
        self.second_separator.grid(column=0, row=7, pady=4, padx=20, columnspan=2, sticky='ew')
            
        self.exit_button = ttk.Button(
            self,
            text='EXIT',
            command=args[0].destroy,
            width=30,
        )
        self.exit_button.grid(column=0,row=8)

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
        
        if not os.path.exists(GlobalConfig.get_global_config().mount_point):
            os.mkdir(GlobalConfig.get_global_config().mount_point)

        print("Mounting drive...")
        os.system('modprobe nbd max_part=8')
        os.system(f'qemu-nbd --connect=/dev/nbd0 {vm_config.disc_filepath}')
        os.system('mount /dev/nbd0p1 /mnt/templeos')
        print("Mounted at /mnt/templeos.")
        
        self.unmount_button.grid(column=0,row=6)
        self.mount_button.grid_remove()
        
    def do_unmount(self):
        """Unmounts the QEMU disc."""
        print("Unmounting drive...")
        os.system(f'umount {GlobalConfig.get_global_config().mount_point}')
        os.system('qemu-nbd --disconnect /dev/nbd0')
        os.system('rmmod nbd')
        os.rmdir(GlobalConfig.get_global_config().mount_point)
        print("Done.")

        self.unmount_button.grid_remove()
        self.mount_button.grid(column=0,row=5)

    
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
        main_menu.pack(side="top", fill="both", expand=True)
        
    root.mainloop()
