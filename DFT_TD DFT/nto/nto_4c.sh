#!/bin/bash
#BSUB -R "same[model] span[ptile='!',Intel_EM64T:16,Intel_a:20,Intel_b:20,Intel_h:32]"
#BSUB -q q_htc
#BSUB -oo orca.%J.o
#BSUB -eo orca.%J.e
#BSUB -m "g1 g2_a g2_b g6"
#BSUB -n 16

module purge
source /tmpu/scunam/config/tipo_nodo.sh
export OMPI_MCA_btl_openib_allow_ib="true"

module load orca/6.1
input=ntos_4c.inp

sed -i "s/\(.*NPROCS\)\(.*\)/\1 $LSB_DJOB_NUMPROC END/g" $input

${ORCA}/orca $input > $input.out.$x.`date +%d-%h-%y.%H:%M `