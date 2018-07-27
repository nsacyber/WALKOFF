# Building walkoff-app and walkoff-worker images:

```
cd walkoff-app
docker build -t x.azurecr.io/walkoff-app:vy .
docker push x.azurecr.io/walkoff-app:vy
cd ..
```
```
cd walkoff-worker
docker build -t x.azurecr.io/walkoff-worker:vy .
docker push x.azurecr.io/walkoff-worker:vy
cd ..
```

Where `x` is your Azure resource group, and `y` is the version you want to tag this image with (update this each time you build.)

In `k8s_manifests/walkoff-app.yaml` and `k8s_manifests/walkoff-workers.yaml`, replace `x.azurecr.io/walkoff-app:vy` and `x.azurecr.io/walkoff-worker:vy` with the values you used above

# Deploying WALKOFF

This assumes you have completed the above section.

```
cd k8s_manifests`

kubectl apply -f redis-primary.yaml
kubectl apply -f redis-secondary.yaml
kubectl apply -f redis-sentinel.yaml

kubectl apply -f case-db.yaml
kubectl apply -f walkoff-db.yaml
kubectl apply -f execution-db.yaml

kubectl apply -f walkoff-workers.yaml
kubectl apply -f walkoff-app.yaml
```

Verify pods:

`kubectl get pods`

Output should be similar to the below:

```
NAME                              READY     STATUS    RESTARTS   AGE
postgres-casedb-7zft6             1/1       Running   0          2d
postgres-executiondb-ck4tt        1/1       Running   0          2d
postgres-walkoffdb-jw4nn          1/1       Running   0          2d
redis-primary-0                   1/1       Running   0          2d
redis-secondary-0                 1/1       Running   0          2d
redis-secondary-1                 1/1       Running   0          2d
redis-sentinel-0                  1/1       Running   0          2d
redis-sentinel-1                  1/1       Running   0          2d
redis-sentinel-2                  1/1       Running   0          2d
walkoff-app-776c4cfdcd-w5h4v      1/1       Running   0          37m
walkoff-worker-766b65fb7f-4cpc2   1/1       Running   0          42m
walkoff-worker-766b65fb7f-gm9tj   1/1       Running   0          42m
walkoff-worker-766b65fb7f-pxcw9   1/1       Running   0          42m
walkoff-worker-766b65fb7f-szh8n   1/1       Running   0          42m
walkoff-worker-766b65fb7f-tx6ww   1/1       Running   0          42m
```

Verify services:

`kubectl get svc`

Output should be similar to the below:

```
NAME                   TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)             AGE
kubernetes             ClusterIP      10.0.0.1       <none>           443/TCP             4d
postgres-casedb        ClusterIP      10.0.5.0       <none>           5432/TCP            2d
postgres-executiondb   ClusterIP      10.0.117.116   <none>           5432/TCP            2d
postgres-walkoffdb     ClusterIP      10.0.31.107    <none>           5432/TCP            2d
redis-primary          ClusterIP      None           <none>           6379/TCP            2d
redis-secondary        ClusterIP      None           <none>           6379/TCP            2d
redis-sentinel         ClusterIP      None           <none>           26379/TCP           2d
walkoff-app-internal   ClusterIP      10.0.204.202   <none>           5556/TCP,5557/TCP   38m
walkoff-app-public     LoadBalancer   10.0.181.152   211.92.226.222   80:30145/TCP        38m
```

Access web interface using the `EXTERNAL-IP` of `walkoff-app-public`.