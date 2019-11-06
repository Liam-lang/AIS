#! /bin/bash


mkdir /tmp/$1
chmod 777 /tmp/$1
cp /opt/lenovo/AIS/material/common/* /tmp/$1
# split the commoStr according to the "-"
OLD_IFS="$IFS"
IFS="-"
array=($1)
IFS="$OLD_IFS"
isoname=$1".iso"
if [[ $1 =~ "RHEL" ]];then
    echo "RHEL config file" 
    cp /opt/lenovo/AIS/material/RedHat/* /tmp/$1
    configfile=${1}"-ks.cfg"
    sed -i "s/KS_FILE/$configfile/g" /tmp/$1/PXE1TIME.CFG.bak
    sed -i "s/KS_FILE/$configfile/g" /tmp/$1/EFI1TIME.CFG.bak
    OS_VERSION=${array[0]}"-"${array[1]}"-"${array[2]}
    mount -t iso9660 /var/opt/lenovo/AIS/checkbase/ISO/$isoname /mnt -o loop
    cp /mnt/isolinux/initrd.img /tmp/$1
    cp /mnt/isolinux/vmlinuz /tmp/$1
    umount /mnt
elif [[ $1 =~ "SLE" ]];then
    echo "SUSE config file"
    cp /opt/lenovo/AIS/material/SUSE/* /tmp/$1
    configfile=${1}".xml"
    sed -i "s/INST_FILE/$configfile/g" /tmp/$1/PXE1TIME.CFG.bak
    sed -i "s/INST_FILE/$configfile/g" /tmp/$1/EFI1TIME.CFG.bak
    sed -i "s/ISO_NAME/$isoname/g" /tmp/$1/PXE1TIME.CFG.bak
    sed -i "s/ISO_NAME/$isoname/g" /tmp/$1/EFI1TIME.CFG.bak
    len=${#array[@]}
    if [[ ${array[2]} =~ "SP" ]];then
        OS_VERSION=${array[0]}"-"${array[1]}"-"${array[2]}"-"${array[(($len-2))]}    
 
    else
        OS_VERSION=${array[0]}"-"${array[1]}"-"${array[(($len-2))]}    
    fi
    mount -t iso9660 /var/opt/lenovo/AIS/checkbase/ISO/$isoname /mnt -o loop
    cp /mnt/boot/x86_64/loader/initrd /tmp/$1
    cp /mnt/boot/x86_64/loader/linux /tmp/$1
    umount /mnt
fi
echo "configfile=$configfile"
echo "OS_VERSION=$OS_VERSION"
cp /etc/opt/lenovo/AIS/conf/OSUnattendedFile/$configfile /tmp/$1

cd /tmp/$1 
echo "start tar ...."
tar -czvf ${OS_VERSION}".tar.gz" *
md5sum ${OS_VERSION}".tar.gz" >  ${OS_VERSION}".md5.txt"
cp ${OS_VERSION}".md5.txt" /var/opt/lenovo/AIS/checkbase/ISO/
cp ${OS_VERSION}".tar.gz" /var/opt/lenovo/AIS/checkbase/ISO/
cd
rm -rf /tmp/$1
