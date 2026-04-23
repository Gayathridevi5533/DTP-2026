navigator.geolocation.getCurrentPosition(pos => {
  fetch('/verify_location', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      lat: pos.coords.latitude,
      lon: pos.coords.longitude
    })
  });
});