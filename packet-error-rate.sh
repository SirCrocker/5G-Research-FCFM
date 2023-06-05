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
if [ $# -gt 0 ];then
{
    myfolder=$1

}
fi
echo $myfolder


serverID=`grep serverID ${myfolder}/graph.ini | cut -d " " -f 3`
flowType=`grep flowType ${myfolder}/graph.ini | cut -d " " -f 3`
#echo $serverID

filename="tcp-all-ascii.txt"
if [ -f $myfolder/$filename.gz ]; then
{
    printf "Uncompressing..." 
    gunzip $myfolder/$filename.gz
}
fi

if [ "$flowType" == "TCP" ]; then
{
    printf "PER..."
    cat $myfolder/$filename |grep /NodeList/$serverID | awk '\
    {
        if($1=="t"){
            size=substr($38,7,length($38)-7);
            SN=substr($32,5,length($32)-4)+size;
            T[SN]=$2;
            L[SN]=$23;
            ACK[SN]=0;
            Btx[$2]+=$23;
            Ptx[$2]++;     
            Bdrop[$2]+=$23;
            Pdrop[$2]++;
        }
        if($1=="r"){
            SN=substr($33,5,length($33)-4);
            if(ACK[SN]==0){
                Bdrop[T[SN]]-=L[SN];
                Pdrop[T[SN]]--;
                ACK[SN]=1;
            }

        }
    }
    END {OFS="\t"; print "Time","BytesTx","BytesDroped","PacketsTx","PacketsDroped";
    for (c in Btx) print  c, Btx[c],Bdrop[c],Ptx[c],Pdrop[c]} 
    ' | sort -n  > $myfolder/"tcp-per.txt"



    # cat $myfolder/$filename |grep /NodeList/$serverID | awk '\
    # { i = 1 }\
    # {len=0;
    # while ( i <= NF )
    # {
    #     if(substr($i,1,7) == "length:") {len=$(i+1)}
    #     if(($1== "t") && (substr($i,1,4) == "Seq=")) {
    #         SN=substr($i,5,length($i)-4);
    #         T[SN]=$2;
    #         L[SN]=len;
    #         ACK[SN]=0;
    #         Btx[$2]+=len;
    #         Ptx[$2]++;     
    #         Bdrop[$2]+=len;
    #         Pdrop[$2]++;
    #         break;
    #     }
    #     if(($1== "r") && (substr($i,1,4) == "Ack=")) {
    #         SN=substr($i,5,length($i)-4);
    #         if(ACK[SN]==0){
    #             Bdrop[T[SN]]-=L[SN];
    #             Pdrop[T[SN]]--;
    #             ACK[SN]=1;
    #         }
    #         break;
    #     }
    #     i++ 
    # }
    # }
    # END {OFS="\t"; print "Time","BytesTx","BytesDroped","PacketsTx","PacketsDroped";
    # for (c in Btx) print  c, Btx[c],Bdrop[c],Ptx[c],Pdrop[c]} 
    # ' | sort -n  > $myfolder/"tcp-per.txt"

    printf "delay..."
    cat $myfolder/$filename |grep /NodeList/$serverID | awk '\
    {
        if($1=="t"){
            size=substr($38,7,length($38)-7);
            SN=substr($32,5,length($32)-4)+size;
            if(delay[SN]==""){
                delay[SN]=-$2;
                time[SN]=$2;
            }
        }
        if($1=="r"){
            SN=substr($33,5,length($33)-4);
            if(delay[SN] != "" ){
                if(delay[SN]<0) delay[SN]+=$2;
                else delay[SN]=$2-time[SN];
            }
        }
    }
    END {OFS="\t"; 
    print "Time","seq","rtt";
    for (c in delay) {if(delay[c]>0) print  time[c],c, delay[c]} 
    }' | sort -n > $myfolder/"tcp-delay.txt"

    # cat $myfolder/$filename |grep /NodeList/$serverID | awk '\
    # { i = 1 }\
    # {len=0;
    # while ( i <= NF )
    # {
    #     if(($1== "t") && (substr($i,1,4) == "Seq=")) {
    #         sec=substr($i,5,length($i)-4);
    #         if(delay[sec]==""){delay[sec]=-$2; time[sec]=$2;}
    #         break;
    #     }
    #     if(($1== "r") && (substr($i,1,4) == "Ack=")) {
    #         sec=substr($i,5,length($i)-4);
    #         if(delay[sec] != "" ){
    #             if(delay[sec]<0) delay[sec]+=$2;
    #             else delay[sec]=$2-time[sec];
    #             }
    #         break;

    #     }
    #     i++ 
    # }
    # }
    # END {OFS="\t"; 
    # print "Time","seq","rtt";
    # for (c in delay) if(delay[c]>0) print  time[c],c, delay[c]} 
    # ' | sort -n > $myfolder/"tcp-delay.txt"
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

if [ -f $myfolder/$filename ]; then
{
    printf "Compressing..." 
    gzip $myfolder/$filename
}
fi
toc=$(date +%s)
printf "Elapsed Time: "${magenta}$(($toc-$tic))${clear}" seconds\n"