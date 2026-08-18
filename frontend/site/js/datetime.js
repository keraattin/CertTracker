/* Every datetime the api sends is UTC. These helpers render them in the
   timezone of the browser, so the dates read the same way as the clock
   on the wall of whoever is looking at the page. */

/* Format an api datetime in the local timezone */
function toLocalTime(value){
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const parsed = new Date(value);
  /* Leave anything unparseable exactly as it arrived, rather than
     showing "Invalid Date" */
  if (isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

/* Write a datetime into an element: local time as the text, the value the
   api sent behind the tooltip so the original stays verifiable */
function writeLocalTime(element, value){
  element.textContent = toLocalTime(value);
  if (value) {
    element.title = value;
  }
}

/* Name of the timezone the dates above are rendered in */
function localTimezone(){
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

/* Fill every element that names the timezone, so the page says which one
   the dates belong to instead of leaving the reader to guess */
function writeLocalTimezone(){
  const elements = document.getElementsByClassName('local-timezone');
  for (const element of elements){
    element.textContent = localTimezone();
  }
}
