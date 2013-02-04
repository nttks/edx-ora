"""
Tests for open ended grading interfaces

django-admin.py test --settings=lms.envs.test --pythonpath=. lms/djangoapps/open_ended_grading
"""

from django.test import TestCase
from open_ended_grading import staff_grading_service
from open_ended_grading import peer_grading_service
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group

from courseware.access import _course_staff_group_name
import courseware.tests.tests as ct
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django
from nose import SkipTest
from mock import patch, Mock
import json

import logging
log = logging.getLogger(__name__)
from override_settings import override_settings


@override_settings(MODULESTORE=ct.TEST_DATA_XML_MODULESTORE)
class TestStaffGradingService(ct.PageLoader):
    '''
    Check that staff grading service proxy works.  Basically just checking the
    access control and error handling logic -- all the actual work is on the
    backend.
    '''
    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.location = 'TestLocation'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)
        
        self.course_id = "edX/toy/2012_Fall"
        self.toy = modulestore().get_course(self.course_id)
        def make_instructor(course):
            group_name = _course_staff_group_name(course.location)
            g = Group.objects.create(name=group_name)
            g.user_set.add(ct.user(self.instructor))

        make_instructor(self.toy)

        self.mock_service = staff_grading_service.staff_grading_service()

        self.logout()

    def test_access(self):
        """
        Make sure only staff have access.
        """
        self.login(self.student, self.password)

        # both get and post should return 404
        for view_name in ('staff_grading_get_next', 'staff_grading_save_grade'):
            url = reverse(view_name, kwargs={'course_id': self.course_id})
            self.check_for_get_code(404, url)
            self.check_for_post_code(404, url)


    def test_get_next(self):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_get_next', kwargs={'course_id': self.course_id})
        data = {'location': self.location}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])
        self.assertEquals(d['submission_id'], self.mock_service.cnt)
        self.assertIsNotNone(d['submission'])
        self.assertIsNotNone(d['num_graded'])
        self.assertIsNotNone(d['min_for_ml'])
        self.assertIsNotNone(d['num_pending'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['ml_error_info'])
        self.assertIsNotNone(d['max_score'])
        self.assertIsNotNone(d['rubric'])


    def test_save_grade(self):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_save_grade', kwargs={'course_id': self.course_id})

        data = {'score': '12',
                'feedback': 'great!',
                'submission_id': '123',
                'location': self.location,
                'rubric_scores[]': ['1', '2']}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'], str(d))
        self.assertEquals(d['submission_id'], self.mock_service.cnt)

    def test_get_problem_list(self):
        self.login(self.instructor, self.password)

        url = reverse('staff_grading_get_problem_list', kwargs={'course_id': self.course_id})
        data = {}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'], str(d))
        self.assertIsNotNone(d['problem_list'])

    
@override_settings(MODULESTORE=ct.TEST_DATA_XML_MODULESTORE)
class TestPeerGradingService(ct.PageLoader):
    '''
    Check that staff grading service proxy works.  Basically just checking the
    access control and error handling logic -- all the actual work is on the
    backend.
    '''
    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.location = 'TestLocation'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)
        
        self.course_id = "edX/toy/2012_Fall"
        self.toy = modulestore().get_course(self.course_id)

        self.mock_service = peer_grading_service.peer_grading_service()

        self.logout()

    def test_get_next_submission_success(self):
        self.login(self.student, self.password)

        url = reverse('peer_grading_get_next_submission', kwargs={'course_id': self.course_id})
        data = {'location': self.location}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])
        self.assertIsNotNone(d['submission_id'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['submission_key'])
        self.assertIsNotNone(d['max_score'])

    def test_get_next_submission_missing_location(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_get_next_submission', kwargs={'course_id': self.course_id})
        data = {}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertFalse(d['success'])
        self.assertEqual(d['error'], "Missing required keys: location")

    def test_save_grade_success(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_save_grade', kwargs={'course_id': self.course_id})
        data = {'location': self.location, 
                'submission_id': '1', 
                'submission_key': 'fake key', 
                'score': '2',
                'feedback': 'This is feedback',
                'rubric_scores[]': [1, 2],
                'submission_flagged' : False}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])

    def test_save_grade_missing_keys(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_save_grade', kwargs={'course_id': self.course_id})
        data = {}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertFalse(d['success'])
        self.assertTrue(d['error'].find('Missing required keys:') > -1)

    def test_is_calibrated_success(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_is_student_calibrated', kwargs={'course_id': self.course_id})
        data = {'location': self.location}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])
        self.assertTrue('calibrated' in d)

    def test_is_calibrated_failure(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_is_student_calibrated', kwargs={'course_id': self.course_id})
        data = {}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertFalse(d['success'])
        self.assertFalse('calibrated' in d)

    def test_show_calibration_essay_success(self):
        self.login(self.student, self.password)

        url = reverse('peer_grading_show_calibration_essay', kwargs={'course_id': self.course_id})
        data = {'location': self.location}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])
        self.assertIsNotNone(d['submission_id'])
        self.assertIsNotNone(d['prompt'])
        self.assertIsNotNone(d['submission_key'])
        self.assertIsNotNone(d['max_score'])

    def test_show_calibration_essay_missing_key(self):
        self.login(self.student, self.password)

        url = reverse('peer_grading_show_calibration_essay', kwargs={'course_id': self.course_id})
        data = {}

        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)

        self.assertFalse(d['success'])
        self.assertEqual(d['error'], "Missing required keys: location")

    def test_save_calibration_essay_success(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_save_calibration_essay', kwargs={'course_id': self.course_id})
        data = {'location': self.location, 
                'submission_id': '1', 
                'submission_key': 'fake key', 
                'score': '2',
                'feedback': 'This is feedback',
                'rubric_scores[]': [1, 2]}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertTrue(d['success'])
        self.assertTrue('actual_score' in d)

    def test_save_calibration_essay_missing_keys(self):
        self.login(self.student, self.password)
        url = reverse('peer_grading_save_calibration_essay', kwargs={'course_id': self.course_id})
        data = {}
        r = self.check_for_post_code(200, url, data)
        d = json.loads(r.content)
        self.assertFalse(d['success'])
        self.assertTrue(d['error'].find('Missing required keys:') > -1)
        self.assertFalse('actual_score' in d)
