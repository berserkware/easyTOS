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
    

class VirtualMachine:
    """A structure for storing and managing virutal machines."""

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
        vms = []
        config = get_or_create_config()
        for section in config.sections():
            if section == 'Global':
                continue
            vms.append(VirtualMachine.make_from_dict(config[section]))

        return vms
            
    @classmethod
    def get_by_name(cls, name):
        """Gets a vm config by name."""
        config = get_or_create_config()
        return VirtualMachine.make_from_dict(config[name])
        
    @classmethod
    def make_from_dict(cls, config_dict: dict):
        """Makes self from a dict gotten from the ini."""
        return cls(
            name=config_dict['Name'],
            disc_filepath=config_dict['DiscFilepath'],
            mountpoint=config_dict['Mountpoint'],
            vm_type=config_dict.get('Type', 'qemu'),
            memory=config_dict.get('Memory', 8096),
            storage=config_dict.get('Storage', 5),
            cpu_count=config_dict.get('CpuCount', 2),
        )

    def run(self):
        """Runs the VM."""
        print("Starting TempleOS...")
        if self.vm_type == 'qemu':
            subprocess.Popen(
                f'sudo qemu-system-x86_64 -m {self.memory} -smp {self.cpu_count} -drive file={self.disc_filepath},format=raw',
                shell=True,
            )
        elif self.vm_type == 'vbox':
            os.system(f'VBoxManage storageattach {self.name} --storagectl "IDE Controller" --port 1 --device 1 --type dvddrive --medium none')
            os.system(f'VBoxManage startvm {self.name}')

    def qemu_install(self):
        """Installs the VM with QEMU."""
        print("Creating QEMU img...")
        os.system(f'sudo qemu-img create /var/lib/easytos/{self.name}.qcow2 {self.storage}G')
        print("Done")

        print("Initial TempleOS boot...")
        os.system(
            f'sudo qemu-system-x86_64 -boot d -cdrom /var/lib/easytos/TempleOS.ISO -m {self.memory} -smp {self.cpu_count} -drive file=/var/lib/easytos/{self.name}.qcow2,format=raw'
        )
        print("Done")
        
    def vbox_install(self):
        """Installs the VM with VirtualBox."""
        print("Creating VirtualBox VM...")
        os.system(f'VBoxManage createvm --name {self.name} --ostype Other_64 --register --basefolder /var/lib/easytos')
        os.system(f'VBoxManage modifyvm {self.name} --ioapic on')
        os.system(f'VBoxManage modifyvm {self.name} --memory {self.memory} --vram 128')
        os.system(f'VBoxManage modifyvm {self.name} --cpus {self.cpu_count}')
            
        os.system(f'VBoxManage createhd --filename /var/lib/easytos/{self.name}/{self.name}.vdi --size {int(self.storage)*1000} --format VDI')
        os.system(f'VBoxManage storagectl {self.name} --name "IDE Controller" --add ide --controller PIIX4')
    
        os.system(f'VBoxManage storageattach {self.name} --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium /var/lib/easytos/{self.name}/{self.name}.vdi')
        os.system(f'VBoxManage storageattach {self.name} --storagectl "IDE Controller" --port 1 --device 1 --type dvddrive --medium /var/lib/easytos/TempleOS.ISO')
        print("Done")

        print("Initial TempleOS boot...")
        os.system(f'VBoxManage startvm {self.name}')
        print("Done")
            
    def install(self):
        """Installs the VM according to the classes attributes."""

        if not os.path.exists('/var/lib/easytos/TempleOS.ISO'):
            get_iso()

        if self.vm_type == 'qemu':
            self.qemu_install()
        elif self.vm_type == 'vbox':
            self.vbox_install()

    def mount(self):
        """Mounts the VM's disc."""
        if not os.path.exists(self.mountpoint):
            os.mkdir(self.mountpoint)

        print("Mounting drive...")
        os.system('modprobe nbd max_part=8')
        os.system(f'qemu-nbd --connect=/dev/nbd0 {self.disc_filepath}')
        os.system(f'mount /dev/nbd0p1 {self.mountpoint}')
        print(f"Mounted at {self.mountpoint}.")

    def unmount(self):
        """Unmounts the VM's disc."""
        print("Unmounting drive...")
        os.system(f'umount {self.mountpoint}')
        os.system('qemu-nbd --disconnect /dev/nbd0')
        os.system('rmmod nbd')
        os.rmdir(self.mountpoint)
        print("Done.")
        
    def save(self):
        """Sets a vm config."""
        config = get_or_create_config()
        config[self.name] = self.make_dict()
        with open('/var/lib/easytos/config.ini', 'w') as configfile:
            config.write(configfile)

    def make_dict(self):
        """Converts the VM into a dict to put into the INI file."""
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


