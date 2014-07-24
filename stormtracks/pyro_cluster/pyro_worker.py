#!/usr/bin/python
import socket
import datetime as dt
import time

import Pyro4

from stormtracks.c20data import C20Data, GlobalEnsembleMember
from stormtracks.tracking import VortmaxFinder, VortmaxNearestNeighbourTracker
from stormtracks.match import match
from stormtracks.ibtracsdata import IbtracsData
from stormtracks.load_settings import pyro_settings
from stormtracks.results import StormtracksResultsManager
from stormtracks.analysis import TrackingAnalysis
from stormtracks.logger import Logger
from stormtracks.pyro_cluster.pyro_task import TASKS

hostname = socket.gethostname()
short_hostname = hostname.split('.')[0]
log = Logger('pyro_worker', 'pyro_worker_{0}.log'.format(short_hostname), 'INFO').get()


class PyroWorker(object):
    '''Runs on each of the worker servers

    Listens for do_work requests by pyro_manager, on receiving of a test
    does the required work and saves it to disk using a results manager.
    '''
    def __init__(self):
        self.best_tracks_by_year = {}

    def do_work(self, year, ensemble_member, task_name, task_data):
        '''Do the work required by pyro_manager

        :param year: year to analyse
        :param ensemble_member: ensemble_member to analyse
        :param task: task to do (currently must be 'vort_track')
        :returns: dict containing details of task
        '''
        if task_name not in TASKS:
            raise Exception('Unkown task {0}'.format(task_name))

        try:
            # Dispatch based on task_name.
            if task_name == 'vort_tracking':
                return self.do_vort_tracking(year, ensemble_member)
            elif task_name == 'analysis':
                return self.do_analysis(year, ensemble_member, task_data)
        except Exception, e:
            log.error(e.message)
            response = {
                'status': 'failure',
                'exception': e,
                'server': short_hostname,
                }
            return response

    def do_vort_tracking(self, year, ensemble_member):
        log.info('Received request for vort_tracking for year {0} ensemble {1}'.format(
            year, ensemble_member))

        if year in self.best_tracks_by_year.keys():
            best_tracks = self.best_tracks_by_year[year]
        else:
            log.info('Loading best_tracks for year {0}'.format(year))
            ibt = IbtracsData(verbose=False)
            best_tracks = ibt.load_ibtracks_year(year)
            self.best_tracks_by_year[year] = best_tracks

        results_manager = StormtracksResultsManager('pyro_vort_tracking')

        start = time.time()

        c20data = C20Data(year, verbose=False)
        gdata = GlobalEnsembleMember(c20data, ensemble_member)

        log.debug('Processing')
        vort_finder = VortmaxFinder(gdata)
        vort_finder.find_vort_maxima(dt.datetime(year, 6, 1), dt.datetime(year, 12, 1))

        tracker = VortmaxNearestNeighbourTracker()
        tracker.track_vort_maxima(vort_finder.vortmax_time_series)

        matches = match(tracker.vort_tracks_by_date, best_tracks)
        # Quick to execute, no need to store.
        # good_matches = [ma for ma in matches.values() if ma.av_dist() < 5 and ma.overlap > 6]

        log.debug('Saving data')
        results_manager.add_result(year, ensemble_member, 'vortmax_time_series',
                                   vort_finder.vortmax_time_series)
        results_manager.add_result(year, ensemble_member, 'vort_tracks_by_date',
                                   tracker.vort_tracks_by_date)
        results_manager.add_result(year, ensemble_member, 'matches',
                                   matches)

        results_manager.save()
        end = time.time()

        log.info('Found {0} matches in {1}s'.format(len(matches.values()), end - start))

        response = {
            'status': 'complete',
            'time_taken': end - start,
            }

        return response

    def do_analysis(self, year, ensemble_member, result_key):
        log.info('Received request for analysis for year {0} ensemble {1}'.format(
            year, ensemble_member))
        log.info('Analysis data {0}'.format(result_key))

        start = time.time()

        results_manager = StormtracksResultsManager('pyro_analysis')
        analysis = TrackingAnalysis(year, ensemble_member)

        result = analysis.run_individual_analysis_from_result_key(result_key)

        results_manager.add_result(year, ensemble_member, result_key, result)
        results_manager.save()

        end = time.time()
        response = {
            'status': 'complete',
            'time_taken': end - start,
            }
        return response


def main():
    '''Sets up a PyroWorker and starts its event loop to wait for calls from a pyro_manager'''
    hostname = socket.gethostname()
    short_hostname = hostname.split('.')[0]
    worker = PyroWorker()

    if pyro_settings.is_ucl:
        daemon = Pyro4.Daemon(host=short_hostname)
    else:
        daemon = Pyro4.Daemon(host='192.168.0.2')

    ns = Pyro4.locateNS()
    uri = daemon.register(worker)   # register the greeting object as a Pyro object
    ns.register('stormtracks.worker_{0}'.format(short_hostname), uri)

    log.info('stormtracks.worker_{0}'.format(short_hostname))
    log.info('Ready. Object uri = {0}'.format(uri))

    daemon.requestLoop()            # start the event loop of the server to wait for calls


if __name__ == '__main__':
    main()
