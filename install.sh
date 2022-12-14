#!/usr/bin/env bash
if [[ ${EUID} != 0 ]]; then
	echo "Please run this installation script as root!" && exit 1
fi

INSTALL_FOLDER=/opt/syschecks

if [[ $(grep "^ID=" /etc/os-release | grep -c "ubuntu\|debian") -gt 0 ]]; then
	apt update
	apt -y install python3-pip python3-venv git
elif [[ $(grep "^ID=" /etc/os-release | grep -c "centos") -gt 0 ]]; then
	yum makecache fast
	yum -y install python3-pip git
	python3 -m pip install virtualenv
elif [[ $(grep "^ID=" /etc/os-release | grep -c 'almalinux\|"ol"\|"rocky"') -gt 0 ]]; then
	dnf makecache
	dnf -y install python3-pip git
	python3 -m pip install virtualenv
else
	echo "Sorry your OS is not yet supported!" && exit 1
fi

mkdir ${INSTALL_FOLDER}
git clone https://github.com/yaroslav-gwit/SysChecks.git ${INSTALL_FOLDER}/

cd ${INSTALL_FOLDER} || (echo "Could not find the installation folder" && exit 1)
python3 -m venv venv
${INSTALL_FOLDER}/venv/bin/python3 -m pip install --upgrade pip
${INSTALL_FOLDER}/venv/bin/python3 -m pip install -r requirements.txt

if [[ -f /bin/syschecks ]]; then
	rm -f /bin/syschecks
fi
ln syschecks /bin/syschecks

syschecks updates --cache-create && syschecks --install-completion && syschecks cron-init && syschecks fix-permissions
(syschecks && echo && echo "The software is now installed!" && echo && exit 0) || (echo "Software installation failed! Try again..." && exit 1)
