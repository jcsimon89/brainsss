import time
import sys
import os
import re
import json
import textwrap
import brainsss
import argparse

def main(args):

    modules = 'gcc/6.3.0 python/3.6 py-numpy/1.14.3_py36 py-pandas/0.23.0_py36 viz py-scikit-learn/0.19.1_py36 antspy/0.2.2'

    #########################
    ### Setup preferences ###
    #########################

    width = 120 # width of print log
    nodes = 2 # 1 or 2
    nice = True # true to lower priority of jobs. ie, other users jobs go first

    #####################
    ### Setup logging ###
    #####################

    logfile = './logs/' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
    printlog = getattr(brainsss.Printlog(logfile=logfile), 'print_to_log')
    sys.stderr = brainsss.Logger_stderr_sherlock(logfile)
    brainsss.print_title(logfile, width)

    #############################
    ### Parse input arguments ###
    #############################

    ### Get user settings
    #printlog("PWD: {}".format(args['PWD']))
    scripts_path = args['PWD']
    com_path = os.path.join(scripts_path, 'com')
    user = scripts_path.split('/')[3]
    settings = brainsss.load_user_settings(user, scripts_path)

    ### Grab buildflies from command line args first since it will impact parsing
    if args['BUILDFLIES'] == '':
        #printlog('not building flies')
        build_flies = False
    else:
        #printlog('building flies')
        build_flies = True
        dir_to_build = args['BUILDFLIES']

    ### Parse user settings
    imports_path = settings['imports_path']
    dataset_path = settings['dataset_path']
    if build_flies:
        fictrac_qc = brainsss.parse_true_false(settings.get('fictrac_qc',False))
        stim_triggered_beh = brainsss.parse_true_false(settings.get('stim_triggered_beh',False))
        bleaching_qc = brainsss.parse_true_false(settings.get('bleaching_qc',False))
        temporal_mean_brain_pre = brainsss.parse_true_false(settings.get('temporal_mean_brain_pre',False))
        motion_correction = brainsss.parse_true_false(settings.get('motion_correction',False))
        temporal_mean_brain_post = brainsss.parse_true_false(settings.get('temporal_mean_brain_post',False))
        zscore = brainsss.parse_true_false(settings.get('zscore',False))
        highpass = brainsss.parse_true_false(settings.get('highpass',False))
        correlation = brainsss.parse_true_false(settings.get('correlation', False))
        STA = brainsss.parse_true_false(settings.get('STA', False))
        h5_to_nii = brainsss.parse_true_false(settings.get('h5_to_nii', False))
        use_warp = brainsss.parse_true_false(settings.get('use_warp', False))
    else:
        fictrac_qc = False
        stim_triggered_beh = False
        bleaching_qc = False
        temporal_mean_brain_pre = False
        motion_correction = False
        temporal_mean_brain_post = False
        zscore = False
        highpass = False
        correlation = False
        STA = False
        h5_to_nii = False
        use_warp = False
        loco_dataset = False


    ### Parse remaining command line args
    if args['FLIES'] == '':
        #printlog('no flies specified')
        fly_dirs = None
    else:
        fly_dirs = args['FLIES'].split(',')

        ### add 'fly_' to beginning if it isn't there
        for i in range(len(fly_dirs)):
            if not fly_dirs[i].startswith('fly_'):
                fly_dirs[i] = 'fly_' + fly_dirs[i]

    if args['DIRTYPE'] == '':
        #printlog('no dirtype specified')
        dirtype = None
    else:
        dirtype = args['DIRTYPE'].lower()
        #printlog('dirtype is {}'.format(dirtype))

    # These command line arguments will be empty unless the flag is called from the command line
    if args['FICTRAC_QC'] != '':
        fictrac_qc = True
    if args['STB'] != '':
        stim_triggered_beh = True
    if args['BLEACHING_QC'] != '':
        bleaching_qc = True
    if args['TEMPORAL_MEAN_BRAIN_PRE'] != '':
        temporal_mean_brain_pre = True
    if args['MOCO'] != '':
        motion_correction = True
    if args['TEMPORAL_MEAN_BRAIN_POST'] != '':
        temporal_mean_brain_post = True
    if args['ZSCORE'] != '':
        zscore = True
    if args['HIGHPASS'] != '':
        highpass = True
    if args['CORRELATION'] != '':
        correlation = True
    if args ['STA'] != '':
        STA = True
    if args ['H5_TO_NII'] != '':
        h5_to_nii = True
    if args ['USE_WARP'] != '':
        use_warp = True
    if args ['LOCO_DATASET'] != '':
        loco_dataset = True

    ### catch errors with incorrect argument combos
    # if fly builder is false, fly dirs must be provided
    if not build_flies and fly_dirs is None:
        printlog("ERROR: you did not provide a directory to build flies from, nor a fly directory to process.")
        printlog("Aborting.")
        return

    # quickly testing using global sherlock resources
    # if user == 'brezovec':
    #     global_resources = True
    # else:
    #     global_resources = False

    #################################
    ############# BEGIN #############
    #################################

    if build_flies:

        ######################
        ### CHECK FOR FLAG ###
        ######################

        # args = {'logfile': logfile, 'imports_path': imports_path}
        # script = 'check_for_flag.py'
        # job_id = brainsss.sbatch(jobname='flagchk',
        #                      script=os.path.join(scripts_path, script),
        #                      modules=modules,
        #                      args=args,
        #                      logfile=logfile, time=1, mem=1, nice=nice, nodes=nodes)
        # flagged_dir = brainsss.wait_for_job(job_id, logfile, com_path)

        ###################
        ### Build flies ###
        ###################

        flagged_dir = os.path.join(imports_path, dir_to_build)
        args = {'logfile': logfile, 'flagged_dir': flagged_dir, 'dataset_path': dataset_path, 'fly_dirs': fly_dirs, 'user': user}
        script = 'fly_builder.py'
        job_id = brainsss.sbatch(jobname='bldfly',
                             script=os.path.join(scripts_path, script),
                             modules=modules,
                             args=args,
                             logfile=logfile, time=1, mem=1, nice=nice, nodes=nodes)
        func_and_anats = brainsss.wait_for_job(job_id, logfile, com_path)
        func_and_anats = func_and_anats.split('\n')[:-1]
        funcs = [x.split(':')[1] for x in func_and_anats if 'func:' in x] # will be full paths to fly/expt
        anats = [x.split(':')[1] for x in func_and_anats if 'anat:' in x]

    else:
        funcs = []
        anats = []
        for fly_dir in fly_dirs:
            fly_directory = os.path.join(dataset_path, fly_dir)
            if dirtype == 'func' or dirtype == None:
                funcs.extend([os.path.join(fly_directory, x) for x in os.listdir(fly_directory) if 'func' in x])
            if dirtype == 'anat'or dirtype == None:
                anats.extend([os.path.join(fly_directory, x) for x in os.listdir(fly_directory) if 'anat' in x])

    brainsss.sort_nicely(funcs)
    brainsss.sort_nicely(anats)
    funcanats = funcs + anats
    dirtypes = ['func']*len(funcs) + ['anat']*len(anats)

    if fictrac_qc:

        ##################
        ### Fictrac QC ###
        ##################

        job_ids = []
        for func in funcs:
            directory = os.path.join(func, 'fictrac')
            if os.path.exists(directory):
                args = {'logfile': logfile, 'directory': directory, 'fps': 100}
                script = 'fictrac_qc.py'
                job_id = brainsss.sbatch(jobname='fictracqc',
                                     script=os.path.join(scripts_path, script),
                                     modules=modules,
                                     args=args,
                                     logfile=logfile, time=1, mem=1, nice=nice, nodes=nodes)
                job_ids.append(job_id)
        for job_id in job_ids:
            brainsss.wait_for_job(job_id, logfile, com_path)

    if stim_triggered_beh:

        ##########################
        ### Stim Triggered Beh ###
        ##########################

        for func in funcs:
            args = {'logfile': logfile, 'func_path': func}
            script = 'stim_triggered_avg_beh.py'
            job_id = brainsss.sbatch(jobname='stim',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=1, mem=2, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if bleaching_qc:

        ####################
        ### Bleaching QC ###
        ####################

        #job_ids = []
        for funcanat, dirtype in zip(funcanats, dirtypes):
            directory = os.path.join(funcanat, 'imaging')
            args = {'logfile': logfile, 'directory': directory, 'dirtype': dirtype}
            script = 'bleaching_qc.py'
            job_id = brainsss.sbatch(jobname='bleachqc',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=1, mem=2, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if temporal_mean_brain_pre:

        #######################################
        ### Create temporal mean brains PRE ###
        #######################################

        for funcanat, dirtype in zip(funcanats, dirtypes):
            directory = os.path.join(funcanat, 'imaging')

            if dirtype == 'func':
                files = ['functional_channel_1.nii', 'functional_channel_2.nii']
            if dirtype == 'anat':
                files = ['anatomy_channel_1.nii', 'anatomy_channel_2.nii']

            args = {'logfile': logfile, 'directory': directory, 'files': files}
            script = 'make_mean_brain.py'
            job_id = brainsss.sbatch(jobname='meanbrn',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=1, mem=2, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if motion_correction:

        #########################
        ### Motion Correction ###
        #########################

        for funcanat, dirtype in zip(funcanats, dirtypes):

            directory = os.path.join(funcanat, 'imaging')
            if dirtype == 'func':
                brain_master = 'functional_channel_1.nii'
                brain_mirror = 'functional_channel_2.nii'
            if dirtype == 'anat':
                brain_master = 'anatomy_channel_1.nii'
                brain_mirror = 'anatomy_channel_2.nii'

            args = {'logfile': logfile,
                    'directory': directory,
                    'brain_master': brain_master,
                    'brain_mirror': brain_mirror,
                    'scantype': dirtype}

            script = 'motion_correction.py'
            # if global_resources:
            #     dur = 48
            #     mem = 8
            # else:
            #     dur = 96
            #     mem = 4
            global_resources = True
            dur = 48
            mem = 8
            job_id = brainsss.sbatch(jobname='moco',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=dur, mem=mem, nice=nice, nodes=nodes, global_resources=global_resources)
        ### currently submitting these jobs simultaneously since using global resources
        brainsss.wait_for_job(job_id, logfile, com_path)

    if zscore:

        ##############
        ### ZSCORE ###
        ##############

        for func in funcs:
            load_directory = os.path.join(func, 'moco')
            save_directory = os.path.join(func)
            brain_file = 'functional_channel_2_moco.h5'

            args = {'logfile': logfile, 'load_directory': load_directory, 'save_directory': save_directory, 'brain_file': brain_file}
            script = 'zscore.py'
            job_id = brainsss.sbatch(jobname='zscore',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=1, mem=2, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if highpass:

        ################
        ### HIGHPASS ###
        ################

        for func in funcs:
            load_directory = os.path.join(func)
            save_directory = os.path.join(func)
            brain_file = 'functional_channel_2_moco_zscore.h5'

            args = {'logfile': logfile, 'load_directory': load_directory, 'save_directory': save_directory, 'brain_file': brain_file}
            script = 'temporal_high_pass_filter.py'
            job_id = brainsss.sbatch(jobname='highpass',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=4, mem=2, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if correlation:

        ###################
        ### CORRELATION ###
        ###################

        for func in funcs:
            load_directory = os.path.join(func)
            save_directory = os.path.join(func, 'corr')
            if use_warp:
                brain_file = 'functional_channel_2_moco_zscore_highpass_warped.nii'
                fps = 100
            elif loco_dataset:
                brain_file = 'brain_zscored_green_high_pass_masked.nii'
                fps = 50
            else:
                brain_file = 'functional_channel_2_moco_zscore_highpass.h5'
                fps =100

            behaviors = ['dRotLabZneg', 'dRotLabZpos', 'dRotLabY']
            for behavior in behaviors:

                args = {'logfile': logfile, 'load_directory': load_directory, 'save_directory': save_directory, 'brain_file': brain_file, 'behavior': behavior, 'fps': fps}
                script = 'correlation.py'
                job_id = brainsss.sbatch(jobname='corr',
                                     script=os.path.join(scripts_path, script),
                                     modules=modules,
                                     args=args,
                                     logfile=logfile, time=2, mem=4, nice=nice, nodes=nodes)
                brainsss.wait_for_job(job_id, logfile, com_path)

    if STA:

        #########################################
        ### STIMULUS TRIGGERED NEURAL AVERAGE ###
        #########################################

        for func in funcs:
            args = {'logfile': logfile, 'func_path': func}
            script = 'stim_triggered_avg_neu.py'
            job_id = brainsss.sbatch(jobname='STA',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=4, mem=4, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if h5_to_nii:

        #################
        ### H5 TO NII ###
        #################

        for func in funcs:
            args = {'logfile': logfile, 'h5_path': os.path.join(func, 'functional_channel_2_moco_zscore_highpass.h5')}
            script = 'h5_to_nii.py'
            job_id = brainsss.sbatch(jobname='h5tonii',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=2, mem=10, nice=nice, nodes=nodes)
            brainsss.wait_for_job(job_id, logfile, com_path)

    if temporal_mean_brain_post:

        #########################################
        ### Create temporal mean brains, POST ###
        #########################################

        for funcanat, dirtype in zip(funcanats, dirtypes):
            directory = os.path.join(funcanat, 'moco')

            if dirtype == 'func':
                files = ['functional_channel_1_moco.h5', 'functional_channel_2_moco.h5']
            if dirtype == 'anat':
                files = ['anatomy_channel_1_moco.h5', 'anatomy_channel_2_moco.h5']

            args = {'logfile': logfile, 'directory': directory, 'files': files}
            script = 'make_mean_brain.py'
            job_id = brainsss.sbatch(jobname='meanbrn',
                                 script=os.path.join(scripts_path, script),
                                 modules=modules,
                                 args=args,
                                 logfile=logfile, time=3, mem=12, nice=nice, nodes=nodes, global_resources=True)
        brainsss.wait_for_job(job_id, logfile, com_path)

    ############
    ### Done ###
    ############

    brainsss.print_footer(logfile, width)

if __name__ == '__main__':
    main(json.loads(sys.argv[1]))
    # parser = argparse.ArgumentParser()
    # parser.add_argument("PWD") 
    # args = parser.parse_args()
    # main(args)