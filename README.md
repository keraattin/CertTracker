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
        - './api/Logs:/api/Logs'
    frontend:
      build: ./frontend
      ports:
        - "8080:80"
```

- Api service works on port 5000 (includes the in-process certificate fetcher). Its liveness can be checked at `/health`
- Frontend service works on 8080

### Step 3 : Change the environment variables (if you want to):

You can find them in `/api/Dockerfile`

| Variable | Default | Description |
| --- | --- | --- |
| `PORT` | `5000` | Port the api listens on |
| `DEBUG` | `False` | Flask debug mode, only used when running `app.py` directly |
| `SECRET_KEY` | `thisistestsecretkey` | Not important for this project at the moment, but you may still want to change it |
| `TIMEZONE` | `Etc/UTC` | Timezone the daily job runs in. Stored datetimes are always UTC |
| `DATABASE_URI` | `sqlite:////api/Database/database.db` | Overridable so the app can also run outside the container |
| `LOG_FILE` | `./Logs/cron.log` | Log file of the daily job |

### Step 4 : Build the containers

```
docker-compose up --build
```

## Usage
### Open the project
- Open your fav browser

- Go to the `http://localhost:8080` (if you didn't change the frontend port)

- The home page summarizes how many certificates are valid, expiring, expired or failed their last check, and lists the ones that need attention

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

- The `Details` button shows the subject, issuer, alternative names, serial number and signature algorithm of the certificate, along with the outcome of the last check

- If a check fails, the row keeps the last certificate that could be fetched and is marked `CHECK FAILED`. Hover the badge to see the error


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
- [ ] [Permit upload of certificate and fetching SAML certificates from public SAML endpoints]( https://github.com/keraattin/CertTracker/issues/5)

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.