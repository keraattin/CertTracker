/* Count the Certificates by Status & Write to the Cards */
function writeSummary(certs, dnsRecords){
  var valid = 0;
  var expiring = 0;
  var expired = 0;
  var failed = 0;

  for (const element of certs){
    if (element.status === 'expired'){
      expired++;
    } else if (element.status === 'expiring'){
      expiring++;
    } else {
      valid++;
    }
    /* Counted on its own: a failed check says nothing about the validity
       of the certificate that was fetched last */
    if (element.last_check_status === 'failed'){
      failed++;
    }
  }

  document.getElementById('summaryValid').textContent = valid;
  document.getElementById('summaryExpiring').textContent = expiring;
  document.getElementById('summaryExpired').textContent = expired;
  document.getElementById('summaryFailed').textContent = failed;

  /* A DNS record without a certificate has never been checked */
  const checkedIds = certs.map(element => element.dns_record.id);
  const neverChecked = dnsRecords.filter(
    element => !checkedIds.includes(element.id)
  ).length;

  document.getElementById('summaryTracked').textContent =
    dnsRecords.length + ' DNS record/s tracked, ' + neverChecked + ' never checked';
}

/* List the Certificates That Need Attention */
function writeAttentionTable(certs){
  const table = document.getElementById("attentionTable");
  const tableBody = table.querySelector("tbody");
  const emptyMessage = document.getElementById("attentionEmpty");

  // Clear the Table
  tableBody.innerHTML = "";

  /* Anything that is not plainly valid, soonest to expire first */
  const attention = certs
    .filter(element =>
      element.status !== 'valid' || element.last_check_status === 'failed'
    )
    .sort((a, b) => a.days_remaining - b.days_remaining);

  if (attention.length === 0){
    emptyMessage.hidden = false;
    table.hidden = true;
    return;
  }
  emptyMessage.hidden = true;
  table.hidden = false;

  // Populate the Table
  for (const element of attention){
    const rowElement = document.createElement("tr");

    const dnsElement = document.createElement("td");
    dnsElement.textContent = element.dns_record.dns;

    const sslPortElement = document.createElement("td");
    sslPortElement.textContent = element.dns_record.ssl_port;

    const notAfterElement = document.createElement("td");
    notAfterElement.textContent = element.not_after;

    const remainingDayElement = document.createElement("td");
    const diffDayBadge = document.createElement("span");
    diffDayBadge.textContent = element.days_remaining + ' day/s';
    if (element.status === 'expired' || element.days_remaining < 7){
      diffDayBadge.className = 'badge rounded-pill bg-danger';
    } else {
      diffDayBadge.className = 'badge rounded-pill bg-warning';
    }
    remainingDayElement.appendChild(diffDayBadge);

    const lastCheckElement = document.createElement("td");
    lastCheckElement.textContent = element.last_check;
    if (element.last_check_status === 'failed'){
      const failedBadge = document.createElement("span");
      failedBadge.textContent = 'CHECK FAILED';
      failedBadge.className = 'badge bg-danger';
      failedBadge.title = element.last_error || '';
      lastCheckElement.appendChild(document.createElement("br"));
      lastCheckElement.appendChild(failedBadge);
    }

    /* Appending Elements */
    rowElement.appendChild(dnsElement);
    rowElement.appendChild(sslPortElement);
    rowElement.appendChild(notAfterElement);
    rowElement.appendChild(remainingDayElement);
    rowElement.appendChild(lastCheckElement);

    tableBody.appendChild(rowElement);
  }
}

/* Get the Summary & Write to the Page */
async function getDashboard(){
  const requestOptions = {
      method: 'GET',
      mode: 'cors',
      redirect: 'follow'
  };

  /* Both lists are fetched: the certificates carry the status, the dns
     records tell how many of them have never been checked at all */
  await Promise.all([
      fetch("http://localhost:5000/api/cert", requestOptions),
      fetch("http://localhost:5000/api/dns", requestOptions)
    ])
    .then(responses => Promise.all(responses.map(response => response.json())))
    .then(([certs, dnsRecords]) => {
      writeSummary(certs, dnsRecords);
      writeAttentionTable(certs);
    })
    .catch(error => {
      Swal.fire({
        icon: 'error',
        title: 'Oops...',
        text: error,
      })
    });
}
