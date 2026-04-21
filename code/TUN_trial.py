# imports exptools and psychopy
from exptools2.core import Trial
from psychopy.visual import Rect, ImageStim
from scipy.signal import find_peaks
from psychopy import event
import random

# other imports
import numpy as np

class TuningTrial(Trial):
    """ Simple trial with text (trial x) and fixation. """
    def __init__(self, session, trial_nr, phase_durations, txt = None, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        
        # get the texture
        self.img = ImageStim(self.session.win, self.parameters['texture_path'], name=self.parameters['texture_path'],#size = 10,
         pos = (self.session.settings['stimuli']['x_offset'], self.session.settings['stimuli']['y_offset']),
                             mask = 'raisedCos', maskParams = {'fringeWidth':0.02}) # proportion that will be blurred
        # self.check_frames = np.zeros((96, 3))
        
        # get the stimulus array with self.session.var_isi/dur_dict and save it into self.stimulus_frames
        if self.parameters['trial_type'] == 'dur':
            self.stimulus_frames = self.session.var_dur_dict[self.parameters['stim_dur']]
            # self.stimulus_frames = self.session.var_dur_dict_flip[self.parameters['stim_dur']]

        else:
            self.stimulus_frames = self.session.var_isi_dict[self.parameters['stim_dur']]
            # self.stimulus_frames = self.session.var_isi_dict_flip[self.parameters['stim_dur']]

        # squares for Photodiode
        if self.session.photodiode_check is True:
            self.white_square = Rect(self.session.win, 2, 2, pos = (5.5,-2.5))
            self.black_square = Rect(self.session.win, 2, 2, pos = (5.5,-2.5), fillColor = 'black')
            if self.parameters['trial_type'] == 'dur':
                self.square_flip_frames = self.session.var_dur_dict_flip[self.parameters['stim_dur']]
                print(self.square_flip_frames)
            else:
                self.square_flip_frames = self.session.var_isi_dict_flip[self.parameters['stim_dur']]

        # used for flicker condition to match frame index to image index
        if self.session.flicker:
            self.frames_to_index = self._generate_index_sequence(self.session.settings['stimuli']['stim_duration'],
                                                             len(self.session.texture_paths) )
        if self.session.debug:
            print(f"made frame index for trial {trial_nr}: {self.frames_to_index}")

    def _generate_index_sequence(self, n_frames: int, n_images: int, frames_per_img = 3) -> list[int]:
        """
        Generate a flat list of image indices where each index repeats 3 times
        before moving to a new random one, with no immediate repeats.
        """
        n_triplets = (n_frames + 2) // frames_per_img # enough triplets to cover all frames
        indices = []
        last = None

        for _ in range(n_triplets):
            choices = [i for i in range(n_images) if i != last]
            chosen = random.choice(choices)
            indices.extend([chosen] * frames_per_img)
            last = chosen

        return indices[:n_frames]  # trim to exact frame count 

    def draw(self):
        """ Draws stimuli 
        This is to be used when flipping on every frame
        """
        # print(np.round(self.session.clock.getTime(), 2), np.round(self.session.clock.getTime(), 3))
        # only outside phase 1:
        # if self.phase != 1:
        #     # fixation dot color change
        #     self.session.switch_fix_color(effective = True)

        if self.session.debug:
            # update debug_message
            self.session.debug_message.setText(f"trial {self.trial_nr}, phase {self.phase},\ntime {self.session.clock.getTime():.2f}, phase duration (s) {self.phase_durations[self.phase]/120:.2f}")
            self.session.debug_message.draw()

        if self.phase == 0: # we are in phase 0, stimulus presentation
            if self.session.photodiode_check is True:
                self.black_square.draw()

            ## if the self.stimulus_frames array at this frame index is one, show the texture, otherwise fix
            if self.stimulus_frames[self.session.trial_frames] == 1:
                # draw texture
                # TODO flicker here in case of flicker setting
                # if flicker:
                #     self.session.images 
                if self.session.flicker:
                    # print(self.session.trial_frames)
                    # print(self.session.trial_frames)
                    self.session.images[self.frames_to_index[self.session.trial_frames]].draw()

                else:
                    self.img.draw()

                # draw fixation
                self.session.default_fix.draw()
                
            else:
                # draw background
                self.session.background.draw()
                # draw fixation 
                self.session.default_fix.draw()

            if self.session.photodiode_check is True:
                if self.square_flip_frames[self.session.trial_frames]:
                    self.white_square.draw()
                else:
                    self.black_square.draw()


        elif self.phase == 1: # we are in phase 1, iti
            
            if self.session.photodiode_check is True:

                # this will oversample, on each draw()! -> TODO correct by putting it outside of draw!
                self.black_square.draw()
                self.session.mic.stop()
                audioClip = self.session.mic.getRecording()
                # plotting for debugging
                # t = np.linspace(0, audioClip.duration, int(np.round(audioClip.sampleRateHz * audioClip.duration)))
                # fig, ax = plt.subplots()
                # ax.plot(t, audioClip.samples[:,1])
                # plt.savefig('audio_recordings/audio_plot_exp.png')

                peaks, _ = find_peaks(audioClip.samples[:,1], height = .3, distance = audioClip.sampleRateHz*1/120) 
                self.session.conditions.append(self.parameters['stim_dur'])
                self.session.trial_type.append(self.parameters['trial_type'])
                self.session.recording_durations.append(audioClip.duration)
                self.session.delta_peaks.append((peaks[1] - peaks[0])/audioClip.sampleRateHz)
                self.session.n_peaks_found.append(len(peaks))
                
                # get recording and save into dict 
                # self.session.recordings[self.parameters['trial_type']][self.parameters['stim_dur']].append(self.session.mic.getRecording())

            # potentially change color either here or in the beginning of draw
            #self.session.switch_fix_color()

            # draw background
            self.session.background.draw()

            # draw fixation
            self.session.default_fix.draw()

    def get_events(self):
        """ Logs responses/triggers """
        events = event.getKeys(timeStamped=self.session.clock)
        
        if events:
            if 'q' in [ev[0] for ev in events]:  # specific key in settings?
                self.session.close()
                self.session.quit()

            for key, t in events:

                if key == self.session.mri_trigger:
                    event_type = 'pulse'
                    
                    ## not exiting based on ts!
                    # if self.phase == 0:
                
                    #     if self.session.photodiode_check is True:
                    #        # start recording
                    #         self.session.mic.start()
                
                    #     self.exit_phase = True

                else:
                    event_type = 'response'
                    dt = None
                    # calculate the dt to last fix color switch
                    # it should just count FAs here
                    if self.session.last_fix_color_switch is None:
                        self.session.n_fas += 1
                    else:
                        dt = t - self.session.last_fix_color_switch
                        if dt < self.session.settings['task']['response interval']:
                            self.session.n_hits += 1
                        elif dt >= self.session.settings['task']['response interval']:
                            self.session.n_fas += 1

                    if self.session.debug:
                        if self.session.last_fix_color_switch is not None:

                            print(f'last switch was {self.session.last_fix_color_switch:.2f}')
                            print(f'pressed key {key} at {t:.2f}, with dt {dt:.2f}')
                        else:
                            pass


                idx = self.session.global_log.shape[0]
                self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idx, 'onset'] = t
                self.session.global_log.loc[idx, 'event_type'] = event_type
                self.session.global_log.loc[idx, 'phase'] = self.phase
                self.session.global_log.loc[idx, 'response'] = key
                if event_type == 'response':
                    self.session.global_log.loc[idx, 'dt'] = dt

                # for param, val in self.parameters.items():
                    # self.session.global_log.loc[idx, param] = val
                for param, val in self.parameters.items():  # add parameters to log
                    if type(val) == np.ndarray or type(val) == list:
                        for i, x in enumerate(val):
                            self.session.global_log.loc[idx, param+'_%4i'%i] = x 
                    else:       
                        self.session.global_log.loc[idx, param] = val

                if self.eyetracker_on:  # send msg to eyetracker
                    msg = f'start_type-{event_type}_trial-{self.trial_nr}_phase-{self.phase}_key-{key}_time-{t}'
                    self.session.tracker.sendMessage(msg)

                #self.trial_log['response_key'][self.phase].append(key)
                #self.trial_log['response_onset'][self.phase].append(t)
                #self.trial_log['response_time'][self.phase].append(t - self.start_trial)

                if key != self.session.mri_trigger:
                    self.last_resp = key
                    self.last_resp_onset = t

        return events


    def run(self):
        """ Runs through phases. Should not be subclassed unless
        really necessary. """

        if self.eyetracker_on:  # Sets status message
            cmd = f"record_status_message 'trial {self.trial_nr}'"
            self.session.tracker.sendCommand(cmd)

        # Because the first flip happens when the experiment starts,
        # we need to compensate for this during the first trial/phase
        if self.session.first_trial:
            # must be first trial/phase
            if self.timing == 'seconds':  # subtract duration of one frame
                self.phase_durations[0] -= 1./self.session.actual_framerate * 1.1  # +10% to be sure
            else:  # if timing == 'frames', subtract one frame 
                self.phase_durations[0] -= 1
            
            self.session.first_trial = False

        for phase_dur in self.phase_durations:  # loop over phase durations
            self.session.trial_frames = 0

            # pass self.phase *now* instead of while logging the phase info.
            self.session.win.callOnFlip(self.log_phase_info, phase=self.phase)

            # Start loading in next trial during this phase (if not None)
            if self.load_next_during_phase == self.phase:
                self.load_next_trial(phase_dur)

            if self.timing == 'seconds':
                # Loop until timer is at 0!
                self.session.timer.add(phase_dur)
                while self.session.timer.getTime() < 0 and not self.exit_phase and not self.exit_trial:
                    self.draw()
                    if self.draw_each_frame:
                        self.session.win.flip()
                        self.session.nr_frames += 1
                        self.session.trial_frames += 1

                    self.get_events()
            else:
                # Loop for a predetermined number of frames
                # Note: only works when you're sure you're not 
                # dropping frames

                for frame in range(phase_dur):
                    
                    if frame == 0:
                        event.clearEvents()

                    if self.exit_phase or self.exit_trial:
                        break
                    
                    # draw stimuli
                    self.draw()
                    
                    # keeping track of flip timings
                    if self.phase == 0:
                        self.session.trialwise_frame_timings[frame, self.trial_nr] = self.session.win.flip()
                        self.get_events()   
                    
                    else:
                        self.session.win.flip()                
                        # getting events only outside phase 1 makes a difference for frame timings?
                        self.get_events()   
                    self.session.nr_frames += 1
                    self.session.trial_frames += 1

            if self.exit_phase:  # broke out of phase loop
                self.session.timer.reset()  # reset timer!
                self.exit_phase = False  # reset exit_phase
            if self.exit_trial:
                self.session.timer.reset()
                break

            self.phase += 1  # advance phase 
            if self.phase > 1: #??
                self.phase = 0     
