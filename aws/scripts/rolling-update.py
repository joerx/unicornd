#!/usr/bin/env python3

import boto3
import json
import random
from pprint import pprint
import time

# NEW_AMI_ID='ami-00f03ea8f7b59f99e'
NEW_AMI_ID = 'ami-091f5da6552bfa63e'
ASG_NAME = 'UnicornStack-ASG46ED3070-5WB6SC5XPSRC'

def do_rolling_update(asg_name, new_ami_id):

    random.seed(int(time.time()))

    # Describe asg
    as_client = boto3.client('autoscaling')

    resp = as_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )

    my_asg = resp['AutoScalingGroups'][0]

    cur_desired_size = my_asg['DesiredCapacity']
    cur_max_size = my_asg['MaxSize']
    termination_policies = my_asg['TerminationPolicies']
    launch_config = my_asg['LaunchConfigurationName']

    print('Termination policies', termination_policies) 
    print('Creating new launch config with image id {}'.format(new_ami_id))

    new_lc_name = clone_launch_config(name=launch_config, ImageId=new_ami_id)

    # update launch config, set termination policy to 'OldestInstance',
    # update max and desired size to launch a batch of new instances
    # TODO: allow gradual rollout, but how to know when we're done?
    # Hint: use LaunchConfigurationName to check if an instance is old or new
    new_desired_size = cur_desired_size * 2
    new_max_size = new_desired_size if cur_max_size < new_desired_size else cur_max_size

    print('Scaling in new instances')
    print('New desired size: {}'.format(new_desired_size))

    update_asg(name=asg_name, 
        LaunchConfigurationName=new_lc_name, 
        DesiredCapacity=new_desired_size,
        MaxSize=new_max_size
    )

    wait_for_scale(asg_name, new_desired_size)

    # scale down: wait until we reach desired capacity
    # kill oldest instances first, assuming they're the ones with the old image id

    print('Scale up complete, scaling out old instances')
    print('New desired size: {}'.format(cur_desired_size))

    update_asg(name=asg_name,
        TerminationPolicies=['OldestInstance'],
        DesiredCapacity=cur_desired_size,
        MaxSize=cur_max_size
    )

    wait_for_scale(asg_name, cur_desired_size)

    print('Cycle complete, restoring termination policies ({})'.format(', '.join(termination_policies)))

    update_asg(name=asg_name, TerminationPolicies=termination_policies)


def wait_for_scale(asg_name, desired_size):
    # wait for all new instances to reach 'InService' lifecycle state
    while True:
        instances = list_instances(asg_name)
        num_not_in_service = sum(i['lifecycle'] != 'InService' for i in instances)

        for i in instances:
            print('{}\t{}\t{}\t{}\t{}'.format(i['id'], i['az'], i['image_id'], i['lifecycle'], i['status']))

        print('{} instances, {} desired, {} not in service'.format(len(instances), desired_size, num_not_in_service))
        
        if len(instances) == desired_size and num_not_in_service == 0:
            print('Scale event complete')
            return
        else:
            time.sleep(5)

        print('---')


def list_instances(asg_name):
    client_asg = boto3.client('autoscaling')
    client_ec2 = boto3.client('ec2')

    instances = list()

    resp = client_asg.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name]
    )

    asg_info = resp['AutoScalingGroups'][0]

    instance_ids = [i['InstanceId'] for i in asg_info['Instances']]

    resp = client_ec2.describe_instances(
        InstanceIds=instance_ids
    )

    # InstanceId => ImageId
    image_map = {}
    for r in resp['Reservations']:
        for i in r['Instances']:
            image_map[i['InstanceId']] = i['ImageId']

    for i in asg_info['Instances']:
        instances.append({
            'image_id': image_map[i['InstanceId']],
            'id': i['InstanceId'],
            'az': i['AvailabilityZone'],
            'status': i['HealthStatus'],
            'lifecycle': i['LifecycleState']
        })

    return instances



def update_asg(name, **kwargs):
    client = boto3.client('autoscaling')
    args = kwargs.copy()
    args['AutoScalingGroupName'] = name
    client.update_auto_scaling_group(**args)


def clone_launch_config(name, **kwargs):
    client = boto3.client('autoscaling')

    # Describe launch configuration
    resp = client.describe_launch_configurations(
        LaunchConfigurationNames=[name]
    )
    lc = resp['LaunchConfigurations'][0]

    # print('[Launch Config]')
    # pprint(lc)
    lc_name = format('{}-{}'.format(lc['LaunchConfigurationName'], random.randint(1000, 9999)))

    args = dict(
        LaunchConfigurationName=lc_name,
        ImageId=lc['ImageId'],
        SecurityGroups=lc['SecurityGroups'],
        InstanceType=lc['InstanceType'],
        BlockDeviceMappings=lc['BlockDeviceMappings'],
        InstanceMonitoring=lc['InstanceMonitoring'],
        IamInstanceProfile=lc['IamInstanceProfile'],
        EbsOptimized=lc['EbsOptimized']
    )
    args.update(kwargs)

    # Create new launch config as a copy of the old one but update image
    resp = client.create_launch_configuration(**args)

    return lc_name


if __name__ == '__main__':
    do_rolling_update(ASG_NAME, NEW_AMI_ID)
