#!/usr/bin/env python
#
# Copyright (C) 2017 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Creates and configures a GCE Windows VM for testing."""
import argparse
import logging
import os
import subprocess
import textwrap
import time
import winrm
import yaml


THIS_DIR = os.path.dirname(os.path.realpath(__file__))
GCE_IMAGE = 'windows-server-2016-dc-v20171010'
GCE_IMAGE_PROJECT = 'windows-cloud'


def logger():
    """Returns the module level logger."""
    return logging.getLogger(__name__)


def check_output(cmd, *args, **kwargs):
    """subprocess.check_output with logging."""
    logger().debug('check_output: %s', ' '.join(cmd))
    return subprocess.check_output(cmd, *args, **kwargs)


def gcloud_compute(project, cmd):
    """Runs a gcloud compute command for the given project."""
    return check_output(['gcloud', 'compute', '--project', project] + cmd)


def create_vm(args):
    """Creates a VM in GCE."""
    logger().info('Creating VM %s.', args.name)
    sysprep_file = os.path.join(THIS_DIR, '../infra/windows_sysprep.ps1')
    gcloud_compute(args.project, [
        'instances', 'create', args.name,
        '--zone', args.zone,
        '--machine-type', args.machine_type,
        '--image-project', GCE_IMAGE_PROJECT,
        '--image', GCE_IMAGE,
        '--boot-disk-type', 'pd-ssd',
        '--boot-disk-size', str(args.disk_size),
        '--tags', 'windows',
        '--metadata-from-file', 'sysprep-specialize-script-ps1={}'.format(
            sysprep_file),
    ])


def create_firewall_rule(project, name, allow, source_ranges, target_tags):
    """Creates a firewall rule for the given project."""
    logger().info('Creating %s firewall rule.', name)
    gcloud_compute(project, [
        'firewall-rules', 'create', name,
        '--allow', allow,
        '--source-ranges', source_ranges,
        '--target-tags', target_tags,
    ])


def get_serial_port_contents(project, zone, name):
    """Gets the serial port contents for the given machine."""
    return gcloud_compute(
        project, ['instances', 'get-serial-port-output', name, '--zone', zone])


def wait_for_activation_complete(project, zone, name):
    """Waits for the machine to be ready to use.

    "Activation successful" will be printed after sysprep has completed and the
    machine has rebooted.
    """
    while True:
        out = get_serial_port_contents(project, zone, name)
        if 'Activation successful.' in out:
            logger().info('Machine is up.')
            return
        else:
            retry_time = 10
            logger().info(
                'Machine still not up. Sleeping for %s seconds.', retry_time)
            time.sleep(retry_time)


def get_instance_info(project, zone, name):
    """Returns the parsed result of gcloud compute instances describe."""
    data = gcloud_compute(
        project, ['instances', 'describe', name, '--zone', zone])
    return yaml.load(data)


def reset_windows_password(project, zone, name):
    """Resets the password and returns a tupe of (username, password)."""
    cmd = [
        'gcloud', 'compute', '--project', project,
        'reset-windows-password', '--zone', zone, name
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    proc.stdin.write('Y')
    out, _ = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError('reset-windows-password failed')

    username = None
    password = None
    for line in out.splitlines():
        key, value = line.split(':')
        key = key.strip()
        value = value.strip()

        if key == 'username':
            username = value
        elif key == 'password':
            password = value

    if username is None:
        raise RuntimeError(
            'Could not find username in output:\n{}'.format(out))
    if password is None:
        raise RuntimeError(
            'Could not find password in output:\n{}'.format(out))

    return username, password


def test_winrm_connection(host, user, password):
    """Checks that we can execute a basic WinRM command."""
    logger().info('Testing WinRM connection.')
    url = 'https://{}:5986'.format(host)
    session = winrm.Session(
        url, auth=(user, password), server_cert_validation='ignore')
    session.run_ps('echo "Hello, world!"')


def parse_args():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--zone', default='us-west1-b', help='Zone the VM will be created in.')

    parser.add_argument(
        '--machine-type', default='n1-standard-8',
        help='GCE machine type. Defaults to 8 cores with 30GB RAM.')

    parser.add_argument(
        '--disk-size', type=int, default=256, help='VM disk size.')

    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase log level. Defaults to logging.WARNING.')

    parser.add_argument(
        'project', metavar='PROJECT', help='GCE project to use.')

    parser.add_argument(
        'name', metavar='NAME', help='Name to use for the instance.')

    return parser.parse_args()


def main():
    """Program entry point."""
    args = parse_args()

    log_levels = [logging.INFO, logging.DEBUG]
    verbosity = min(args.verbose, len(log_levels) - 1)
    log_level = log_levels[verbosity]
    logging.basicConfig(level=log_level)

    create_vm(args)
    out = gcloud_compute(args.project, ['firewall-rules', 'list'])
    if 'winrm' not in out:
        create_firewall_rule(
            args.project, 'winrm', 'tcp:5986', '0.0.0.0/0', 'windows')
    wait_for_activation_complete(args.project, args.zone, args.name)

    info = get_instance_info(args.project, args.zone, args.name)
    host = info['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    user, password = reset_windows_password(args.project, args.zone, args.name)
    test_winrm_connection(host, user, password)

    secrets_py = os.path.join(THIS_DIR, '..', 'secrets.py')
    logger().info('Writing connection information to %s', secrets_py)
    with open(secrets_py, 'w') as secrets_file:
        secrets_file.write(textwrap.dedent("""\
            GCE_HOST='{}'
            GCE_USER='{}'
            GCE_PASS='{}'
        """.format(host, user, password)))
    os.chmod(secrets_py, 0600)
    logger().info('Setup completed successfully.')
    logger().info('Host: %s', host)
    logger().info('Username: %s', user)
    logger().info('Password: %s', password)


if __name__ == '__main__':
    main()
