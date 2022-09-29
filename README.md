# Introduction
SysChecks up to this date include: Login View, Kernel reboot check, and System Update check.
<br>![SysChecks Overview](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_help_flag.png "SysChecks Overview")

The list of supported OSes:
- AlmaLinux 8
- CentOS 7
- Ubuntu (any non-EOL ubuntu release)
- Debian (any non-EOL debian release)

## Login banner (Login View)
This function displays the whole system overview, including number of updates, kernel reboot check, CPU type, RAM info, etc. It's most commonly used as a login banner.
<br>![SysChecks Login View](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_login_view.png "SysChecks Login View")

## Kernel reboot check
Kernel reboot check compares the running kernel version with a list of installed ones and lets you know if there is a need to reboot the system. It's used to encourage you to keep your system up-to-date on a kernel patch level. There are 2 outputs: human (used in Login Banner) and JSON (used to integrate with Zabbix).
<br>![SysChecks Kern Reboot Check](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_kern_reboot.png "SysChecks Kern Reboot Check")

## System Updates
Updates check uses dnf, yum or apt (depending on the OS) to get a list of available updates, and then sorts them into 2 groups: System and Security updates. Includes 2 outputs: human (used in Login Banner) and JSON (used to integrate with Zabbix).
<br>![SysChecks Updates Check](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_updates.png "SysChecks Updates Check")

# Installation
If you'd like to install SysChecks on your server, just run the command below:

Enter the `root` mode
```
sudo su -
```
Execute the below to install SysChecks
 > or with `bash -x syschecks_install.sh` to turn on the debug mode
```
curl https://raw.githubusercontent.com/yaroslav-gwit/SysChecks/main/install.sh > /root/syschecks_install.sh && bash syschecks_install.sh
```
Remove the installation script after you are done:
```
rm -f /root/syschecks_install.sh
```

# Roadmap
- fwupd intergration to inform the enduser/admin about the firmware updates
- disk space checks to show up at the login sreen if there are disks with less than 10% free space
- system update integration to automate system and security updates across the estate
- FreeBSD integration
- unified JSON output for all included functions
- publish Zabbix Templates for LTS versions 5 and 6
- make a YT video about the SysChecks usage and usecases
