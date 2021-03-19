# Subsample raw reads files to 0.005% of reads

start=$(date +%s)
echo "start time: $start"

SUBSAMPLE_RATE=0.00005 #as a fraction, out of 1

for file in /data2/JO_Internship_2021/V-V_scripts/GLDS-194/00-RawData/Fastq/*.fastq.gz
do
	echo subsampling $file to `basename $file`
	seqtk sample -s 777 $file $SUBSAMPLE_RATE > `basename $file`
done

end=$(date +%s)
echo "end time: $end"
runtime_s=$(echo $(( end - start )))
echo "total run time(s): $runtime_s"
sec_per_min=60
sec_per_hr=3600
runtime_m=$(echo "scale=2; $runtime_s / $sec_per_min;" | bc)
echo "total run time(m): $runtime_m"
runtime_h=$(echo "scale=2; $runtime_s / $sec_per_hr;" | bc)
echo "total run time(h): $runtime_h"
