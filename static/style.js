let attendanceID = null;

function checkLocation() {

    const result = document.getElementById("result");

    if (!navigator.geolocation) {

        result.innerText =
            "❌ Geolocation is not supported.";

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

                attendanceID = data.id;

                if (data.status === "allowed") {

                    result.innerText =
                        "✅ Attendance Recorded";

                    result.style.color = "green";

                    // SHOW TEXTBOX
                    document.getElementById("studyBox").style.display = "block";

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


function submitReason() {

    const reason =
        document.getElementById("study_reason").value;

    fetch('/submit_reason', {

        method: 'POST',

        headers: {
            'Content-Type': 'application/json'
        },

        body: JSON.stringify({

            id: attendanceID,

            study_reason: reason

        })

    })

    .then(res => res.json())

    .then(data => {

        alert("Study activity saved!");

    });

}