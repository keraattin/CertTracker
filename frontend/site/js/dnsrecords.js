/* Get DNS Records & Write to the Table */
async function getDnsRecords(){
    const url = "http://localhost:5000/api/dns"
    const requestOptions = {
        method: 'GET',
        mode: 'cors',
        redirect: 'follow'
    };
  
    const table = document.getElementById("dnsRecordsTable");
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
              dnsElement.textContent = element.dns;
  
              const sslPortElement = document.createElement("td");
              sslPortElement.textContent = element.ssl_port;

              /* Actions */
              const actionsElement = document.createElement("td");
              
              /* Update Actions */
              const updateButton = document.createElement("button");
              updateButton.className = 'btn btn-warning btn-sm';
              updateButton.textContent = "Update"
              updateButton.onclick = function(){
                var updateDnsID = document.getElementById('updateDnsId');
                var updateDnsInput = document.getElementById('updateDnsInput');
                var updateSslPortInput = document.getElementById('updateSslPortInput');
                
                /* Clear the Values */
                updateDnsID.value = '';
                updateDnsInput.value = '';
                updateSslPortInput.value = '';

                /* Populate the Values */
                updateDnsID.value = element.id;
                updateDnsInput.value = element.dns;
                updateSslPortInput.value = element.ssl_port;

                $('#updateDnsModal').modal('toggle');   // Toggle the Modal
              }

              /* Delete Actions */
              const deleteButton = document.createElement("button");
              deleteButton.className = 'btn btn-danger btn-sm';
              deleteButton.textContent =  "Delete"
              deleteButton.onclick = function(){
                const swalWithBootstrapButtons = Swal.mixin({
                  customClass: {
                    confirmButton: 'btn btn-danger',
                    cancelButton: 'btn btn-secondary'
                  },
                  buttonsStyling: false
                })
                swalWithBootstrapButtons.fire({
                  title: 'Are you sure?',
                  text: 'Do you want to delete the ' + element.dns + ' ?',
                  icon: 'warning',
                  showCancelButton: true,
                  reverseButtons: true,
                  confirmButtonText: 'Delete',
                  cancelButtonText: 'No, cancel!',
                }).then((result) => {
                  if (result.isConfirmed) {
                    deleteDnsRecord(element.id);
                  }
                })
              }
              
              /* Cert Check Action */
              const checkCertButton = document.createElement("button");
              checkCertButton.className = 'btn btn-info btn-sm';
              checkCertButton.textContent = "Check Cert"
              checkCertButton.onclick = function(){
                certCheck(element.id);
              }

              /* Appending Elements */
              rowElement.appendChild(idElement);
              rowElement.appendChild(dnsElement);
              rowElement.appendChild(sslPortElement);

              actionsElement.appendChild(checkCertButton);
              actionsElement.appendChild(updateButton);
              actionsElement.appendChild(deleteButton);
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

async function createDnsRecord(){
  var dnsInput = document.getElementById('dnsInput');
  var sslPortInput = document.getElementById('sslPortInput');

  var raw = JSON.stringify({
    "dns": dnsInput.value.toString(),
    "ssl_port": parseInt(sslPortInput.value)
  });

  if (dnsInput.value === "" || sslPortInput.value === "") {
    Swal.fire({
      icon: 'error',
      title: 'Blank Fields',
      text: 'Please do not leave blank fields.',
    })
  } else {
    const url = "http://localhost:5000/api/dns"
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    var requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
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
          title: 'Created',
        }).then((result) => {
          if (result.isConfirmed) {
            getDnsRecords() // Get Records Again
            $('#createDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            dnsInput.value = '';
            sslPortInput.value = '';
          } else if (result.isDenied) {
            getDnsRecords() // Get Records Again
            $('#createDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            dnsInput.value = '';
            sslPortInput.value = '';
          } else {
            getDnsRecords() // Get Records Again
            $('#createDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            dnsInput.value = '';
            sslPortInput.value = '';
          }
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
}

async function deleteDnsRecord(id){
  const url = "http://localhost:5000/api/dns/"+id
  
  var myHeaders = new Headers();
  myHeaders.append("Content-Type", "application/json");

  var requestOptions = {
    method: 'DELETE',
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
        title: 'Deleted',
      }).then((result) => {
        if (result.isConfirmed) {
          getDnsRecords() // Get Records Again
        } else if (result.isDenied) {
          getDnsRecords() // Get Records Again
        } else {
          getDnsRecords() // Get Records Again
        }
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

async function updateDnsRecord(id){
  var updateDnsInput = document.getElementById('updateDnsInput');
  var updateSslPortInput = document.getElementById('updateSslPortInput');

  var raw = JSON.stringify({
    "dns": updateDnsInput.value.toString(),
    "ssl_port": parseInt(updateSslPortInput.value)
  });
  if (updateDnsInput.value === "" || updateSslPortInput.value === "") {
    Swal.fire({
      icon: 'error',
      title: 'Blank Fields',
      text: 'Please do not leave blank fields.',
    })
  } else {
    const url = "http://localhost:5000/api/dns/"+id
    var myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    var requestOptions = {
      method: 'PUT',
      headers: myHeaders,
      body: raw,
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
          title: 'Updated',
        }).then((result) => {
          if (result.isConfirmed) {
            getDnsRecords() // Get Records Again
            $('#updateDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            updateDnsInput.value = '';
            updateSslPortInput.value = '';
          } else if (result.isDenied) {
            getDnsRecords() // Get Records Again
            $('#updateDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            updateDnsInput.value = '';
            updateSslPortInput.value = '';
          } else {
            getDnsRecords() // Get Records Again
            $('#updateDnsModal').modal('toggle');   // Toggle the Modal
            // Clear the Inputs
            updateDnsInput.value = '';
            updateSslPortInput.value = '';
          }
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