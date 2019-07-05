__Usage:__

After redeploying an ECS service:
```
$ aws --region $AWS_REGION ecs update-service --cluster $ECS_CLUSTER_NAME --service $ECS_SERVICE_NAME --force-new-deployment
```

Check if the redeployment was successful:
```
$ python3 verify-ecs-service-redeployment.py [-h] -c $ECS_CLUSTER_NAME -s $ECS_SERVICE_NAME
                                          [-w WAIT_TIME]
                                          [-r AWS_DEFAULT_REGION]
```
