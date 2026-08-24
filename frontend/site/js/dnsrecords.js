/* Show only the fields the chosen source actually uses. The prefix is
   "" for the create form and "update" for the update one. */
function toggleSourceFields(prefix){
  const id = function(name){
    return prefix === "" ? name : prefix + name.charAt(0).toUpperCase() + name.slice(1);
  };
  const source = document.getElementById(id('sourceInput')).value;

  const portField = document.getElementById(id('sslPortField'));
  const urlField = document.getElementById(id('sourceUrlField'));

  /* Only a TLS record connects to a port, and only a SAML record has a
     document to read */
  portField.hidden = source !== 'tls';
  urlField.hidden = source !== 'saml';

  const hint = document.getElementById('uploadHint');
  if (hint) {
    hint.hidden = source !== 'upload';
  }
}

/* Read a chosen certificate file into the textarea, so the same request
   is sent whether it was picked or pasted */
function readCertFile(){
  const input = document.getElementById('uploadCertFile');
  const target = document.getElementById('uploadCertText');
  if (!input.files || input.files.length === 0) {
    return;
  }
  const reader = new FileReader();
  reader.onload = function(){
    target.value = reader.result;
  };
  /* DER is binary; reading it as text would mangle it, so those are
     sent by picking the file and letting the api read the bytes */
  reader.readAsText(input.files[0]);
}

/* Get DNS Records & Write to the Table */
async function getDnsRecords(){
    const url = "/api/dns"
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
              /* Only meaningful when something actually connects */
              sslPortElement.textContent =
                element.source === 'tls' ? element.ssl_port : '-';

              const sourceElement = document.createElement("td");
              const sourceBadge = document.createElement("span");
              sourceBadge.textContent = element.source;
              if (element.source === 'upload'){
                sourceBadge.className = 'badge bg-secondary';
                sourceBadge.title = 'Uploaded by hand, not re-checked automatically';
              } else if (element.source === 'saml'){
                sourceBadge.className = 'badge bg-info text-dark';
                sourceBadge.title = element.source_url || '';
              } else {
                sourceBadge.className = 'badge bg-light text-dark';
              }
              sourceElement.appendChild(sourceBadge);

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
                
                var updateSourceInput = document.getElementById('updateSourceInput');
                var updateSourceUrlInput = document.getElementById('updateSourceUrlInput');

                /* Clear the Values */
                updateDnsID.value = '';
                updateDnsInput.value = '';
                updateSslPortInput.value = '';
                updateSourceUrlInput.value = '';

                /* Populate the Values */
                updateDnsID.value = element.id;
                updateDnsInput.value = element.dns;
                updateSslPortInput.value = element.ssl_port;
                updateSourceInput.value = element.source;
                updateSourceUrlInput.value = element.source_url || '';
                toggleSourceFields('update');

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
              /* An uploaded certificate has no origin to go back to */
              checkCertButton.disabled = element.source === 'upload';

              /* Upload Action */
              const uploadButton = document.createElement("button");
              uploadButton.className = 'btn btn-success btn-sm';
              uploadButton.textContent = "Upload Cert"
              uploadButton.onclick = function(){
                document.getElementById('uploadDnsId').value = element.id;
                document.getElementById('uploadCertText').value = '';
                document.getElementById('uploadCertFile').value = '';
                $('#uploadCertModal').modal('toggle');
              }

              /* Appending Elements */
              rowElement.appendChild(idElement);
              rowElement.appendChild(dnsElement);
              rowElement.appendChild(sslPortElement);
              rowElement.appendChild(sourceElement);

              actionsElement.appendChild(checkCertButton);
              actionsElement.appendChild(uploadButton);
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
  var sourceInput = document.getElementById('sourceInput');
  var sourceUrlInput = document.getElementById('sourceUrlInput');

  var body = {
    "dns": dnsInput.value.toString(),
    "source": sourceInput.value
  };
  /* Each source carries only what it needs: a port to connect to, or a
     document to read */
  if (sourceInput.value === 'tls') {
    body.ssl_port = parseInt(sslPortInput.value);
  }
  if (sourceInput.value === 'saml') {
    body.source_url = sourceUrlInput.value.toString();
  }
  var raw = JSON.stringify(body);

  var missing = dnsInput.value === ""
    || (sourceInput.value === 'tls' && sslPortInput.value === "")
    || (sourceInput.value === 'saml' && sourceUrlInput.value === "");

  if (missing) {
    Swal.fire({
      icon: 'error',
      title: 'Blank Fields',
      text: 'Please do not leave blank fields.',
    })
  } else {
    const url = "/api/dns"
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
  const url = "/api/dns/"+id
  
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
  var updateSourceInput = document.getElementById('updateSourceInput');
  var updateSourceUrlInput = document.getElementById('updateSourceUrlInput');

  var body = {
    "dns": updateDnsInput.value.toString(),
    "source": updateSourceInput.value
  };
  if (updateSourceInput.value === 'tls') {
    body.ssl_port = parseInt(updateSslPortInput.value);
  }
  if (updateSourceInput.value === 'saml') {
    body.source_url = updateSourceUrlInput.value.toString();
  }
  var raw = JSON.stringify(body);

  var missing = updateDnsInput.value === ""
    || (updateSourceInput.value === 'tls' && updateSslPortInput.value === "")
    || (updateSourceInput.value === 'saml' && updateSourceUrlInput.value === "");

  if (missing) {
    Swal.fire({
      icon: 'error',
      title: 'Blank Fields',
      text: 'Please do not leave blank fields.',
    })
  } else {
    const url = "/api/dns/"+id
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
async function uploadCert(id){
  var certText = document.getElementById('uploadCertText');
  var certFile = document.getElementById('uploadCertFile');

  if (certText.value === "" && certFile.files.length === 0) {
    Swal.fire({
      icon: 'error',
      title: 'Blank Fields',
      text: 'Please choose a certificate file or paste one.',
    })
    return;
  }

  const url = "/api/cert/upload/"+id

  var myHeaders = new Headers();
  myHeaders.append("Content-Type", "application/json");

  var requestOptions = {
    method: 'POST',
    headers: myHeaders,
    body: JSON.stringify({"certificate": certText.value.toString()}),
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
        title: 'Certificate Uploaded',
        html: 'You can go to <a href="/certificates.html">Certificates</a> page to see the results.',
      }).then((result) => {
        getDnsRecords() // Get Records Again
        $('#uploadCertModal').modal('toggle');   // Toggle the Modal
        // Clear the Inputs
        certText.value = '';
        certFile.value = '';
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
