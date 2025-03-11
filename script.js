function downloadVideo() {
    const url = document.getElementById("url").value;
    const quality = document.getElementById("quality").value;
    const messageBox = document.getElementById("message");

    if (!url) {
        messageBox.innerText = "Please enter a YouTube URL.";
        return;
    }

    messageBox.innerText = "Downloading... Please wait.";

    fetch("https://ytvid-downloader.onrender.com/download/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url, quality })
    })
    .then(response => response.json())
    .then(data => {
        messageBox.innerText = data.message || "Download started!";
    })
    .catch(error => {
        messageBox.innerText = "Error: " + error.message;
    });
}
