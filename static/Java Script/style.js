let attendanceID = null;
var lat;
var lon;

function checkActualLocation() {

    const result = document.getElementById("result");
    const status = document.getElementById("locationStatus");

    if (!navigator.geolocation) {

        result.innerText =
            "❌ Geolocation is not supported.";

        result.style.color = "red";

        status.innerText =
            "Location not supported";

        status.classList.add("absent-badge");

        return;
    }

    // Update location status while checking
    status.innerText =
        "Checking your location...";

    status.className =
        "status-badge";

    navigator.geolocation.getCurrentPosition(

        pos => {

            // Show that location was found
            status.innerText =
                "Location found";

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

                    status.innerText =
                        "✓ Location Verified";

                    status.className =
                        "status-badge present-badge";

                    document.getElementById("latitude").value =
                        pos.coords.latitude;

                    document.getElementById("longitude").value =
                        pos.coords.longitude;

                }

                else {

                    status.innerText =
                        "✕ Location not within allowed area";

                    status.className =
                        "status-badge absent-badge";

                }

            })

            .catch(error => {

                console.error(error);

                result.innerText =
                    "❌ Unable to verify location.";

                result.style.color = "red";

                status.innerText =
                    "Verification failed";

                status.className =
                    "status-badge absent-badge";

            });

        },

        err => {

            result.innerText =
                "❌ Please allow location access.";

            result.style.color = "red";

            status.innerText =
                "Location permission required";

            status.className =
                "status-badge absent-badge";

        }

    );
}

function checkLocation() {

    const result = document.getElementById("result");
    const status = document.getElementById("locationStatus");

    // Check schedule first
    fetch('/check_schedule')

        .then(res => res.json())

        .then(scheduleData => {

            if (scheduleData.status === "denied") {

                status.innerText =
                    "✕ Not in scheduled period";

                status.className =
                    "status-badge absent-badge";

                result.innerText =
                    scheduleData.message;

                result.style.color = "red";

                return;
            }

            // Only check location if currently scheduled
            checkActualLocation();

        })

        .catch(error => {

            console.error(error);

            result.innerText =
                "❌ Unable to check schedule.";

            result.style.color = "red";

        });
}

function submitReason1() {
    const reason =
        document.getElementById("study_reason").value;

    fetch('/submit_reason', {

        method: 'POST',

        headers: {
            'Content-Type': 'application/json'
        },

        body: JSON.stringify({

            lat: parseFloat(document.getElementById("latitude").value),

            lon: parseFloat(document.getElementById("longitude").value),

            study_reason: reason

        })


    })

    .then(res => res.json())

    .then(data => {

        alert("Study activity saved!");

    });

}

function submitReason() {

    const result = document.getElementById("result");
    const status = document.getElementById("locationStatus");
    const reason = document.getElementById("study_reason").value;

    // Check reason first
    // if (!reason.trim()) {

    //     result.innerText =
    //         "❌ Please enter your study reason.";

    //     result.style.color = "red";

    //     return;
    // }

    // Check schedule
    fetch('/check_schedule')

        .then(res => res.json())

        .then(scheduleData => {

            if (scheduleData.status === "denied") {

                result.innerText =
                    scheduleData.message;

                result.style.color = "red";

                return;
            }

            // Schedule is valid
            status.innerText =
                "Checking your location...";

            // Get location
            if (!navigator.geolocation) {

                result.innerText =
                    "❌ Geolocation is not supported.";

                result.style.color = "red";

                return;
            }

            navigator.geolocation.getCurrentPosition(

                pos => {

                    const latitude =
                        pos.coords.latitude;

                    const longitude =
                        pos.coords.longitude;

                    // Verify location
                    fetch('/verify_location', {

                        method: 'POST',

                        headers: {
                            'Content-Type': 'application/json'
                        },

                        body: JSON.stringify({
                            lat: latitude,
                            lon: longitude
                        })

                    })

                    .then(res => res.json())

                    .then(locationData => {

                        if (locationData.status !== "allowed") {

                            status.innerText =
                                "✕ Location not within allowed area";

                            status.className =
                                "status-badge absent-badge";

                            result.innerText =
                                "You are outside the allowed school location.";

                            result.style.color = "red";

                            return;
                        }

                        // Location is valid
                        status.innerText =
                            "✓ Location Verified";

                        status.className =
                            "status-badge present-badge";

                        // Submit attendance + reason
                        fetch('/submit_reason', {

                            method: 'POST',

                            headers: {
                                'Content-Type': 'application/json'
                            },

                            body: JSON.stringify({

                                lat: latitude,

                                lon: longitude,

                                study_reason: reason

                            })

                        })

                        .then(res => res.json())

                        .then(data => {

                            if (data.status === "allowed") {

                                result.innerText =
                                    "✓ Attendance submitted successfully.";

                                result.style.color =
                                    "green";

                                document.getElementById(
                                    "submitReasonButton"
                                ).disabled = true;

                            }

                            else {

                                result.innerText =
                                    data.message;

                                result.style.color =
                                    "red";

                            }

                        });

                    });

                },

                err => {

                    result.innerText =
                        "❌ Please allow location access.";

                    result.style.color =
                        "red";

                    status.innerText =
                        "Location permission required";

                    status.className =
                        "status-badge absent-badge";

                }

            );

        })

        .catch(error => {

            console.error(error);

            result.innerText =
                "❌ Unable to verify attendance.";

            result.style.color =
                "red";

        });
}

function updateClock() {

    const clock = document.getElementById("clock");

    if (!clock) {
        return;
    }

    const now = new Date();

    const time = now.toLocaleTimeString("en-NZ", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
    });

    clock.textContent = time;
}


updateClock();

setInterval(updateClock, 1000);

