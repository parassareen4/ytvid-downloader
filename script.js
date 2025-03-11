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
            throw new Error("Failed to fetch download link");
        }
        return response.blob(); // Get the file as a Blob
    })
    .then(blob => {
        // Create a downloadable link
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "video.mp4"; // Default file name
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);

        messageBox.innerText = "Download complete!";
    })
    .catch(error => {
        messageBox.innerText = "Error: " + error.message;
    });
}
