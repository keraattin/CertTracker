/* Get Certificate Records & Write to the Table */
async function getCerts(){
  const url = "http://localhost:5000/api/cert"
  const requestOptions = {
      method: 'GET',
      mode: 'cors',
      redirect: 'follow'
  };

  const table = document.getElementById("certsTable");
  const tableBody = table.querySelector("tbody");

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

            const notBeforeElement = document.createElement("td");
            notBeforeElement.textContent = element.not_before;

            const notAfterElement = document.createElement("td");
            notAfterElement.textContent = element.not_after;

            const remainingDayElement = document.createElement("td");
            var notAfterDay = new Date(element.not_after);
            var todayDay = new Date().getTime();
            var diff = notAfterDay - todayDay;
            var diffAsDay = Math.round(diff / 1000 / 60 / 60 / 24);
            
            const diffDayBadge = document.createElement("span");
            diffDayBadge.textContent = diffAsDay + ' day/s';
            if (diffAsDay < 0 ){
              const outOfDateBadge = document.createElement("span");
              outOfDateBadge.textContent = 'OUT OF DATE';
              outOfDateBadge.className = 'badge bg-danger';
              remainingDayElement.appendChild(outOfDateBadge);
              diffDayBadge.className = 'badge rounded-pill bg-danger';
            } else if (diffAsDay < 7 ){
              diffDayBadge.className = 'badge rounded-pill bg-danger';
            } else if ( diffAsDay < 30 ){
              diffDayBadge.className = 'badge rounded-pill bg-warning';
            } else if ( diffAsDay > 30 ){
              diffDayBadge.className = 'badge rounded-pill bg-success';
            }
            //remainingDayElement.textContent = diffAsDay.toString();
            remainingDayElement.appendChild(diffDayBadge);
            
            const lastUpdateElement = document.createElement("td");
            lastUpdateElement.textContent = element.last_update;

            /* Actions */
            const actionsElement = document.createElement("td");
            /* Cert Check Action */
            const checkCertButton = document.createElement("button");
            checkCertButton.className = 'btn btn-info btn-sm text-light';
            checkCertButton.textContent = "Check Cert"
            checkCertButton.onclick = function(){
              certCheck(element.dns_record.id);
            }

            /* Appending Elements */
            actionsElement.appendChild(checkCertButton);

            rowElement.appendChild(idElement);
            rowElement.appendChild(dnsElement);
            rowElement.appendChild(sslPortElement);
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
  const url = "http://localhost:5000/api/cert/cert_check/"+id
  
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
  const getUrl = "http://localhost:5000/api/dns"
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
        dnsArr.push(element.id)
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
   for(const id of dnsArr){
    const url = "http://localhost:5000/api/cert/cert_check/"+id
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      mode: 'cors'
    };

    await fetch(url, requestOptions)
      .then(response => response.json())
      .then(result => {
        const rowElement = document.createElement("tr");
        const dnsElement = document.createElement("td");
        dnsElement.textContent = result.dns_record.dns;
        
        const okElement = document.createElement("td");
        const okSpan = document.createElement("span");
        okSpan.className = "bi bi-check-all";
        
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
