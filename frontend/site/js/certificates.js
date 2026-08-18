/* Format a Detail Value for Display */
function detailValue(value){
  /* Rows stored before a column existed simply have no value */
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (value === true) {
    return "Yes";
  }
  if (value === false) {
    return "No";
  }
  return value;
}

/* Fill the Details Modal & Show It */
function showCertDetails(cert){
  document.getElementById('detailsDns').textContent = detailValue(cert.dns_record.dns);
  document.getElementById('detailsSubject').textContent = detailValue(cert.subject);
  document.getElementById('detailsIssuer').textContent = detailValue(cert.issuer);
  document.getElementById('detailsSans').textContent = detailValue(cert.sans);
  document.getElementById('detailsSerial').textContent = detailValue(cert.serial_number);
  document.getElementById('detailsSignature').textContent = detailValue(cert.signature_algorithm);
  document.getElementById('detailsSelfSigned').textContent = detailValue(cert.self_signed);
  document.getElementById('detailsLastCheck').textContent = toLocalTime(cert.last_check);
  document.getElementById('detailsLastError').textContent = detailValue(cert.last_error);

  $('#detailsModal').modal('toggle');   // Toggle the Modal
}

/* Get Certificate Records & Write to the Table */
async function getCerts(){
  const url = "/api/cert"
  const requestOptions = {
      method: 'GET',
      mode: 'cors',
      redirect: 'follow'
  };

  const table = document.getElementById("certsTable");
  const tableBody = table.querySelector("tbody");

  writeLocalTimezone();

  await fetch(url, requestOptions)
      .then(response => response.json())
      .then(result => {
          // Clear the Table
          tableBody.innerHTML = "";

          // Populate the Table
          for (const element of result){
            const rowElement = document.createElement("tr");

            const idElement = document.createElement("td");
            idElement.textContent = element.id;

            const dnsElement = document.createElement("td");
            dnsElement.textContent = element.dns_record.dns;

            const sslPortElement = document.createElement("td");
            sslPortElement.textContent = element.dns_record.ssl_port;

            const issuerElement = document.createElement("td");
            issuerElement.textContent = detailValue(element.issuer);

            const notBeforeElement = document.createElement("td");
            writeLocalTime(notBeforeElement, element.not_before);

            const notAfterElement = document.createElement("td");
            writeLocalTime(notAfterElement, element.not_after);

            /* The remaining days and the status come from the api, so the
               thresholds live in one place instead of being repeated here */
            const remainingDayElement = document.createElement("td");
            const diffDayBadge = document.createElement("span");
            diffDayBadge.textContent = element.days_remaining + ' day/s';
            if (element.status === 'expired'){
              const outOfDateBadge = document.createElement("span");
              outOfDateBadge.textContent = 'OUT OF DATE';
              outOfDateBadge.className = 'badge bg-danger';
              remainingDayElement.appendChild(outOfDateBadge);
              diffDayBadge.className = 'badge rounded-pill bg-danger';
            } else if (element.status === 'expiring'){
              /* The last week stays red, as it was before */
              if (element.days_remaining < 7){
                diffDayBadge.className = 'badge rounded-pill bg-danger';
              } else {
                diffDayBadge.className = 'badge rounded-pill bg-warning';
              }
            } else {
              diffDayBadge.className = 'badge rounded-pill bg-success';
            }
            remainingDayElement.appendChild(diffDayBadge);

            const lastUpdateElement = document.createElement("td");
            writeLocalTime(lastUpdateElement, element.last_update);
            /* The certificate above is the last one that could be fetched.
               Without this badge a host that stopped answering would keep
               looking perfectly healthy */
            if (element.last_check_status === 'failed'){
              const failedBadge = document.createElement("span");
              failedBadge.textContent = 'CHECK FAILED';
              failedBadge.className = 'badge bg-danger';
              failedBadge.title = element.last_error || '';
              lastUpdateElement.appendChild(document.createElement("br"));
              lastUpdateElement.appendChild(failedBadge);
            }

            /* Actions */
            const actionsElement = document.createElement("td");
            /* Cert Check Action */
            const checkCertButton = document.createElement("button");
            checkCertButton.className = 'btn btn-info btn-sm text-light';
            checkCertButton.textContent = "Check Cert"
            checkCertButton.onclick = function(){
              certCheck(element.dns_record.id);
            }

            /* Details Action */
            const detailsButton = document.createElement("button");
            detailsButton.className = 'btn btn-secondary btn-sm';
            detailsButton.textContent = "Details"
            detailsButton.onclick = function(){
              showCertDetails(element);
            }

            /* Appending Elements */
            actionsElement.appendChild(checkCertButton);
            actionsElement.appendChild(detailsButton);

            rowElement.appendChild(idElement);
            rowElement.appendChild(dnsElement);
            rowElement.appendChild(sslPortElement);
            rowElement.appendChild(issuerElement);
            rowElement.appendChild(notBeforeElement);
            rowElement.appendChild(notAfterElement);
            rowElement.appendChild(remainingDayElement);
            rowElement.appendChild(lastUpdateElement);
            rowElement.appendChild(actionsElement);

            tableBody.appendChild(rowElement);
          };
        })
      .catch(error => {
          Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: error,
          })
        });
}

