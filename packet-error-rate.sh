#!/usr/bin/bash
# Set text colors
clear='\033[0m'
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'

tic=$(date +%s)

outfolder="./out"

myfolder=$outfolder
if [ $# -gt 0 ];
then
{
    myfolder=$1

}
fi
#echo $myfolder


serverID=`grep serverID ${myfolder}/graph.ini | cut -d " " -f 3`
flowType=`grep flowType ${myfolder}/graph.ini | cut -d " " -f 3`
#echo $serverID

filename="tcp-all-ascii.txt"

if [ "$flowType" == "TCP" ]; then
{
    cat $myfolder/$filename |grep /NodeList/$serverID | awk ' /^t/ \
    { i = 1 }\
    {len=0;
    while ( i <= NF )
    {
        if(substr($i,1,7) == "length:") {len=$(i+1)}
        if(substr($i,1,4) == "Seq=") {
            sec=substr($i,5,length($i)-4);
            seq[sec]++; 
            Btx[$2]+=len;
            Ptx[$2]++;     
            if (seq[sec] > 1){
                Bdrop[$2]+=len;
                Pdrop[$2]++;
            }else{
                Bdrop[$2]+=0;
                Pdrop[$2]+=0;         
            }
        }
        i++ 
    }
    }
    END {OFS="\t"; print "Time","BytesTx","BytesDroped","PacketsTx","PacketsDroped";
    for (c in Btx) print  c, Btx[c],Bdrop[c],Ptx[c],Pdrop[c]} 

    ' | sort -n > $myfolder/"tcp-per.txt"


    cat $myfolder/$filename |grep /NodeList/$serverID | awk '\
    { i = 1 }\
    {len=0;
    while ( i <= NF )
    {
        if(($1== "t") && (substr($i,1,4) == "Seq=")) {
            sec=substr($i,5,length($i)-4);
            if(delay[sec]==""){delay[sec]=-$2; time[sec]=$2;}
        }
        if(($1== "r") && (substr($i,1,4) == "Ack=")) {
            sec=substr($i,5,length($i)-4);
            if(delay[sec] != "" ){
                if(delay[sec]<0) delay[sec]+=$2;
                else delay[sec]=$2-time[sec];
                }

        }
        i++ 
    }
    }
    END {OFS="\t"; 
    print "Time","seq","rtt";
    for (c in delay) if(delay[c]>0) print  time[c],c, delay[c]} 
    ' | sort -n > $myfolder/"tcp-delay.txt"
}
fi

if [ "$flowType" == "UDP" ];
then
{
    cat $myfolder/$filename |grep /NodeList/0 | awk '\
    { i = 1 }\
    {len=0;
    while ( i <= NF )
    {
        if(($1== "r") && (substr($i,1,6) == "((seq=")) {
            sec=substr($i,7,length($i)-4);
            t2=$2
            t1=substr($(i+1),7,length($(i+1))-9);
            size=substr($(i+3),7,length($(i+3))-7) + 20;
            if(delay[sec]=="")
            {
                delay[sec]=t2-t1;
                time[sec]=t2;
                bytes[sec]=size;
            }
        }
        i++ 
    }
    }
    END {OFS="\t"; 
    print "Time","seq","time","bytes";
    for (c in delay) if(delay[c]>0) print  time[c],c, delay[c], bytes[c]} 
    ' | sort -n > $myfolder/"udp-delay.txt"
    
    
    
    

}
fi

gzip $myfolder/$filename &

toc=$(date +%s)
printf "Elapsed Time: "${magenta}$(($toc-$tic))${clear}" seconds\n"