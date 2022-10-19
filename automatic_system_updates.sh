#!/usr/bin/env bash

# CHECK IF USER HAS SUDO RIGHTS
if [[ ${EUID} != 0 ]]; then
    echo "Please run this installation script as root!" && exit 1
fi

# SET THE LOG CONFIG LOCATION
LOG_FILE=/var/log/automatic_system_updates.log

# DETECT THE OS TYPE AND START THE UPGRADE
if [[ $(grep "ID=" /etc/os-release | grep -c "ubuntu\|debian") > 0 ]]; then
    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    apt-get update 2>&1 >> ${LOG_FILE}
    apt-get -y dist-upgrade >> ${LOG_FILE}

elif [[ $(grep "ID=" /etc/os-release | grep -c "centos") > 0 ]]; then
    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    yum -y update 2>&1 >> ${LOG_FILE}

elif [[ $(grep "ID=" /etc/os-release | grep -c 'almalinux\|\"ol\"') > 0 ]]; then
    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    dnf -y update 2>&1 >> ${LOG_FILE}

else
    echo "Sorry your OS is not yet supported!" && exit 1

fi
