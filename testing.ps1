# Running these tests on a Windows host can be rather slow - running them inside a container appears to resolve this.

.\walkoff.ps1 up -dyr

docker build -t walkoff_tester -f testing\Dockerfile .

docker run --rm -it --network walkoff_network --name walkoff_tester `
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock `
    -e DOCKER_HOST=unix:///var/run/docker.sock `
    -e CONFIG_PATH=/app/data/test_config.yml `
    walkoff_tester $args

