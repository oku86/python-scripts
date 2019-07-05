# Verifies if an ECS Service re-deployment is successful
# It needs the following arguments:
# cluster: name of ECS cluster
# service: name of ECS service to verify
# aws_default_region: AWS region where the applicatin runs (default: eu-west-1/Ireland)
# wait_time: Number of 20 second iterations to wait for the ECS service re-deployment (default: 10 minutes)
import argparse
import boto3
import sys
from time import sleep


def get_deployment_id(cluster_name, service_name, deployment_status):
    """Get ECS service deployment ID
    """
    # Get service details
    response_services = ecs_client.describe_services(cluster=cluster_name, services=[service_name])
    # Get a list of current deployments (this is a 'list of dictionaries')
    deployment_list = response_services["services"][0]["deployments"]
    # Get deployment ID
    for d in deployment_list:
        if d["status"] == deployment_status:
            return d["id"].split("/")[-1]


if __name__ == "__main__":
    try:
        # Import arguments to create the doc to be indexed
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--cluster", type=str, help="ECS cluster name", required=True)
        parser.add_argument("-s", "--service", type=str, help="Service that will be re-deployed", required=True)
        parser.add_argument(
            "-w",
            "--wait_time",
            type=int,
            help="Number of 20 second iterations to wait for the ECS service re-deployment (default: 10 minutes)",
            default=30,
        )
        parser.add_argument(
            "-r",
            "--aws_default_region",
            type=str,
            help="AWS region where the applicatin runs (default: 'eu-west-1')",
            default="eu-west-1",
        )
        args = parser.parse_args()
    except Exception as e:
        parser.print_help()
    try:
        # Connect to ECS cluster
        ecs_client = boto3.client("ecs", region_name=args.aws_default_region)
        # Get inital/old and new deployment IDs
        # initial_id  ->  the old (to be replaced) deployment - currently in ACTIVE status
        # new_id      ->  the new deployment which should replace the initial one - currently in PRIMARY status
        initial_id = get_deployment_id(args.cluster, args.service, "ACTIVE")
        new_id = get_deployment_id(args.cluster, args.service, "PRIMARY")

        count = 0
        while count < args.wait_time:
            print("Iteration", count + 1, "out of", args.wait_time)
            count += 1
            active_id = get_deployment_id(args.cluster, args.service, "ACTIVE")
            if active_id:
                print("New deployment in progress - active/initial deployment ID:", active_id)
                sleep(20)
            elif new_id == get_deployment_id(args.cluster, args.service, "PRIMARY"):
                print("Deployment successful")
                sys.exit(0)
            else:
                print("Re-deployment failed. Please check events log.")
                sys.exit(1)
        else:
            print("Deployment still in progress after {} minutes. Please check events log.".format(args.wait_time))
            sys.exit(2)

    except Exception as e:
        print(e)
        raise Exception
