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
    
    // Handle folder selection
    chooseLocationBtn.addEventListener('click', function() {
      messageBox.innerText = "Note: Browser security restricts choosing download folders. Files will be saved to your default download location.";
      downloadPathInput.value = "Default Downloads Folder";
      downloadPath = "default";
    });
    
    downloadBtn.addEventListener('click', function() {
      downloadVideo();
    });
    
    // Also trigger download on Enter key in the URL field
    urlInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        downloadVideo();
      }
    });
    
    function downloadVideo() {
      const url = urlInput.value.trim();
      const quality = qualitySelect.value;
      
      if (!url) {
        messageBox.innerText = "Please enter a YouTube URL.";
        return;
      }
      
      // Basic URL validation
      if (!isValidYouTubeUrl(url)) {
        messageBox.innerText = "Please enter a valid YouTube URL.";
        return;
      }
      
      // Disable button and show loading state
      downloadBtn.disabled = true;
      downloadBtn.textContent = "Processing...";
      messageBox.innerText = "Preparing download... This may take a minute.";
      
      // Show progress elements
      progressContainer.style.display = 'block';
      progressBar.value = 10; // Show some initial progress
      progressText.innerText = 'Processing...';
      
      // Simulate progress while waiting for server
      let progressInterval = simulateProgress();
      
      // Send request to our backend
      fetch("https://ytvid-downloader.onrender.com/prepare/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url, quality })
      })
      .then(response => {
        clearInterval(progressInterval);
        
        if (!response.ok) {
          return response.json().then(data => {
            throw new Error(data.detail || "Failed to prepare video download.");
          });
        }
        return response.json();
      })
      .then(data => {
        if (data.download_url) {
          // Update progress to almost complete
          progressBar.value = 90;
          progressText.innerText = 'Starting download...';
          
          // Update message with video title if available
          if (data.title) {
            messageBox.innerText = `Downloading: "${data.title}"`;
          } else {
            messageBox.innerText = "Download ready! Starting download...";
          }
          
          // Create download link and click it
          const a = document.createElement("a");
          a.href = data.download_url;
          a.download = data.filename || `video.${quality === "audio" ? "mp3" : "mp4"}`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          
          // Set progress to complete
          progressBar.value = 100;
          progressText.innerText = 'Complete!';
          
          setTimeout(() => {
            messageBox.innerText = "Download complete! The file will be in your downloads folder.";
            downloadBtn.disabled = false;
            downloadBtn.textContent = "Download";
          }, 2000);
        } else {
          messageBox.innerText = "Error: Download URL not found in response.";
          downloadBtn.disabled = false;
          downloadBtn.textContent = "Download";
          progressContainer.style.display = 'none';
        }
      })
      .catch(error => {
        clearInterval(progressInterval);
        messageBox.innerText = "Error: " + error.message;
        progressContainer.style.display = 'none';
        downloadBtn.disabled = false;
        downloadBtn.textContent = "Download";
      });
    }
    
    function isValidYouTubeUrl(url) {
      // Basic validation for YouTube URLs
      const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
      return youtubeRegex.test(url);
    }
    
    function simulateProgress() {
      let progress = 10;
      return setInterval(() => {
        if (progress < 80) {
          progress += Math.random() * 3;
          progressBar.value = progress;
          progressText.innerText = 'Processing...';
        }
      }, 500);
    }
  });