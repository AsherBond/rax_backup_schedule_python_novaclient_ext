# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Backup schedule extension
"""
from novaclient import base
from novaclient import utils

DAY_CHOICES = ['DISABLED', 'SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY',
               'THURSDAY', 'FRIDAY', 'SATURDAY']

HOUR_CHOICES = ['DISABLED', 'H_0000_0200', 'H_0200_0400', 'H_0400_0600',
                'H_0600_0800', 'H_0800_1000', 'H_1000_1200', 'H_1200_1400',
                'H_1400_1600', 'H_1600_1800', 'H_1800_2000', 'H_2000_2200',
                'H_2200_0000']


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


class BackupSchedule(base.Resource):
    """
    Represents the daily or weekly backup schedule for some server.
    """
    def get(self):
        """
        Get this `BackupSchedule` again from the API.
        """
        return self.manager.get(server=self.server)

    def delete(self):
        """
        Delete (i.e. disable and remove) this scheduled backup.
        """
        self.manager.delete(server=self.server)

    def update(self, enabled=True, weekly='disabled', daily='disabled',
               rotation=0):
        """
        Update this backup schedule.

        See :meth:`BackupScheduleManager.create` for details.
        """
        self.manager.create(self.server, enabled, weekly, daily, rotation)


class BackupScheduleManager(base.Manager):
    """
    Manage server backup schedules.
    """
    resource_class = BackupSchedule

    def get(self, server):
        """
        Get the current backup schedule for a server.

        :arg server: The server (or its ID).
        :rtype: :class:`BackupSchedule`
        """
        schedule = self._get('/servers/%s/backup_schedule' % server.id,
                             'backupSchedule')
        schedule.server = server
        return schedule

    # Backup schedules use POST for both create and update, so allow both here.
    # Unlike the rest of the API, POST here returns no body, so we can't use
    # the nice little helper methods.

    def create(self, server, enabled=True, weekly='disabled',
               daily='disabled', rotation=0):
        """
        Create or update the backup schedule for the given server.

        :arg server: The server (or its ID).
        :arg enabled: boolean; should this schedule be enabled?
        :arg weekly: Run a weekly backup on this day
                     (one of the `BACKUP_WEEKLY_*` constants)
        :arg daily: Run a daily backup at this time
                    (one of the `BACKUP_DAILY_*` constants)
        """
        backup_schedule = dict(enabled=enabled,
                               weekly=weekly,
                               daily=daily,
                               rotation=rotation)
        self.api.client.post('/servers/%s/backup_schedule' % server.id,
                             body=dict(backupSchedule=backup_schedule))

    update = create

    def delete(self, server):
        """
        Remove the scheduled backup for `server`.

        :arg server: The server (or its ID).
        """
        self._delete('/servers/%s/backup_schedule' % server.id)


@utils.arg('server',
           metavar='<server>',
           help='Name or ID of server.')
@utils.arg('--enable',
           dest='enabled',
           default=None,
           action='store_true',
           help='Enable backups.')
@utils.arg('--disable',
           dest='enabled',
           action='store_false',
           help='Disable backups.')
@utils.arg('--weekly',
           metavar='<day>',
           choices=DAY_CHOICES,
           help='Schedule a weekly backup for <day> (one of: %s).' %
                pretty_choice_list(DAY_CHOICES))
@utils.arg('--daily',
           metavar='<time-window>',
           choices=HOUR_CHOICES,
           help='Schedule a daily backup during <time-window> (one of: %s).' %
                pretty_choice_list(HOUR_CHOICES))
@utils.arg('--rotation',
           dest='rotation',
           action='store',
           help='Number of extra backups to keep around.')
def do_backup_schedule(cs, args):
    """
    Show or edit the backup schedule for a server.

    With no flags, the backup schedule will be shown. If flags are given,
    the backup schedule will be modified accordingly.
    """
    server = utils.find_resource(cs.servers, args.server)
    backup_schedule = cs.rax_backup_schedule_python_novaclient_ext.get(server)
    # If we have some flags, update the backup
    backup = {}
    if args.daily:
        backup['daily'] = args.daily.upper()
    if args.weekly:
        backup['weekly'] = args.weekly.upper()
    if args.enabled is not None:
        backup['enabled'] = args.enabled
    if args.rotation is not None:
        backup['rotation'] = args.rotation
    if backup:
        backup_schedule.update(**backup)
    else:
        utils.print_dict(backup_schedule._info)


@utils.arg('server',
           metavar='<server>',
           help='Name or ID of server.')
def do_backup_schedule_delete(cs, args):
    """
    Delete the backup schedule for a server.
    """
    server = utils.find_resource(cs.servers, args.server)
    cs.rax_backup_schedule_python_novaclient_ext.get(server).delete()
