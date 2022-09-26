# Introduction
SysChecks up to this date include: Login View, Kernel reboot check, and System Update check.
<br>The list of supported OSes:
- AlmaLinux 8
- CentOS 7
- Ubuntu (any non-EOL ubuntu release)
- Debian (any non-EOL debian release)

## Login banner (Login View)
This function displays the whole system overview, including number of updates, kernel reboot check, CPU type, RAM info, etc. It's most useful as a login banner.
<br>![SysChecks Login View](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_login_view.png "SysChecks Login View")

## Kernel reboot check
Kernel reboot check compares the running kernel version with a list of installed ones and lets you know if there is a need to reboot the system. It's useful to keep your system up-to-date on a kernel patch level. There are 2 outputs: human and JSON.
<br>![SysChecks Kern Reboot Check](https://github.com/yaroslav-gwit/SysChecks/blob/main/screenshots/syschecks_kern_reboot.png "SysChecks Kern Reboot Check")
