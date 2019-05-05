#
# Copyright (c) 2018, Prethish Bhasuran (prethishb@gmail.com)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE

"""
Script to run nuke batch renders in chunks.Has been tested in windows

 Note::The script assumes that nuke executable
 is available in the command line

Usage:
    eg:
    python render_threads.py -start_frame 1
                          -end_frame 100
                          -script_path /path//to/nuket.nk
                          -chunks 20
                          -frame_step 2
"""

import threading
import os
import sys
import subprocess
import argparse
import logging
import time
import Queue


logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)


def worker(work_queue):
    """ Worker function for the threads

    Args:
        work_queue (Queue): queue object which stores the commands to
                            be run
    """
    while True:
        cmd = work_queue.get()
        run_bash(cmd, mock=False)
        work_queue.task_done()


def generate_frame_chunks(start_frame, end_frame, chunks):
    """ Generator to create the frameranges according to chunk

    Args:
        start_frame (int):
        end_frame (int):
        chunks (int):

    Returns:
        (start,end) (tuple)

    """
    frames_per_chunk = (end_frame - start_frame) / chunks
    start = start_frame
    end = 0
    for nChunk in xrange(chunks):
        if end:
            start = end + 1
        end = start + frames_per_chunk
        if end > end_frame:
            end = end_frame
        yield start, end


def render_nuke(start_frame, end_frame, nukescript, step=None, chunks=None):
    """ Function to render the frame in threads according to thread count

    Args:
        start_frame (int):
        end_frame (int):
        nukescript (str):
        step (int):
        chunks (int):
    """
    thread_limit = 10

    frame_range = '{start_frame}-{end_frame}%s' % (
        'x%s' % (step) if step > 1 else '')
    cmd = 'nuke -F {frame_range} -x {nukescript}'
    if chunks <= 1:
        run_bash(
            cmd.format(
                frame_range=frame_range.format(
                    start_frame=start_frame,
                    end_frame=end_frame,
                ),
                nukescript=nukescript
            )
        )
    else:

        print 'Rendering {0}-{1} in {2} chunks'.format(
            start_frame,
            end_frame,
            chunks
        )

        work_queue = Queue.Queue()
        # creating the threads
        thread_count = thread_limit if chunks > thread_limit else chunks
        print 'Starting {} threads to render images using nuke'.format(thread_count)
        for i in xrange(thread_count):
            t = threading.Thread(
                target=worker,
                args=(work_queue,)
            )
            t.setDaemon(True)
            t.start()

        for start, end in generate_frame_chunks(start_frame, end_frame, chunks):
            cmd_worker = cmd.format(
                frame_range=frame_range.format(
                    start_frame=start,
                    end_frame=end
                ),
                nukescript=nukescript,
            )
            work_queue.put(cmd_worker)

        work_queue.join()


def run_bash(cmd, mock=False):
    """ run bash command as a subprocess
    Args:
        cmd (str):
        mock (bool):
    """

    logging.debug('Running bash command {0}'.format(cmd))

    if mock:
        time.sleep(2)
        return

    _cmd = cmd.split()
    # setting this so that in windows it can find a bat file from PATH
    run_in_shell = True if sys.platform == 'win32' else False
    process = subprocess.Popen(
        _cmd, stdout=subprocess.PIPE, shell=run_in_shell)
    out, err = process.communicate()

    # print only errors
    if process.returncode != 0:
        print out
        print err


def get_arguments():
    '''get the command line arguments using argparse

    Returns:
        args (dict)
    '''
    parser = argparse.ArgumentParser(
        description='NukeRender in threads',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '-script_path',
        action='store',
        help='path to nuke script',
        type=str,
        required=True
    )

    parser.add_argument(
        '-start_frame',
        action='store',
        help='start frame of frame range',
        type=int,
        required=True
    )

    parser.add_argument(
        '-end_frame',
        help='end frame of frame range',
        action='store',
        type=int,
        required=True
    )

    parser.add_argument(
        '-frame_step',
        help='render in steps,ie a step of 2 will render 2,4,6,8..',
        action='store',
        type=int,
        default=1
    )

    parser.add_argument(
        '-chunks',
        help='thread count, there is a thread limit of 10, '
             'anything beyond 10 will cause the frame-range per thread'
             'to become less and it will queue the renders',
        action='store',
        type=int,
        default=1
    )

    return vars(parser.parse_args())


if __name__ == '__main__':
    args = get_arguments()

    render_nuke(
        args['start_frame'],
        args['end_frame'],
        args['script_path'],
        args['frame_step'],
        args['chunks']
    )
