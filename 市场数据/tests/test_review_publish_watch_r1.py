"""Watcher loop/notification tests use local bare Git, never real messaging."""
import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from tests import test_review_publish_sync as fixture
import sync_watchdog_candidate as sync

class WatchR1(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.SyncTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root,self.repo=self.fixture.root,self.fixture.repo

    def test_once_notifies_only_after_remote_confirmation_and_once_per_revision(self):
        self.assertTrue(hasattr(sync,'run_once'))
        notifications=[]
        hook=self.fixture.remote/'hooks'/'pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n',encoding='utf-8')
        bad=sync.run_once(self.root,self.repo,d=fixture.D,notify=notifications.append)
        self.assertEqual(bad['status'],'fail')
        self.assertEqual(notifications,[])
        hook.unlink()
        good=sync.run_once(self.root,self.repo,d=fixture.D,notify=notifications.append)
        self.assertEqual(good['status'],'pass',good)
        self.assertEqual(len(notifications),1)
        self.assertTrue(sync.repo_synced(fixture.D,root=self.root,repo=self.repo))
        self.assertEqual(sync.run_once(self.root,self.repo,d=fixture.D,notify=notifications.append)['status'],'pass')
        self.assertEqual(len(notifications),1)
        self.fixture.jpath.write_bytes(self.fixture.jpath.read_bytes()+b'\n')
        self.fixture.release()
        self.assertEqual(sync.run_once(self.root,self.repo,d=fixture.D,notify=notifications.append)['status'],'pass')
        self.assertEqual(len(notifications),2)

    def test_cli_once_and_hidden_background_route_to_candidate(self):
        import os
        from unittest.mock import Mock
        args=['sync_watchdog_candidate.py','--root',str(self.root),'--repo',str(self.repo)]
        with patch.object(sys,'argv',args+['--once']),patch.object(sync,'run_once',return_value={'status':'pass'}) as once:
            self.assertEqual(sync.main(),0)
            once.assert_called_once()
        # CONTROLLED launch stub: does not start a daemon or install a task.
        with patch.object(sys,'argv',args+['--background']),patch.object(sync.subprocess,'Popen',return_value=Mock(pid=12345)) as launch:
            self.assertEqual(sync.main(),0)
        command=launch.call_args.args[0]
        self.assertIn('--loop',command)
        self.assertIn(str(self.root),command)
        if os.name=='nt':self.assertTrue(launch.call_args.kwargs['creationflags'] & sync.subprocess.CREATE_NO_WINDOW)
        else:self.assertTrue(launch.call_args.kwargs['start_new_session'])

    def test_weekday_loop_skips_weekend_and_retries_without_waiting_other_workers(self):
        self.assertTrue(hasattr(sync,'run_loop'))
        moments=iter([dt.datetime(2026,9,5,19),dt.datetime(2026,9,7,19),dt.datetime(2026,9,7,19,1)])
        sleeps=[]
        with patch.object(sync,'run_once',side_effect=[{'status':'fail','errors':['CONTROLLED transient']},{'status':'pass','errors':[]}]) as once:
            r=sync.run_loop(self.root,self.repo,interval=1,iterations=3,clock=lambda:next(moments),sleeper=sleeps.append)
        self.assertEqual(once.call_count,2)
        self.assertEqual(r[-1]['status'],'pass')
        self.assertEqual(sleeps,[1,1])

if __name__=='__main__':unittest.main(verbosity=2)
