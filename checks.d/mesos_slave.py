"""Mesos Slave check

Collects metrics from mesos slave node.
"""
# stdlib
from hashlib import md5

# project
from checks import AgentCheck, CheckException

# 3rd party
import requests

class MesosSlave(AgentCheck):
    GAUGE = AgentCheck.gauge
    RATE = AgentCheck.rate
    SERVICE_CHECK_NAME = "mesos_slave.can_connect"

    TASK_STATUS = {
        'TASK_STARTING'     : 0,
        'TASK_RUNNING'      : 1,
        'TASK_FINISHED'     : 2,
        'TASK_FAILED'       : 3,
        'TASK_KILLED'       : 4,
        'TASK_LOST'         : 5,
        'TASK_STAGING'      : 6,
        'TASK_ERROR'        : 7,
    }

    TASK_METRICS = {
        'cpus'                              : ('mesos.state.task.cpu', GAUGE),
        'mem'                               : ('mesos.state.task.mem', GAUGE),
        'disk'                              : ('mesos.state.task.disk', GAUGE),
    }

    STATE_METRICS = {
        'failed_tasks'                      : ('mesos.state.failed_tasks', GAUGE),
        'finished_tasks'                    : ('mesos.state.finished_tasks', GAUGE),
        'killed_tasks'                      : ('mesos.state.killed_tasks', GAUGE),
        'lost_tasks'                        : ('mesos.state.lost_tasks', GAUGE),
        'staged_tasks'                      : ('mesos.state.staged_tasks', GAUGE),
        'started_tasks'                     : ('mesos.state.started_tasks', GAUGE),
    }

    STATS_METRICS = {
        'failed_tasks'                      : ('mesos.stats.failed_tasks', GAUGE),
        'finished_tasks'                    : ('mesos.stats.finished_tasks', GAUGE),
        'invalid_status_updates'            : ('mesos.stats.invalid_status_updates', GAUGE),
        'killed_tasks'                      : ('mesos.stats.killed_tasks', GAUGE),
        'launched_tasks_gauge'              : ('mesos.stats.launched_tasks_gauge', GAUGE),
        'lost_tasks'                        : ('mesos.stats.lost_tasks', GAUGE),
        'queued_tasks_gauge'                : ('mesos.stats.queued_tasks_gauge', GAUGE),
        'recovery_errors'                   : ('mesos.stats.recovery_errors', GAUGE),
        'registered'                        : ('mesos.stats.registered', GAUGE),
        'staged_tasks'                      : ('mesos.stats.staged_tasks', GAUGE),
        'started_tasks'                     : ('mesos.stats.started_tasks', GAUGE),
        'total_frameworks'                  : ('mesos.stats.total_frameworks', GAUGE),
        'uptime'                            : ('mesos.stats.uptime', GAUGE),
        'valid_status_updates'              : ('mesos.stats.valid_status_updates', GAUGE),
        'slave/cpus_percent'                : ('mesos.stats.slave.cpus_percent', GAUGE),
        'slave/cpus_total'                  : ('mesos.stats.slave.cpus_total', GAUGE),
        'slave/cpus_used'                   : ('mesos.stats.slave.cpus_used', GAUGE),
        'slave/disk_percent'                : ('mesos.stats.slave.disk_percent', GAUGE),
        'slave/disk_total'                  : ('mesos.stats.slave.disk_total', GAUGE),
        'slave/disk_used'                   : ('mesos.stats.slave.disk_used', GAUGE),
        'slave/executors_registering'       : ('mesos.stats.slave.executors_registering', GAUGE),
        'slave/executors_running'           : ('mesos.stats.slave.executors_running', GAUGE),
        'slave/executors_terminated'        : ('mesos.stats.slave.executors_terminated', GAUGE),
        'slave/executors_terminating'       : ('mesos.stats.slave.executors_terminating', GAUGE),
        'slave/frameworks_active'           : ('mesos.stats.slave.frameworks_active', GAUGE),
        'slave/invalid_framework_messages'  : ('mesos.stats.slave.invalid_framework_messages', GAUGE),
        'slave/invalid_status_updates'      : ('mesos.stats.slave.invalid_status_updates', GAUGE),
        'slave/mem_percent'                 : ('mesos.stats.slave.mem_percent', GAUGE),
        'slave/mem_total'                   : ('mesos.stats.slave.mem_total', GAUGE),
        'slave/mem_used'                    : ('mesos.stats.slave.mem_used', GAUGE),
        'slave/recovery_errors'             : ('mesos.stats.slave.recovery_errors', GAUGE),
        'slave/registered'                  : ('mesos.stats.slave.registered', GAUGE),
        'slave/tasks_failed'                : ('mesos.stats.slave.tasks_failed', GAUGE),
        'slave/tasks_finished'              : ('mesos.stats.slave.tasks_finished', GAUGE),
        'slave/tasks_killed'                : ('mesos.stats.slave.tasks_killed', GAUGE),
        'slave/tasks_lost'                  : ('mesos.stats.slave.tasks_lost', GAUGE),
        'slave/tasks_running'               : ('mesos.stats.slave.tasks_running', GAUGE),
        'slave/tasks_staging'               : ('mesos.stats.slave.tasks_staging', GAUGE),
        'slave/tasks_starting'              : ('mesos.stats.slave.tasks_starting', GAUGE),
        'slave/uptime_secs'                 : ('mesos.stats.slave.uptime_secs', GAUGE),
        'slave/valid_framework_messages'    : ('mesos.stats.slave.valid_framework_messages', GAUGE),
        'slave/valid_status_updates'        : ('mesos.stats.slave.valid_status_updates', GAUGE),
        'system/cpus_total'                 : ('mesos.stats.system.cpus_total', GAUGE),
        'system/load_15min'                 : ('mesos.stats.system.load_15min', RATE),
        'system/load_1min'                  : ('mesos.stats.system.load_1min', RATE),
        'system/load_5min'                  : ('mesos.stats.system.load_5min', RATE),
        'system/mem_free_bytes'             : ('mesos.stats.system.mem_free_bytes', GAUGE),
        'system/mem_total_bytes'            : ('mesos.stats.system.mem_total_bytes', GAUGE),
    }

    cluster_name = None

    def _timeout_event(self, url, timeout, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'http_check',
            'msg_title': 'URL timeout',
            'msg_text': '%s timed out after %s seconds.' % (url, timeout),
            'aggregation_key': aggregation_key
        })

    def _status_code_event(self, url, r, aggregation_key):
        self.event({
            'timestamp': int(time.time()),
            'event_type': 'http_check',
            'msg_title': 'Invalid reponse code for %s' % url,
            'msg_text': '%s returned a status of %s' % (url, r.status_code),
            'aggregation_key': aggregation_key
        })

    def _get_json(self, url, timeout):
        # Use a hash of the URL as an aggregation key
        aggregation_key = md5(url).hexdigest()
        tags = ["url:%s" % url]
        msg = None
        status = None
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                self._status_code_event(url, r, aggregation_key)
                status = AgentCheck.CRITICAL
                msg = "Got %s when hitting %s" % (r.status_code, url)
            else:
                status = AgentCheck.OK
                msg = "Mesos master instance detected at %s " % url
        except requests.exceptions.Timeout as e:
            # If there's a timeout
            self._timeout_event(url, timeout, aggregation_key)
            msg = "%s seconds timeout when hitting %s" % (timeout, url)
            status = AgentCheck.CRITICAL
        except Exception as e:
            msg = e.message
            status = AgentCheck.CRITICAL
        finally:
            self.service_check(self.SERVICE_CHECK_NAME, status, tags=tags, message=msg)
            if status is AgentCheck.CRITICAL:
                self.warning(msg)
                return None

        return r.json()

    def _get_state(self, url, timeout):
        return self._get_json(url + '/state.json', timeout)

    def _get_stats(self, url, timeout):
        return self._get_json(url + '/stats.json', timeout)

    def _get_constant_attributes(self, url, timeout):
        json = None
        if self.cluster_name is None:
            json = self._get_state(url, timeout)
            if json is not None:
                master_state = self._get_state('http://' + json['master_hostname'] + ':5050', timeout)
                if master_state is not None:
                    self.cluster_name = master_state['cluster']

        return json

    def check(self, instance):
        if 'url' not in instance:
            raise Exception('Mesos instance missing "url" value.')

        url = instance['url']
        instance_tags = instance.get('tags', [])
        tasks = instance.get('tasks', [])
        default_timeout = self.init_config.get('default_timeout', 5)
        timeout = float(instance.get('timeout', default_timeout))

        json = self._get_constant_attributes(url, timeout)
        tags = None

        if json is None:
            json = self._get_state(url, timeout)
        if json:
            tags = ['cluster:' + self.cluster_name, 'mesos_id:' + json['id'], 'mesos_pid:' + json['pid']] + instance_tags

            [v[1](self, v[0], json[k], tags=tags) for k, v in self.STATE_METRICS.iteritems()]

            for task in tasks:
                for framework in json['frameworks']:
                    for executor in framework['executors']:
                        for t in executor['tasks']:
                            if task.lower() in t['name'].lower() and t['slave_id'] == json['id']:
                                task_tags = ['framework_id:' + t['framework_id'], 'executor_id:' + t['executor_id'], 'task_name:' + t['name']] + tags
                                self.GAUGE('mesos.state.task.status', self.TASK_STATUS[t['state']], tags=task_tags)
                                [v[1](self, v[0], t['resources'][k], tags=task_tags) for k, v in self.TASK_METRICS.iteritems()]

        json = self._get_stats(url, timeout)
        if json:
            tags = tags if tags else instance_tags
            [v[1](self, v[0], json[k], tags=tags) for k, v in self.STATS_METRICS.iteritems()]
