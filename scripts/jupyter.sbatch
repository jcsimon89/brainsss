#!/bin/bash
#
#SBATCH --job-name=jupyter
#SBATCH --output=/home/users/jcsimon/logs/jobs/jupyter.log
#SBATCH --time=1-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --partition=trc

cat /etc/hosts | grep $(hostname)

ml load py-jupyter/1.0.0_py36
ml python/3.6.1
ml py-ants/0.3.2_py36
source $HOME/venvs/brainsss/bin/activate

cd

jupyter notebook --ip=0.0.0.0 --port=8888
