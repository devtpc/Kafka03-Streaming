# Kafka Streaming Homework

## Introduction

This project is a homework at the EPAM Data Engineering Mentor program. The main idea behind this task is to focus on Kafka aspects and the Kafka Streams framework for implementing streaming solutions. Through this assignment, it is expected to gain experience working with the Kafka Streams framework and become familiar with the enrichment process of data in streaming applications.

Infrastructure should be setup with Terraform on an Azure Kubernetes Cluster, and the Kafka deployed on this cluster should read data from an Azure Blob Container. The original copyright belongs to [EPAM](https://www.epam.com/). 


Some instructions from the original task:

* Data “m12kafkastreams.zip” you can find [here](https://static.cdn.epam.com/uploads/583f9e4a37492715074c531dbd5abad2/dse/m12kafkastreams.zip). Unzip it and upload into provisioned via Terraform storage account.
* Deploy Kubernetes Service, to setup infrastructure use terraform scripts from module. Kafka will be deployed in Kubernetes Service, use Confluent Operator and Confluent Platform for this
* Modify Kafka Connect to read data from storage container into Kafka topic (expedia)
* Write Kafka Streams job to read data from Kafka topic (expedia) and calculate customer's duration of stay as days between requested check-in (srch_ci) and check-out (srch_co) date. Use underling logic to setup proper category.
  * "Erroneous data": null, less than or equal to zero
  * "Short stay": 1-4 days
  * "Standard stay": 5-10 days
  * "Standard extended stay": 11-14 days
  * "Long stay": 2 weeks plus
* Store enriched data in Kafka topic (expedia_ext). Visualized data in Kafka topic (expedia_ext) with KSQL. Show total amount of hotels (hotel_id) and number of distinct hotels (hotel_id) for each category.

## About the repo

This repo is hosted [here](https://github.com/devtpc/Kafka03-Streaming)

> [!NOTE]
> The original data files are not included in this repo, only the link.
> Some sensitive files, like configuration files, API keys, tfvars are not included in this repo.

## Documentation

> [!IMPORTANT]
> About 80-90% of this task is essentialy the same, as my previous work, [Kafka Connect](https://github.com/devtpc/Kafka02-Connect) Although I document the similar parts as well, they are not as detailed. In these cases please refer to [there](https://github.com/devtpc/Kafka02-Connect) for detailed explanations, especially the detailed commands behind the 'Makefile' commands 

## Prerequisites

* The necessiary software environment should be installed on the computer (python, spark, azure cli, docker, terraform, etc.)
* For Windows use Gitbash to run make and shell commands. (Task was deployed and tested on a Windows machine)
* Have an Azure account
* Have an Azure storage account ready for hosting the terraform backend


## Preparatory steps

### Download the data files

Download the data files from [here](https://static.cdn.epam.com/uploads/583f9e4a37492715074c531dbd5abad2/dse/m12kafkastreams.zip).
Exctract the zip file, and copy its content to this repo. Rename the `m12kafkastreams` folder to `data`.
The file structure should look like this:

![File structure image](/screenshots/img_file_structure.png)

### Setup your configuration

Go to the [configcripts folder](/configscripts/) and copy/rename the `config.conf.template` file to `config.conf`. Change the AZURE_BASE, DOCKER_IMAGE_NAME values as instructed within the file.

In the [configcripts folder](/configscripts/) copy/rename the `terraform_backend.conf.template` file to `terraform_backend.conf`. Fill the parameters with the terraform data.

Propagate your config data to other folders with `make refresh-confs` from the main folder.

The details are in comments in the config files.

### Create and push the Docker image for Azure Blob Connector

We need an image with the  Azure Blob Storage Source Connector to be used later in the confluent-platform.yaml. The dockerfile is ready in the [connectors folder](/connectors/). In the dockerfile we basically use `confluentinc/cp-server-connect-base:7.5.4` as base, and install the latest `kafka-connect-azure-blob-storage` and `kafka-connect-azure-blob-storage-source`

Before creating the image, make sure your docker daemon / docker desktop is running, and you are logged in your DockerHub account. Use `make docker-upload` to build and push your docker image.

## Create Azure base infrastructure with Terraform

Use `make createinfra` command to create the Azure infrastructure. This command uses terraform commands to create the Azure infrastructure.

To verify the infrastructure visually, login to the Azure portal, and view your resource groups. There are  2 new resource groups:

* the one, which was parameterized, named rg-youruniquename-yourregion, with the Kubernetes Service and the Storage account.

![AKS created 1 image](/screenshots/img_aks_created_1.png)

* the managed cluster resource group, starting with MC_

![AKS created 2 image](/screenshots/img_aks_created_2.png)

After entering the AKS, it can be observed that events are occuring, confirming that the cluster is up and running:

![AKS created 3 image](/screenshots/img_aks_created_3.png)

## Upload data to provisioned account

### Save needed keys from Azure
Storage access key will be needed for data access, so save the storage account key from Azure by typing `make retrieve-storage-keys`. This saves the storage key to `configscripts/az_secret.conf` file. 
### Upload data files to the storage account

Now, that you have your storage account and key ready, the data files can be uploaded to the storage. Type `make uploaddata` to upload the data files. 

The data is uploaded to the server:

![Data upload 1 img](/screenshots/img_data_uploaded.png)

## Deploy Confluent environment on the cluster
### Prepare the cluster before deployment

If you destroyed your previous AKS cluster, and now you are trying to set it up with the same name, you might need to edit your `.kube/.config` file to remove your previous credentials. 

Use `make retrieve-aks-credentials` to get the AKS credentials, and prepare the `kubectl` to use the cluster.

### Prepare the cluster for using Confluent

Use `make prepare-confluent` to prepare kubernetes for using confluent.

### Deploy the Confluent Kafka environment

Use `make deploy-kafka` to deploy the Confluent Platform Component, and a sample producer app and topic.

### Wait for all the pods to run

Check regularily with `kubectl get pods -o wide`, if all pods are running, and all heave READY 1/1 state! It may require several minutes. If everything is ready, we can go to the next step.

![KAS Kafka_running img](/screenshots/img_aks_kafka_running.png)


## Check the environment at the control center

### Setup port-forwarding

Use `make run-proxys` to start port-forwarding to the Control Center and to Connect Service, in order to use them as localhost. The command internally uses these 2 commands:
```
kubectl port-forward controlcenter-0 9021:9021
kubectl port-forward service/connect 8083:8083
```
Note, that if you are using these commands separately without the `make` command, you should run them in two new terminals, as they are blocking the terminal.

![Portforward img](/screenshots/img_portforward.png)

### Check Control Center

Control Center now can be opened at: [http://localhost:9021](http://localhost:9021)

It can be checked, that it is working:

![Control Center 1 img](/screenshots/img_controlcenter.png)

## Deploy the connector for the expedia topic and Azure blob storage

### Create the expedia topic

Use `make createtopic-expedia` to create the expedia topic. We can check in the Control Center that the topic is really created:

![Topic created img](/screenshots/img_topic_created.png)

### Prepare the Azure connector configuration

The created connector is the [azure-source-expedia.json](/connectors/azure-source-expedia.json) in the [/connectors](/connectors/) folder.

Use `make deploy-connector` to deploy the connector to the cluster. If there are no errors, the connector is deployed:

![Connector deployed 1 img](/screenshots/img_connector_deployed.png)


### Observe, that the connector is working

We can observe the connector logs, that it reads the data:

![Topic consumed 1 img](/screenshots/img_connector_reading_1.png)

On the Control Center we can observe, that the topic now has substantial data read, and the Offset is also greater than 0, meaning, that data is being read.

![Topic consumed 2 img](/screenshots/img_connector_reading_2.png)

## Performing the new tasks

Till this point, the task was basically the same as the previous [Kafka Connect](https://github.com/devtpc/Kafka02-Connect) task. The steps and the documentation there are more detailed, so if you need to go deeper into more details, refer to the documentation [there](https://github.com/devtpc/Kafka02-Connect). Note, that the only difference was in the `azure-source-expedia` connector file. In the previous version, there was a transformation applied, to  mask time from the date field using MaskField transformer. In this task this part was not a requirement, so it was deleted from the [azure-source-expedia.json](/connectors/azure-source-expedia.json) file


## Implement KStream application

When using Python as a programming language, the [faust library](https://github.com/robinhood/faust) can be used to create a stream applicaton. The soucre code of the app with the comments are in the [src](/src/) folder, in the [main.py](/src/main.py) file.

Some important sections from the source:

The faust library should be imported:
```
import faust
```

The classes/records used should be inherited from faust.Record


```
#Expedia record based on faust.Record
class ExpediaRecord(faust.Record):
    id: int
    date_time: str
    site_name: int
    posa_container: int
    user_location_country: int
    user_location_region: int
    user_location_city: int
    orig_destination_distance: float
    user_id: int
    is_mobile: int
    is_package: int
    channel: int
    srch_ci: str
    srch_co: str
    srch_adults_cnt: int
    srch_children_cnt: int
    srch_rm_cnt: int
    srch_destination_id: int
    srch_destination_type_id: int
    hotel_id: int


#Extended record, for the output topic
class ExpediaExtRecord(ExpediaRecord):
    stay_category: str

#A record, holding only the hotel id and the calculated stay
class ExpediaTestRecord(faust.Record, serializer = 'json'):
    hotel_id: int
    stay_category: str
```

app is based on faust.App

```
app = faust.App('kafkastreams', broker='kafka://kafka:9092')
```

topics are based on app.topic

```
source_topic = app.topic('expedia', value_type=ExpediaRecord)
destination_topic = app.topic('expedia_ext', value_type=ExpediaExtRecord)
test_topic = app.topic('expedia_test', value_type=ExpediaTestRecord)
```

The main stream-procssing function is decorated with `@app.agent`, and is `async`

```
@app.agent(source_topic, sink=[destination_topic])
async def handle(messages):
    async for message in messages:
```

The main logic is to read the dates from the input stream, calculate the differences, and group the numbers to the respective stay categories

```
#Calculate the day difference. On error use -1
try:
    from_date = parse_date(message.srch_ci)
    to_date = parse_date(message.srch_co)
    diff_days = (to_date - from_date).days
except Exception as e:
    diff_days = -1

#convert days to categories
if diff_days<=0:
    stay_category="Erroneous data"
elif diff_days<=4:
    stay_category="Short stay"
elif diff_days<=10:
    stay_category="Standard stay"
elif diff_days<=14:
    stay_category="Standard extended stay"
else:
    stay_category="Long stay"
```

Write the enriched data back to a new topic. Although 1 output topic would have been enough, I used 2 output topics, one as requested, with the enriched data, and another one - for testing purposes - with only the 2 important fields: `hotel_id` and the `stay_category`. I used `await test_topic.send` and `yield` logics paralelly

```
  # _ext topic
  input_data = message.to_representation()
  
  # _test topic
  test_record = ExpediaTestRecord(
      hotel_id = input_data['hotel_id'],
      stay_category= stay_category
  )

  await test_topic.send(value=test_record.dumps())  # _test topic
  yield ExpediaExtRecord(**input_data, stay_category=stay_category) # _ext topic
```


## Deploy application

### Build the Docker Image

The streaming app should be run in a Docker container. The build and push logic is the same as with the connector image, use `docker-app-build` to build, and `docker-app-push` to build and push (or `docker-app-upload` to to it in one command) the image to the registry. Note, that the [Dockerfile](/src/Dockerfile) for the app is in the [src](/src/) folder

### Create the extra topics

Use `make createtopic-expedia-ext` to create the extended and test expedia topics.

### Deploy the app

Use `make deploy-app` to deploy the app on the cluster. Observe, that after couple of seconds a pod, starting with the name `kstream-app` appears and running on the cluster


![App running img](/screenshots/img_app_running.png)

### Visually check the app running

Observe, that in the Control Center, the expedia_ext topic is receiving the messages, and the new categories appear in the expedia_ext topic:

![Messages_coming img](/screenshots/img_messages_coming.png)


In the Consumers, our kafkastreams app appears, and showing that the faust library is consuming the topic.


![Messages_coming img](/screenshots/img_app_consuming.png)

## Use ksqldb to visualize the result

As a first step, we are creating a stream from the topic:
```
CREATE STREAM expedia_stay_stream
(
    stay_category varchar,
    hotel_id bigint
) 
WITH (
    KAFKA_TOPIC='expedia_test',
    VALUE_FORMAT='JSON',
    KEY_FORMAT='JSON'
);
```

Then we are creating a Table, with the stay_categories and the hotels, with their counts of bookings

```
CREATE OR REPLACE TABLE hotel_stay_cat_counts AS 
SELECT stay_category, hotel_id, COUNT(*) AS stays 
FROM expedia_stay_stream 
GROUP BY stay_category, hotel_id
EMIT CHANGES;
```

Finally, we are creating another Table, where we aggregate all the data. This table containes per stay category:
* the number of distinct hotel ids
* the number of all hotels/seaches

```
CREATE OR REPLACE TABLE stay_counts AS 
SELECT stay_category, COUNT(*) AS count_distinct, SUM(stays) AS count_all 
FROM hotel_stay_cat_counts GROUP BY stay_category
EMIT CHANGES;
```

This is the flow of the streams/tables, and the created streams/tables:

![ksql flow img](/screenshots/img_ksqldb_flow.png)

![ksql available img](/screenshots/img_ksqldb_available.png)


Observe the results by using `SELECT * FROM stay_counts EMIT CHANGES;`

> [!NOTE]
> Running some of these queries could be problematic using the Control Center, showing some strange errors. I used the terminal to show the final results.
> In this case enter the ksqldb-cli or the server with `kubectl exec -it ksqldb-0  -n confluent -- /bin/sh`, and then access the ksql prompt with `ksql http://localhost:8088` 

While the process is running, the results are always updated with the new records

![ksql running img](/screenshots/img_ksqldb_running_1.png)


When the process is finished, run the `SELECT * FROM stay_counts EMIT CHANGES;` query again to view the final results.

![ksql running 2 img](/screenshots/img_ksqldb_running_2.png)


## Clean up your work
As the task has been finished, use `make destroy-cluster` to destroy the cluster!


