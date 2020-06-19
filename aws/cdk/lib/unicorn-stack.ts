import * as cdk from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as elbv2 from '@aws-cdk/aws-elasticloadbalancingv2';
import * as iam from '@aws-cdk/aws-iam';
import * as autoscaling from '@aws-cdk/aws-autoscaling'
import { CfnAccessKey } from '@aws-cdk/aws-iam';

export class UnicornStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here

    // Define image ID
    const imageId = 'ami-091f5da6552bfa63e';

    const vpcCidr = '10.41.0.0/16'

    // Create VPC
    const vpc = new ec2.Vpc(this, 'unicorns', {
      natGateways: 1,
      maxAzs: 3,
      subnetConfiguration: [
        {
          subnetType: ec2.SubnetType.PRIVATE,
          name: 'Application',
          cidrMask: 24
        },
        {
          subnetType: ec2.SubnetType.PUBLIC,
          name: 'Ingress',
          cidrMask: 24,
        }
      ]
    });

    // Create load balancer security group
    const loadbalancerSg = new ec2.SecurityGroup(this, 'loadbalancer', {
      vpc: vpc,
      allowAllOutbound: true
    });

    loadbalancerSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80));
    loadbalancerSg.addIngressRule(ec2.Peer.anyIpv6(), ec2.Port.tcp(80));
    
    // Create instance security group
    const instanceSg = new ec2.SecurityGroup(this, 'instance', {
      vpc: vpc,
      allowAllOutbound: true
    });

    instanceSg.addIngressRule(loadbalancerSg, ec2.Port.tcp(8080));

    // Create autoscaling group
    const asg = new autoscaling.AutoScalingGroup(this, 'ASG', {
      vpc,
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
      machineImage: ec2.MachineImage.genericLinux({'ap-southeast-1': imageId}),
      minCapacity: 1,
      maxCapacity: 3,
      vpcSubnets: {subnetType: ec2.SubnetType.PRIVATE},
    });

    asg.addSecurityGroup(instanceSg);

    // Create target group and attach
    const albTgt = new elbv2.ApplicationTargetGroup(this, 'public', {
      vpc,
      port: 8080,
      targetType: elbv2.TargetType.INSTANCE,
      healthCheck: {
        enabled: true,
        interval: cdk.Duration.minutes(5),
        path: '/health',
        port: '8080',
        protocol: elbv2.Protocol.HTTP, 
      }
    });

    asg.attachToApplicationTargetGroup(albTgt);

    // Create load balancer
    const alb = new elbv2.ApplicationLoadBalancer(this, 'application', {
      vpc,
      internetFacing: true,
      vpcSubnets: {subnetType: ec2.SubnetType.PUBLIC},
      securityGroup: loadbalancerSg
    });

    // Create load balancer listener
    const listener = alb.addListener('public', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultTargetGroups: [albTgt]
    });
  }
}
