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
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to fetch video.");
        }
        return response.blob(); // Convert response to a Blob
    })
    .then(blob => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "video.mp4"; // Adjust file extension accordingly
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
        messageBox.innerText = "Download started!";
    })
    .catch(error => {
        messageBox.innerText = "Error: " + error.message;
    });
}
