#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from '@aws-cdk/core';
import { UnicornStack } from '../lib/unicorn-stack';

const app = new cdk.App();
new UnicornStack(app, 'UnicornStack', {
    env: {
        region: 'ap-southeast-1',
        account: '468871832330',
    }
});
