#!/usr/bin/env bash

# CHECK IF USER HAS SUDO RIGHTS
if [[ ${EUID} != 0 ]]; then
    echo "Please run this installation script as root!" && exit 1
fi

# SET THE LOG CONFIG LOCATION
LOG_FILE=/var/log/automatic_security_updates.log

# DETECT THE OS TYPE AND START THE UPGRADE
if [[ $(grep "ID=" /etc/os-release | grep -c "ubuntu\|debian") > 0 ]]; then
    grep -i security /etc/apt/sources.list > /etc/apt/security.sources.list

    # DOCKER UPDATES ARE LOCKED TO AVOID THE CONTAINER FAILURES
    apt-mark hold docker*
    apt-mark hold containerd*

    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    apt-get update 2>&1 >> ${LOG_FILE}
    apt-get --yes upgrade -o Dir::Etc::SourceList=/etc/apt/security.sources.list -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" 2>&1 >> ${LOG_FILE}

    # DOCKER UPDATES ARE ENABLED AGAIN AT THE END OF THE PROCESS
    apt-mark unhold docker*
    apt-mark unhold containerd*

elif [[ $(grep "ID=" /etc/os-release | grep -c "centos") > 0 ]]; then
    yum install -y yum-plugin-versionlock 2>&1 /dev/null

    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    # DOCKER UPDATES ARE LOCKED TO AVOID CONTAINER FAILURES
    yum versionlock docker* 2>&1 >> ${LOG_FILE}
    yum versionlock containerd* 2>&1 >> ${LOG_FILE}

    yum updateinfo info security 2>&1 >> ${LOG_FILE}
    yum -y update --security 2>&1 >> ${LOG_FILE}

    # DOCKER UPDATES ARE ENABLED AGAIN AT THE END OF THE PROCESS
    yum versionlock delete docker* 2>&1 >> ${LOG_FILE}
    yum versionlock delete containerd* 2>&1 >> ${LOG_FILE}

elif [[ $(grep "ID=" /etc/os-release | grep -c 'almalinux\|\"ol\"') > 0 ]]; then
    dnf install -y python3-dnf-plugin-versionlock 2>&1 /dev/null

    echo "" >> ${LOG_FILE} && echo "" >> ${LOG_FILE}
    echo "#_ $(date) _#" >> ${LOG_FILE}

    # DOCKER UPDATES ARE LOCKED TO AVOID CONTAINER FAILURES
    dnf versionlock docker* 2>&1 >> ${LOG_FILE}
    dnf versionlock containerd* 2>&1 >> ${LOG_FILE}

    dnf updateinfo info security 2>&1 >> ${LOG_FILE}
    dnf -y update --security 2>&1 >> ${LOG_FILE}

    # DOCKER UPDATES ARE ENABLED AGAIN AT THE END OF THE PROCESS
    dnf versionlock delete docker* 2>&1 >> ${LOG_FILE}
    dnf versionlock delete containerd* 2>&1 >> ${LOG_FILE}

else
    echo "Sorry your OS is not yet supported!" && exit 1

fi
