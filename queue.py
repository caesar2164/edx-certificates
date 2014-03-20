import requests
import json
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, Timeout
import logging

log = logging.getLogger(__name__)


class XQueuePullManager(object):
    """
    XQueuePullManager provides an interface to
    the xqueue server for the pull interface

    Methods for getting the queue length,
    retrieving a single item from the queue
    and posting a response.
    """

    def __init__(self, queue_url, queue_name, queue_auth_user,
            queue_auth_pass, queue_user, queue_pass):
        self.url = queue_url
        self.queue_name = queue_name
        self.auth_user = queue_auth_user
        self.auth_pass = queue_auth_pass
        self.queue_user = queue_user
        self.queue_pass = queue_pass
        self._login()

    def _login(self):
        """
        Login to the xqueue server
        """

        try:
            self.session = requests.session(auth=HTTPBasicAuth(
                self.auth_user, self.auth_pass))
            request = self.session.post('{0}/xqueue/login/'.format(self.url),
                    data={
                        'username': self.queue_user,
                        'password': self.queue_pass
                        })
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply resp:{0}".format(
                    str(response)))
        except (Exception, ConnectionError, Timeout) as e:
            log.critical("Unable to connect to queue: {0}".format(e))
            raise

    def get_length(self):
        """
        Returns the length of the queue
        """

        try:
            request = self.session.get('{0}/xqueue/get_queuelen/'.format(
                self.url), params={'queue_name': self.queue_name})
            response = json.loads(request.text)
            if response['return_code'] != 0:
                raise Exception("Invalid return code in reply")
            length = int(response['content'])
        except (ValueError, Exception, ConnectionError, Timeout) as e:
            log.critical("Unable to get queue length: {0}".format(e))
            raise

        return length

    def get_submission(self):
        """
        Gets a single submission from the xqueue
        server and returns the payload as a dictionary
        """

        try:
            request = self.session.get('{0}/xqueue/get_submission/'.format(
                self.url), params={'queue_name': self.queue_name})
        except (ConnectionError, Timeout) as e:
            log.critical("Unable to get submission "
                             "from queue: {0}".format(e))
            raise

        try:
            response = json.loads(request.text)
            log.debug('response from get_submission: {0}'.format(response))
            if response['return_code'] != 0:
                log.critical("response: {0}".format(request.text))
                raise Exception("Invalid return code in reply")

            return json.loads(response['content'])

        except (Exception, ValueError, KeyError) as e:
            log.critical("Unable to parse queue message: {0} "
                                "response: {1}".format(e, request.text))
            raise

    def respond(self, xqueue_reply):
        """
        Posts xqueue_reply to the qserver which
        will be posted back to the LMS
        """

        try:
            request = self.session.post('{0}/xqueue/put_result/'.format(
                self.url), data=xqueue_reply)
            log.info('Response: {0}'.format(request.text))

        except (ConnectionError, Timeout) as e:
            log.critical("Connection error posting response "
                             "to the LMS: {0}".format(e))
            raise
        response = json.loads(request.text)
        if response['return_code'] != 0:
            log.critical("response: {0}".format(request.text))
            raise Exception("Invalid return code in reply")

    def __str__(self):
        return self.url