"""Mesos Master check

Collects metrics from mesos master node, only the leader is sending metrics.
"""
# stdlib
from hashlib import md5

# project
from checks import AgentCheck, CheckException

# 3rd party
import requests

class MesosMaster(AgentCheck):
    GAUGE = AgentCheck.gauge
    RATE = AgentCheck.rate
    SERVICE_CHECK_NAME = "mesos_master.can_connect"

    FRAMEWORK_METRICS = {
        'cpus'                                              : ('mesos.state.framework.cpu', GAUGE),
        'mem'                                               : ('mesos.state.framework.mem', GAUGE),
        'disk'                                              : ('mesos.state.framework.disk', GAUGE),
    }

    ROLE_RESOURCES_METRICS = {
        'cpus'                                              : ('mesos.role.cpu', GAUGE),
        'mem'                                               : ('mesos.role.mem', GAUGE),
        'disk'                                              : ('mesos.role.disk', GAUGE),
    }

    STATE_METRICS = {
        'deactivated_slaves'                                : ('mesos.state.deactivated_slaves', GAUGE),
        'failed_tasks'                                      : ('mesos.state.failed_tasks', GAUGE),
        'finished_tasks'                                    : ('mesos.state.finished_tasks', GAUGE),
        'killed_tasks'                                      : ('mesos.state.killed_tasks', GAUGE),
        'lost_tasks'                                        : ('mesos.state.lost_tasks', GAUGE),
        'staged_tasks'                                      : ('mesos.state.staged_tasks', GAUGE),
        'started_tasks'                                     : ('mesos.state.started_tasks', GAUGE),
    }

    STATS_METRICS = {
        'activated_slaves'                                  : ('mesos.stats.activated_slaves', GAUGE),
        'active_schedulers'                                 : ('mesos.stats.active_schedulers', GAUGE),
        'active_tasks_gauge'                                : ('mesos.stats.active_tasks_gauge', GAUGE),
        'cpus_percent'                                      : ('mesos.stats.cpus_percent', GAUGE),
        'cpus_total'                                        : ('mesos.stats.cpus_total', GAUGE),
        'cpus_used'                                         : ('mesos.stats.cpus_used', GAUGE),
        'deactivated_slaves'                                : ('mesos.stats.deactivated_slaves', GAUGE),
        'disk_percent'                                      : ('mesos.stats.disk_percent', GAUGE),
        'disk_total'                                        : ('mesos.stats.disk_total', GAUGE),
        'disk_used'                                         : ('mesos.stats.disk_used', GAUGE),
        'elected'                                           : ('mesos.stats.elected', GAUGE),
        'failed_tasks'                                      : ('mesos.stats.failed_tasks', GAUGE),
        'finished_tasks'                                    : ('mesos.stats.finished_tasks', GAUGE),
        'invalid_status_updates'                            : ('mesos.stats.invalid_status_updates', GAUGE),
        'killed_tasks'                                      : ('mesos.stats.killed_tasks', GAUGE),
        'lost_tasks'                                        : ('mesos.stats.lost_tasks', GAUGE),
        'total_schedulers'                                  : ('mesos.stats.total_schedulers', GAUGE),
        'uptime'                                            : ('mesos.stats.uptime', GAUGE),
        'valid_status_updates'                              : ('mesos.stats.valid_status_updates', GAUGE),
        'mem_percent'                                       : ('mesos.stats.mem_percent', GAUGE),
        'mem_total'                                         : ('mesos.stats.mem_total', GAUGE),
        'mem_used'                                          : ('mesos.stats.mem_used', GAUGE),
        'outstanding_offers'                                : ('mesos.stats.outstanding_offers', GAUGE),
        'staged_tasks'                                      : ('mesos.stats.staged_tasks', GAUGE),
        'started_tasks'                                     : ('mesos.stats.started_tasks', GAUGE),
        'master/cpus_percent'                               : ('mesos.stats.master.cpus_percent', GAUGE),
        'master/cpus_total'                                 : ('mesos.stats.master.cpus_total', GAUGE),
        'master/cpus_used'                                  : ('mesos.stats.master.cpus_used', GAUGE),
        'master/disk_percent'                               : ('mesos.stats.master.disk_percent', GAUGE),
        'master/disk_total'                                 : ('mesos.stats.master.disk_total', GAUGE),
        'master/disk_used'                                  : ('mesos.stats.master.disk_used', GAUGE),
        'master/dropped_messages'                           : ('mesos.stats.master.dropped_messages', GAUGE),
        'master/elected'                                    : ('mesos.stats.master.elected', GAUGE),
        'master/event_queue_dispatches'                     : ('mesos.stats.master.event_queue_dispatches', GAUGE),
        'master/event_queue_http_requests'                  : ('mesos.stats.master.event_queue_http_requests', GAUGE),
        'master/event_queue_messages'                       : ('mesos.stats.master.event_queue_messages', GAUGE),
        'master/frameworks_active'                          : ('mesos.stats.master.frameworks_active', GAUGE),
        'master/frameworks_connected'                       : ('mesos.stats.master.frameworks_connected', GAUGE),
        'master/frameworks_disconnected'                    : ('mesos.stats.master.frameworks_disconnected', GAUGE),
        'master/frameworks_inactive'                        : ('mesos.stats.master.frameworks_inactive', GAUGE),
        'master/invalid_framework_to_executor_messages'     : ('mesos.stats.master.invalid_framework_to_executor_messages', GAUGE),
        'master/invalid_status_update_acknowledgements'     : ('mesos.stats.master.invalid_status_update_acknowledgements', GAUGE),
        'master/invalid_status_updates'                     : ('mesos.stats.master.invalid_status_updates', GAUGE),
        'master/mem_percent'                                : ('mesos.stats.master.mem_percent', GAUGE),
        'master/mem_total'                                  : ('mesos.stats.master.mem_total', GAUGE),
        'master/mem_used'                                   : ('mesos.stats.master.mem_used', GAUGE),
        'master/messages_authenticate'                      : ('mesos.stats.master.messages_authenticate', GAUGE),
        'master/messages_deactivate_framework'              : ('mesos.stats.master.messages_deactivate_framework', GAUGE),
        'master/messages_decline_offers'                    : ('mesos.stats.master.messages_decline_offers', GAUGE),
        'master/messages_exited_executor'                   : ('mesos.stats.master.messages_exited_executor', GAUGE),
        'master/messages_framework_to_executor'             : ('mesos.stats.master.messages_framework_to_executor', GAUGE),
        'master/messages_kill_task'                         : ('mesos.stats.master.messages_kill_task', GAUGE),
        'master/messages_launch_tasks'                      : ('mesos.stats.master.messages_launch_tasks', GAUGE),
        'master/messages_reconcile_tasks'                   : ('mesos.stats.master.messages_reconcile_tasks', GAUGE),
        'master/messages_register_framework'                : ('mesos.stats.master.messages_register_framework', GAUGE),
        'master/messages_register_slave'                    : ('mesos.stats.master.messages_register_slave', GAUGE),
        'master/messages_reregister_framework'              : ('mesos.stats.master.messages_reregister_framework', GAUGE),
        'master/messages_reregister_slave'                  : ('mesos.stats.master.messages_reregister_slave', GAUGE),
        'master/messages_resource_request'                  : ('mesos.stats.master.messages_resource_request', GAUGE),
        'master/messages_revive_offers'                     : ('mesos.stats.master.messages_revive_offers', GAUGE),
        'master/messages_status_update'                     : ('mesos.stats.master.messages_status_update', GAUGE),
        'master/messages_status_update_acknowledgement'     : ('mesos.stats.master.messages_status_update_acknowledgement', GAUGE),
        'master/messages_unregister_framework'              : ('mesos.stats.master.messages_unregister_framework', GAUGE),
        'master/messages_unregister_slave'                  : ('mesos.stats.master.messages_unregister_slave', GAUGE),
        'master/outstanding_offers'                         : ('mesos.stats.master.outstanding_offers', GAUGE),
        'master/recovery_slave_removals'                    : ('mesos.stats.master.recovery_slave_removals', GAUGE),
        'master/slave_registrations'                        : ('mesos.stats.master.slave_registrations', GAUGE),
        'master/slave_removals'                             : ('mesos.stats.master.slave_removals', GAUGE),
        'master/slave_reregistrations'                      : ('mesos.stats.master.slave_reregistrations', GAUGE),
        'master/slave_shutdowns_canceled'                   : ('mesos.stats.master.slave_shutdowns_canceled', GAUGE),
        'master/slave_shutdowns_scheduled'                  : ('mesos.stats.master.slave_shutdowns_scheduled', GAUGE),
        'master/slaves_active'                              : ('mesos.stats.master.slaves_active', GAUGE),
        'master/slaves_connected'                           : ('mesos.stats.master.slaves_connected', GAUGE),
        'master/slaves_disconnected'                        : ('mesos.stats.master.slaves_disconnected', GAUGE),
        'master/slaves_inactive'                            : ('mesos.stats.master.slaves_inactive', GAUGE),
        'master/tasks_error'                                : ('mesos.stats.master.tasks_error', GAUGE),
        'master/tasks_failed'                               : ('mesos.stats.master.tasks_failed', GAUGE),
        'master/tasks_finished'                             : ('mesos.stats.master.tasks_finished', GAUGE),
        'master/tasks_killed'                               : ('mesos.stats.master.tasks_killed', GAUGE),
        'master/tasks_lost'                                 : ('mesos.stats.master.tasks_lost', GAUGE),
        'master/tasks_running'                              : ('mesos.stats.master.tasks_running', GAUGE),
        'master/tasks_staging'                              : ('mesos.stats.master.tasks_staging', GAUGE),
        'master/tasks_starting'                             : ('mesos.stats.master.tasks_starting', GAUGE),
        'master/uptime_secs'                                : ('mesos.stats.master.uptime_secs', GAUGE),
        'master/valid_framework_to_executor_messages'       : ('mesos.stats.master.valid_framework_to_executor_messages', GAUGE),
        'master/valid_status_update_acknowledgements'       : ('mesos.stats.master.valid_status_update_acknowledgements', GAUGE),
        'master/valid_status_updates'                       : ('mesos.stats.master.valid_status_updates', GAUGE),
        'registrar/queued_operations'                       : ('mesos.stats.registrar.queued_operations', GAUGE),
        'registrar/registry_size_bytes'                     : ('mesos.stats.registrar.registry_size_bytes', GAUGE),
        'registrar/state_fetch_ms'                          : ('mesos.stats.registrar.state_fetch_ms', GAUGE),
        'registrar/state_store_ms'                          : ('mesos.stats.registrar.state_store_ms', GAUGE),
        'registrar/state_store_ms/count'                    : ('mesos.stats.registrar.state_store_ms.count', GAUGE),
        'registrar/state_store_ms/max'                      : ('mesos.stats.registrar.state_store_ms.max', GAUGE),
        'registrar/state_store_ms/min'                      : ('mesos.stats.registrar.state_store_ms.min', GAUGE),
        'registrar/state_store_ms/p50'                      : ('mesos.stats.registrar.state_store_ms.p50', GAUGE),
        'registrar/state_store_ms/p90'                      : ('mesos.stats.registrar.state_store_ms.p90', GAUGE),
        'registrar/state_store_ms/p95'                      : ('mesos.stats.registrar.state_store_ms.p95', GAUGE),
        'registrar/state_store_ms/p99'                      : ('mesos.stats.registrar.state_store_ms.p99', GAUGE),
        'registrar/state_store_ms/p999'                     : ('mesos.stats.registrar.state_store_ms.p999', GAUGE),
        'registrar/state_store_ms/p9999'                    : ('mesos.stats.registrar.state_store_ms.p9999', GAUGE),
        'system/cpus_total'                                 : ('mesos.stats.system.cpus_total', GAUGE),
        'system/load_15min'                                 : ('mesos.stats.system.load_15min', RATE),
        'system/load_1min'                                  : ('mesos.stats.system.load_1min', RATE),
        'system/load_5min'                                  : ('mesos.stats.system.load_5min', RATE),
        'system/mem_free_bytes'                             : ('mesos.stats.system.mem_free_bytes', GAUGE),
        'system/mem_total_bytes'                            : ('mesos.stats.system.mem_total_bytes', GAUGE),
    }

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

    def _get_master_state(self, url, timeout):
        return self._get_json(url + '/state.json', timeout)

    def _get_master_stats(self, url, timeout):
        return self._get_json(url + '/stats.json', timeout)

    def _get_master_roles(self, url, timeout):
        return self._get_json(url + '/roles.json', timeout)

    def _check_leadership(self, url, timeout):
        json = self._get_master_state(url, timeout)

        if json is not None and json['leader'] == json['pid']:
            return json
        return None

    def check(self, instance):
        if 'url' not in instance:
            raise Exception('Mesos instance missing "url" value.')

        url = instance['url']
        instance_tags = instance.get('tags', [])
        default_timeout = self.init_config.get('default_timeout', 5)
        timeout = float(instance.get('timeout', default_timeout))

        json = self._check_leadership(url, timeout)
        if json:
            tags = ['cluster:' + json['cluster'], 'mesos_pid:' + json['pid'], 'mesos_id:' + json['id']] + instance_tags

            [v[1](self, v[0], json[k], tags=tags) for k, v in self.STATE_METRICS.iteritems()]

            for framework in json['frameworks']:
                tags = ['framework:' + framework['id'], 'framework_name:' + framework['name']] + instance_tags
                resources = framework['resources']
                [v[1](self, v[0], resources[k], tags=tags) for k, v in self.FRAMEWORK_METRICS.iteritems()]

            json = self._get_master_stats(url, timeout)
            if json is not None:
                tags = instance_tags
                [v[1](self, v[0], json[k], tags=tags) for k, v in self.STATS_METRICS.iteritems()]

            json = self._get_master_roles(url, timeout)
            if json is not None:
                for role in json['roles']:
                    tags += ['mesos_role:' + role['name']]
                    self.GAUGE('mesos.role.frameworks', len(role['frameworks']), tags=tags)
                    self.GAUGE('mesos.role.weight', role['weight'], tags=tags)
                    [v[1](self, v[0], role['resources'][, tags=tags) for k, v in self.ROLE_RESOURCES_METRICS.iteritems()]
