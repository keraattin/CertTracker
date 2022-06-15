## The Goal of The Project
The aim of the project is to track the expired or nearly expired certificates from a single point.

![Dns Records](/docs/images/DnsRecords.png "Dns Records")

![Certificates](/docs/images/Certificates.png "Certificates")


## Installation
### Step 1 : Clone the repo

```
git clone https://github.com/keraattin/CertTracker
```
### Step 2 : Configure the exposed ports (if you want to)

You can find the configurations in the `docker-compose.yaml` file

```
services:
    api:
      build: ./api
      ports:
        - "5000:5000"
      volumes:
        - './api/Database:/api/Database'
    cert-checker:
      build: ./cert-checker
      ports:
        - "5001:5001"
      volumes:
        - './cert-checker/logs:/cert-checker/logs'
    frontend:
      build: ./frontend
      ports:
        - "8080:80"
```

- Api service works on port 5000
- Certificate Checker service works on port 5001
- Frontend service works on 8080

### Step 3 : Change the secret keys (if you want to):

Although the secret key is not important for this project at the moment but you may still want to change it. 

You can find secret key configs in `/api/Dockerfile` and `/cert-checker/Dockerfile`

```
ENV SECRET_KEY "thisistestsecretkey"
```

### Step 4 : Build the containers

```
docker-compose up --build
```

## Usage
### Open the project
- Open your fav browser

- Go to the `http://localhost:8080` (if you didn't change the frontend port)

### Create DNS record
- Go to the `DnsRecords` Page

- Press the `Add New` button in the upper right corner

- Type your DNS or Ip Address

- Type the port of the SSL Certificate

- Hit the `Create` button

![Add Dns](/docs/images/AddDns.png "AddDns")

### Check Certificates 
- After adding a DNS record, you may check the Certificate by clicking the `Check Cert` button under the actions section in the `DnsRecords` Page.

![Check Cert Dns](/docs/images/CheckCertDns.png "Check Cert Dns")

- If you have already checked the Certificate, certificates will be listed in the `Certificates` Page. you may check the Certificate again by clicking the `Check Cert` button under the actions section in the `Certificates` Page

![Check Cert Cert](/docs/images/CheckCertCert.png "Check Cert Cert")


### Check All Certificates
- Go to the `Certificates` Page

- Press the `Check All Certs` button in the upper right corner

- Wait for finish

![Check All Certs](/docs/images/CheckAllCerts.png "Check All Certs")

## Build With
- Python
- Bootstrap
- Javascript

## Roadmap

- [X] [Add Scheduled Jobs to Check Certificates Daily]( https://github.com/keraattin/CertTracker/issues/1)
- [ ] [Add Send Mail Notification Function]( https://github.com/keraattin/CertTracker/issues/2)
- [ ] [Add Time Conversion to User Local Time in Frontend]( https://github.com/keraattin/CertTracker/issues/3)

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.