#!/bin/bash
source loadtest.env && \
echo "Building loads.json" && \
cat > loads.json <<EOF
{
  "name": "Shavar Server Testing",
  "plans": [

    {
      "name": "4 Servers",
      "description": "4 boxes",
      "steps": [
        {
          "name": "Shavar: Test Cluster",
          "instance_count": 4,
          "instance_region": "us-east-1",
          "instance_type": "m3.medium",
          "run_max_time": 600,
          "container_name": "rpappalax/ailoads-shavar:latest",
          "environment_data": [
            "URL_SHAVAR_SERVER=https://shavar.stage.mozaws.net/downloads",
            "CONNECTIONS=100",
            "TEST_DURATION=600"
          ],
          "volume_mapping": "/var/log:/var/log/$RUN_ID:rw",
          "docker_series": "shavar_tests
        }
      ]
    }
  ]
}
EOF
