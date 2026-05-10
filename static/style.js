function checkLocation() {

    const result = document.getElementById("result");

    // NO GEOLOCATION
    if (!navigator.geolocation) {

        result.innerText =
            "❌ Geolocation is not supported.";

        result.style.color = "red";

        return;
    }

    // GET LOCATION
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
                        "✅ Attendance Recorded";

                    result.style.color = "green";

                }

                else {

                    result.innerText =
                        "❌ Too far away";

                    result.style.color = "red";
                }

            });

        },

        err => {

            result.innerText =
                "❌ Please allow location access.";

            result.style.color = "red";

        }

    );
}