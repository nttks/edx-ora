import json
import logging

from django.core.management.base import BaseCommand
#from http://jamesmckay.net/2009/03/django-custom-managepy-commands-not-committing-transactions/
#Fix issue where db data in manage.py commands is not refreshed at all once they start running
from django.db import transaction
transaction.commit_unless_managed()
from controller.models import Submission, SubmissionState, Grader, GraderStatus
from optparse import make_option


log = logging.getLogger(__name__)


class Command(BaseCommand):
    args = "<submission_id>"
    help = "Usage: rollback_staff_grading [--check] <submission_id>\n"

    option_list = BaseCommand.option_list + (
        make_option(
            '--check',
            action='store_true',
            help="Only check the specified submission.",
        ),
    )

    def handle(self, *args, **options):
        """
        Rollback a student submission to a state waiting to be graded.
        """

        if len(args)!=1:
            print self.help
            return

        submission_id, = args
        submission_id = int(submission_id)

        try:
            sub = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            raise Exception("Could not find submission with id: {0}".format(submission_id))
        except Exception:
            raise

        check = options['check']
        if check:
            try:
                grader = Grader.objects.filter(
                    submission_id=submission_id,
                    status_code=GraderStatus.success,
                    grader_type="IN"
                ).order_by('-date_created')[0:1].get()
            except Grader.DoesNotExist:
                grader = {}
            except Exception:
                raise

            print "submission_id           : %s" % submission_id
            print "course_id               : %s" % sub.course_id
            print "student_id              : %s" % sub.student_id
            print "state                   : %s" % sub.state
            print "student_response        : %s" % sub.student_response
            print "student_submission_time : %s" % sub.student_submission_time
            print "last_score              : %s" % (grader.score if grader else None)
            print "last_feedback           : %s" % (json.loads(grader.feedback)['feedback'] if grader else None)
            return

        sub.state = SubmissionState.waiting_to_be_graded
        sub.posted_results_back_to_queue = False
        sub.save()

        transaction.commit_unless_managed()
        print "Submission(id=%s) saved successfully." % submission_id
