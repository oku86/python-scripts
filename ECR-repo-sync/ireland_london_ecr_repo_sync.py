# Copy Docker images from 'Ireland' (eu-west-1) region ECR repository into 'London' (eu-west-2) region
# Automatically detect all the ECR repositories defined in 'London' region (Note: ECR repo names should be the same in both regions)

import boto3
import base64
import docker
import sys

# Environment variables
IRELAND_REGION='eu-west-1'      # Source AWS region
LONDON_REGION='eu-west-2'       # Destination AWS region
TAGS=['production', 'master']   # Docker tags

docker_client = docker.from_env()
docker_api = docker.APIClient()

def ecr_login(region):
    """Docker Login to AWS ECR repository.
    """
    ecr_client = boto3.client('ecr', region_name=region)
    # Get ECR authorization token
    token = ecr_client.get_authorization_token()
    # Extract ECR username, password and registry
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
    registry = token['authorizationData'][0]['proxyEndpoint']
    # Login to ECR
    try:
        docker_client.login(username, password, registry=registry)
        print(f"Docker login to AWS '{region}' ECR repository has been successful.")
        return registry.strip('https://'), {'username': username, 'password': password}
    except Exception as e:
        print(f"Docker login to AWS '{region}' ECR repository has failed.")
        print(e)
        sys.exit(1)


def get_ecr_repos(region):
    """Return a list of ECR repositories.
    """
    london_ecr_repos = []
    ecr_client = boto3.client('ecr', region_name=region)
    repos = ecr_client.describe_repositories()

    for repo in repos.get('repositories'):
        london_ecr_repos.append(repo.get('repositoryName'))

    return london_ecr_repos


def pull_image(repository, tag, auth_creds):
    """Pull image from ECR repositoryself.
    """
    try:
        print(f"Pulling '{repository}' tagged as '{tag}'.")
        docker_client.images.pull(repository, tag=tag, auth_config=auth_creds)
    except Exception as e:
        print(e)
        sys.exit(1)


def image_tag(current_tag, new_tag):
    """Tag Docker image.
    """
    print(f"Retagging '{current_tag}' image to '{new_tag}'.")
    if docker_api.tag(current_tag, new_tag) is False:
        raise RuntimeError(f"Tagging from '{current_tag}' to '{new_tag}' failed.")


def push_image(repository, tag, auth_creds):
    """Push image to ECR repository.
    """
    try:
        print(f"Pushing image to '{repository}' tagged as '{tag}'.")
        docker_client.images.push(repository, tag=tag, auth_config=auth_creds)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    # Login to 'eu-west-2' region
    london_ecr_registry, london_auth_creds = ecr_login(LONDON_REGION)
    # Get 'eu-west-2' ECR repos list
    london_ecr_repos = get_ecr_repos(LONDON_REGION)
    print(f"'{LONDON_REGION}' region ECR repository list: {london_ecr_repos}")
    # Login to 'eu-west-1' region
    ireland_ecr_registry, ireland_auth_creds = ecr_login(IRELAND_REGION)

    for repo in london_ecr_repos:
        for tag in TAGS:
            # Pull image from Ireland ECR repo
            pull_image(f"{ireland_ecr_registry}/{repo}", tag, ireland_auth_creds)
            # Retag the image
            image_tag(f"{ireland_ecr_registry}/{repo}:{tag}", f"{london_ecr_registry}/{repo}:{tag}")
            # Push image to London ECR repo
            push_image(f"{london_ecr_registry}/{repo}", tag, london_auth_creds)

