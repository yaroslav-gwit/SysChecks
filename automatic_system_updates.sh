#!/usr/bin/env bash

# CHECK IF USER HAS SUDO RIGHTS
if [[ ${EUID} != 0 ]]; then
    echo "Please run this installation script as root!" && exit 1
fi

# SET THE LOG CONFIG LOCATION
LOG_FILE=/var/log/automatic_system_updates.log

# DETECT THE OS TYPE AND START THE UPGRADE
if [[ $(grep "ID=" /etc/os-release | grep -c "ubuntu\|debian") > 0 ]]; then
    if [[ -f ${LOG_FILE} ]]; then echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}; fi
    echo "#_ $(date) _#" >> ${LOG_FILE}
    DEBIAN_FRONTEND=noninteractive
    APT_LISTCHANGES_FRONTEND=none
    apt-get update 2>&1 | tee -a ${LOG_FILE}
    apt-get dist-upgrade -f -u -y --allow-downgrades --allow-remove-essential --allow-change-held-packages -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" 2>&1 | tee -a ${LOG_FILE}

elif [[ $(grep "ID=" /etc/os-release | grep -c "centos") > 0 ]]; then
    if [[ -f ${LOG_FILE} ]]; then echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}; fi
    echo "#_ $(date) _#" >> ${LOG_FILE}
    yum -y update 2>&1 | tee -a ${LOG_FILE}

elif [[ $(grep "^ID=" /etc/os-release | grep -c 'almalinux\|"ol"\|"rocky"') > 0 ]]; then
    if [[ -f ${LOG_FILE} ]]; then echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}; fi
    echo "#_ $(date) _#" >> ${LOG_FILE}
    dnf -y update 2>&1 | tee -a ${LOG_FILE}

else
    echo "Sorry your OS is not yet supported!" && exit 1
    exit 1

fi

syschecks updates --cache-create
syschecks
