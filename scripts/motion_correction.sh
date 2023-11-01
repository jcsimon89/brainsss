#!/bin/bash
#SBATCH --job-name=moco
#SBATCH --partition=trc
#SBATCH --time=8-00:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --output=./logs/mainlog.out
#SBATCH --open-mode=append

date

directory=$1
brain_master=$2
brain_mirror=$3

echo $directory
echo $brain_master
echo $brain_mirror

# Optional params
type_of_transform=${4:-"SyN"}
output_format=${5:-"h5"}
echo $type_of_transform
echo $output_format

args="{\"directory\":\"$directory\",\"brain_master\":\"$brain_master\",\"brain_mirror\":\"$brain_mirror\","\
"\"type_of_transform\":\"$type_of_transform\",\"output_format\":\"$output_format\"}"

source brainsss/bin/activate
ml python/3.6.1
ml py-ants/0.3.2_py36
date
python3 -u ./motion_correction.py $args