async function certCheck(id){
  const url = "/api/cert/cert_check/"+id
  
  var myHeaders = new Headers();
  myHeaders.append("Content-Type", "application/json");


  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    mode: 'cors'
  };
  
  await fetch(url, requestOptions)
    .then(response => {
      if (!response.ok) {
          return response.json().then(errData => { throw new Error(errData.message+" ["+response.status+"]"+response.statusText) })
      } else {
          response.json()
      }
    })
    .then(result => {
      Swal.fire({
        icon: 'success',
        title: 'Certificate Checked',
        html: 'You can go to <a href="/certificates.html">Certificates</a> page to see the results.',
      }).then((result) => {
        getCerts() // Get Records Again
      })
    })
    .catch(error => {
      Swal.fire({
        icon: 'error',
        title: 'Oops...',
        text: error,
      })
    });
}

async function checkAllCerts(){
  const getUrl = "/api/dns"
  const getRequestOptions = {
      method: 'GET',
      mode: 'cors',
      redirect: 'follow'
  };
  var dnsArr = [];
  $('#checkingModal').modal('toggle');
  await fetch(getUrl, getRequestOptions)
    .then(response => response.json())
    .then(result => {
      for (const element of result){
        /* Keeping the dns around so a failed check can still be named:
           an error response carries no dns_record */
        dnsArr.push({id: element.id, dns: element.dns})
      }
    })
    .catch(error => {
      Swal.fire({
        icon: 'error',
        title: 'Oops...',
        text: error,
      })
    });

    const table = document.getElementById("checkingTable");
    const tableBody = table.querySelector("tbody");
    tableBody.innerHTML = "";

    /* Looping over DNS Records & Checking Certificates */
   for(const record of dnsArr){
    const url = "/api/cert/cert_check/"+record.id
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      mode: 'cors'
    };

    await fetch(url, requestOptions)
      .then(response => {
        const rowElement = document.createElement("tr");
        const dnsElement = document.createElement("td");
        dnsElement.textContent = record.dns;

        const okElement = document.createElement("td");
        const okSpan = document.createElement("span");
        /* A host that could not be reached used to be dropped from this
           table, which read as if it had never been checked at all */
        if (response.ok){
          okSpan.className = "bi bi-check-all";
        } else {
          okSpan.className = "bi bi-x-lg text-danger";
        }

        okElement.appendChild(okSpan);
        rowElement.appendChild(dnsElement);
        rowElement.appendChild(okElement);
        tableBody.appendChild(rowElement);
      })
      .catch(error => console.log('error', error));
   }
  getCerts()
  $('#checkingModal').modal('toggle');
}
