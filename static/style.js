function checkLocation() {

    const result = document.getElementById("result");

    result.innerText = "Checking your location...";
    result.style.color = "black";

    if (!navigator.geolocation) {

        result.innerText =
            "❌ Geolocation is not supported on this device.";

        result.style.color = "red";

        return;
    }

    navigator.geolocation.getCurrentPosition(

        pos => {

            fetch('/verify_location', {

                method: 'POST',

                headers: {
                    'Content-Type': 'application/json'
                },

                body: JSON.stringify({
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                })

            })

            .then(res => res.json())

            .then(data => {

                if (data.status === "allowed") {

                    result.innerText =
                        "✅ Your attendance has been recorded.";

                    result.style.color = "green";

                } else {

                    result.innerText =
                        "❌ You are outside school grounds.";

                    result.style.color = "red";
                }

            });

        },

        err => {

            if (err.code === 1) {

                result.innerText =
                    "❌ Please allow location access.";

            } else if (err.code === 2) {

                result.innerText =
                    "❌ Unable to detect your location.";

            } else if (err.code === 3) {

                result.innerText =
                    "❌ Location request timed out.";

            } else {

                result.innerText =
                    "❌ Unknown location error.";
            }

            result.style.color = "red";
        },

        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }

    );
}