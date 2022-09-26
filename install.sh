#!/usr/bin/env bash
if [[ ${EUID} != 0 ]]; then
    echo "Please run this installation script as root!" && exit 1
fi

INSTALL_FOLDER=/opt/syschecks

if [[ $(grep -c ubuntu /etc/os-release) > 0 ]]; then
    apt update
    apt -y install python3-pip python3-venv git

elif [[ $(grep -c debian /etc/os-release) > 0 ]]; then
    apt update
    apt -y install python3-pip python3-venv git

elif [[ $(grep -c centos /etc/os-release) > 0 ]]; then
    yum makecache fast
    yum -y install python3-pip git
    python3 -m pip install virtualenv

elif [[ $(grep -c almalinux /etc/os-release) > 0 ]]; then
    dnf makecache
    dnf -y install python3-pip python3-virtualenv git

else
    echo "Sorry your OS is not yet supported!" && exit 1
fi

mkdir ${INSTALL_FOLDER}
git clone https://github.com/yaroslav-gwit/SysChecks.git ${INSTALL_FOLDER}/

cd ${INSTALL_FOLDER}
python3 -m venv venv
${INSTALL_FOLDER}/venv/bin/python3 -m pip install --upgrade pip
${INSTALL_FOLDER}/venv/bin/python3 -m pip install -r requirements.txt

if [[ -f /bin/syschecks ]]; then
    rm -f /bin/syschecks
fi
ln syschecks /bin/syschecks

echo
echo
echo "The software has been installed!"
