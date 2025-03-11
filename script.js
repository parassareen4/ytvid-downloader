document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('url');
    const qualitySelect = document.getElementById('quality');
    const downloadBtn = document.getElementById('download-btn');
    const messageBox = document.getElementById('message');
    const downloadPathInput = document.getElementById('download-path');
    const chooseLocationBtn = document.getElementById('choose-location');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('download-progress');
    const progressText = document.getElementById('progress-text');
    
    let downloadPath = '';
    
    // Handle folder selection (only works with Electron-like environments)
    chooseLocationBtn.addEventListener('click', function() {
      messageBox.innerText = "Note: Browser security restricts choosing download folders. Files will be saved to your default download location.";
      downloadPathInput.value = "Default Downloads Folder";
      downloadPath = "default";
    });
    
    downloadBtn.addEventListener('click', function() {
      downloadVideo();
    });
    
    function downloadVideo() {
      const url = urlInput.value;
      const quality = qualitySelect.value;
      
      if (!url) {
        messageBox.innerText = "Please enter a YouTube URL.";
        return;
      }
      
      messageBox.innerText = "Preparing download...";
      
      // Show progress elements
      progressContainer.style.display = 'block';
      progressBar.value = 0;
      progressText.innerText = '0%';
      
      // Send request to our backend
      fetch("https://ytvid-downloader.onrender.com/prepare/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url, quality })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to prepare video download.");
        }
        return response.json();
      })
      .then(data => {
        if (data.download_url) {
          // Update message
          messageBox.innerText = "Download ready! Starting download...";
          
          // Create download link and click it
          const a = document.createElement("a");
          a.href = data.download_url;
          a.download = data.filename || `video.${quality === "audio" ? "mp3" : "mp4"}`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          
          // Set progress to complete
          progressBar.value = 100;
          progressText.innerText = '100%';
          
          setTimeout(() => {
            messageBox.innerText = "Download complete!";
          }, 2000);
        } else {
          messageBox.innerText = "Error: Download URL not found in response.";
        }
      })
      .catch(error => {
        messageBox.innerText = "Error: " + error.message;
        progressContainer.style.display = 'none';
      });
    }
  });