"""
- debug and check if all settings work out form command line
- investigate all outputs (regarding also things not checked so far, eg metacognition etc)
"""


from code.TUN_sess import TuningSession
from datetime import datetime
import sys
import pandas as pd
import os
import json

def main():
    sub = sys.argv[1] # which subject (XX)
    ses =  sys.argv[2] # which session (XX)
    run = sys.argv[3] # which run (XX)
    task = 'TUN' # which task
    settings = f'settings/settings_{task}.yml' # grab settings
    dt = datetime.now().strftime('%Y%m%d%H%M%S') # get time to avoid overwriting

    # eyetracking yes/no
    eyetracker_on=True
    if 'no-et' in sys.argv:
        eyetracker_on = False

    # debug yes/no
    debug=False
    if 'debug' in sys.argv:
        debug = True

    # flicker yes/no
    flicker=False
    if 'flicker' in sys.argv:
        flicker = True

    output_str = f'sub-{sub}_ses-{ses}_task-{task}_run-{run}_dt-{dt}'
    # output_dir_root = '/data1/projects/dumoulinlab/Lab_members/Xaver/sm-ND_taskdata-raw'
    output_dir_root = './MEDTUN_taskdata'
    if 'test' in sys.argv:
        output_dir = os.path.join(output_dir_root, f'TEST/mri/sub-{sub}/ses-{ses}') # test for now
    else:
        output_dir = os.path.join(output_dir_root, f'mri/sub-{sub}/ses-{ses}')

    # Check if the directory already exists
    if not os.path.exists(output_dir):
        # Create the directory
        os.makedirs(output_dir)
        print("output_dir created successfully!")

    else:
        print("output_dir already exists!")

    # seqs_df = pd.read_csv(os.path.join('trial_sequences', 'seqs_df.csv'))
    
    sequence_id = run.zfill(3)
  
    if sequence_id is not None:
        print(f"running task {task} with {settings} for {output_str} with sequence {str(sequence_id).zfill(3)}, data saved in {output_dir}")
    else:
        print(f"running task {task} with {settings} for {output_str}, data saved in {output_dir}")
    
    print(f"eyetracking_on is {eyetracker_on}")


    # initialize
    session = TuningSession(output_str, output_dir = output_dir, eyetracker_on=eyetracker_on,
                            n_trials=None, settings_file=settings, flicker = flicker, sequence_id = sequence_id, photodiode_check = False, debug = debug)
    # create trials
    session.create_trials()
    total_frames = sum([sum(trial.phase_durations) for trial in session.trials[1:-1]]) 
    print(f"Total frames in trials: {total_frames}, total time (s) : {total_frames/120}")

    session.trials
    # run the session
    session.run()
    # TODO is necessary?
    session.quit()

if __name__ == '__main__':
    main()