class ConfigureEasyTOS(tk.Toplevel):
    """A window for configuring easyTOS."""

    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)

        self.wm_title("Configure easyTOS")
        self.wm_resizable(False, False)

        self.message = ttk.Label(
            self,
            text='Configure easyTOS!',
            font=('Helvetica', 15),
        )
        self.message.grid(column=0, row=0, pady=5, padx=5, columnspan=2, stick='w')

        self.iso_source_label = ttk.Label(
            self,
            text='ISO Source:',
        )
        self.iso_source_label.grid(column=0, row=1, padx=5, stick='e')
        
        self.iso_source = tk.StringVar()
        self.iso_source.set(GlobalConfig.get_global_config().iso_source)
        self.iso_source_textbox = ttk.Entry(self, textvariable=self.iso_source, width=40)
        self.iso_source_textbox.grid(column=1, row=1, padx=5)

        self.save_button = ttk.Button(
            self,
            text='Save',
            command=self.save_config,
            width=10,
        )
        self.save_button.grid(column=0, row=2, padx=5, pady=5, stick="e", columnspan=2)

    def save_config(self):
        config = GlobalConfig.get_global_config()
        config.iso_source = self.iso_source.get()
        config.save()
        self.destroy()
        

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

        self.type_label = ttk.Label(
            self,
            text='Type:',
        )
        self.type_label.grid(column=0, row=1, padx=5, stick='e')
        
        types = ['qemu', 'vbox']
        self.chosen_type = tk.StringVar(self)
        self.chosen_type.set(types[0])
        
        self.vm_chooser = ttk.OptionMenu(
            self,
            self.chosen_type,
            types[0],
            *types,
        )
        self.vm_chooser.grid(column=1, row=1, padx=5, stick='ew')
        
        self.name_label = ttk.Label(
            self,
            text='Name:',
        )
        self.name_label.grid(column=0, row=2, padx=5, stick='e')

        self.vm_name = tk.StringVar()
        self.vm_name_textbox = ttk.Entry(self, textvariable=self.vm_name, width=20)
        self.vm_name_textbox.grid(column=1, row=2, padx=5)

        self.memory_label = ttk.Label(
            self,
            text='Memory (MB):',
        )
        self.memory_label.grid(column=0, row=3, padx=5, stick='e')

        self.vm_memory = tk.StringVar()
        self.vm_memory_textbox = ttk.Entry(self, textvariable=self.vm_memory, width=20)
        self.vm_memory_textbox.grid(column=1, row=3, padx=5)

        self.storage_label = ttk.Label(
            self,
            text='Storage (GB):',
        )
        self.storage_label.grid(column=0, row=4, padx=5, stick='e')

        self.vm_storage = tk.StringVar()
        self.vm_storage_textbox = ttk.Entry(self, textvariable=self.vm_storage, width=20)
        self.vm_storage_textbox.grid(column=1, row=4, padx=5)

        self.core_label = ttk.Label(
            self,
            text='Core Count:',
        )
        self.core_label.grid(column=0, row=5, padx=5, stick='e')

        self.vm_core = tk.StringVar()
        self.vm_core_textbox = ttk.Entry(self, textvariable=self.vm_core, width=20)
        self.vm_core_textbox.grid(column=1, row=5, padx=5)

        self.create_vm_frame = tk.Frame(
            self,
        )
        self.create_vm_frame.grid(column=0, row=6, columnspan=2, stick="e")
        
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
        vm_type = self.chosen_type.get()
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

        if vm_type == 'qemu':
            vm = VirtualMachine(
                name=vm_name,
                mountpoint=f'/mnt/{vm_name}',
                disc_filepath=f'/var/lib/easytos/{vm_name}.qcow2',
                vm_type=vm_type,
                memory=int(vm_memory),
                storage=int(vm_storage),
                cpu_count=int(vm_cores),
            )
            vm.install()
            vm.save()
        elif vm_type == 'vbox':
            vm = VirtualMachine(
                name=vm_name,
                mountpoint=f'/mnt/{vm_name}',
                disc_filepath=f'/var/lib/easytos/{vm_name}/{vm_name}.vdi',
                vm_type=vm_type,
                memory=int(vm_memory),
                storage=int(vm_storage),
                cpu_count=int(vm_cores),
            )
            vm.install()
            vm.save()

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

        vms = [vm.name for vm in VirtualMachine.get_all()]
        self.chosen_vm = tk.StringVar(self)
        self.chosen_vm.set(vms[0])
        
        self.vm_chooser = ttk.OptionMenu(
            self,
            self.chosen_vm,
            vms[0],
            *vms,
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
            
        vms = [vm.name for vm in VirtualMachine.get_all()]
        if self.chosen_vm is not None:
            chosen_vm = self.chosen_vm.get()
            vms[vms.index(chosen_vm)] = vms[0]
            vms[0] = chosen_vm
        self.chosen_vm = tk.StringVar(self)
        self.chosen_vm.set(vms[0])
        
        self.vm_chooser = ttk.OptionMenu(
            self,
            self.chosen_vm,
            vms[0],
            *vms,
        )
        self.vm_chooser.grid(column=0,row=1,stick='ew')

        self.chosen_vm.trace("w", lambda *args: self.refresh())

        vm = VirtualMachine.get_by_name(self.chosen_vm.get())

        self.info_label['text'] = f"{vm.vm_type}\n{vm.cpu_count} Cores\n{vm.memory}MB RAM\n{vm.storage}GB Storage"
            
        if os.path.exists(vm.disc_filepath):
            self.run_button.grid(column=1,row=1)
            
        if(os.path.exists(vm.disc_filepath) and
           not os.path.exists(vm.mountpoint)):
            self.mount_button.grid(column=1,row=2,sticky="nw")
            
        if os.path.exists(vm.mountpoint):
            self.unmount_button.grid(column=1,row=2,sticky="nw")

        self.info_label.grid(column=0,row=2, padx=5)

    def do_run(self):
        """Runs TempleOS."""
        vm = VirtualMachine.get_by_name(self.chosen_vm.get())
        vm.run()
        

    def do_mount(self):
        """Mounts the QEMU disc."""
        vm = VirtualMachine.get_by_name(self.chosen_vm.get())
        vm.mount()
        
        self.refresh()
        
    def do_unmount(self):
        """Unmounts the QEMU disc."""
        vm = VirtualMachine.get_by_name(self.chosen_vm.get())
        vm.unmount()

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

        if len(VirtualMachine.get_all()) > 0:
            self.vm_options = VMOptionFrame(self)
            self.vm_options.refresh()
            self.vm_options.grid(column=0, row=2)

        self.second_separator = ttk.Separator(
            self,
            orient='horizontal'
        )
        self.second_separator.grid(column=0, row=3, pady=10, padx=20, sticky='ew')

        self.configure_button = ttk.Button(
            self,
            text='CONFIGURE EASYTOS',
            command=lambda: ConfigureEasyTOS(self),
        )
        self.configure_button.grid(column=0,row=4,sticky='ew')
        
        self.exit_button = ttk.Button(
            self,
            text='EXIT',
            command=args[0].destroy,
        )
        self.exit_button.grid(column=0,row=5,sticky='ew')

    
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
