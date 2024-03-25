function loadScript(url, callback) {
  var script = document.createElement("script");
  script.type = "text/javascript";
  if (script.readyState) {
    script.onreadystatechange = function() {
      if (script.readyState == "loaded" || script.readyState == "complete") {
        script.onreadystatechange = null;
        callback();
      }
    };
  } else {
    script.onload = function() {
      callback();
    };
  }
  script.src = url;
  document.getElementsByTagName("head")[0].appendChild(script);
}

function setupWebcam() {
  loadScript("https://cdnjs.cloudflare.com/ajax/libs/webcamjs/1.0.26/webcam.min.js", function() {
    console.log("WebcamJS loaded successfully.");

    var cameraBtn = document.getElementById('camera-btn');
    if (cameraBtn) {
      console.log("'camera-btn' button found.");
      cameraBtn.addEventListener('click', function() {
        if (cameraBtn.textContent === 'Open Camera') {
          console.log("Open camera button clicked.");
          Webcam.set({
            width: 320,
            height: 240,
            image_format: 'jpeg',
            jpeg_quality: 90
          });
          var cameraModal = document.getElementById('camera-modal');
          if (cameraModal) {
            console.log("'camera-modal' element found. Attaching webcam...");
            Webcam.attach('#camera-modal');
          } else {
            console.error("'camera-modal' element not found.");
          }
        } else if (cameraBtn.textContent === 'Capture Image') {
          console.log("Capture button clicked. Attempting to capture image...");
          Webcam.snap(function(data_uri) {
            console.log("Image captured.");
            console.log("Data URI size: ", data_uri.length);

            // Send the captured image data to the Python backend using an HTTP POST request
            fetch('/capture', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ image_data: data_uri })
            })
            .then(response => response.json())
            .then(data => {
              // Update the output div with the captured image and predicted depth
              document.getElementById('output-image-upload').innerHTML = `
                <img src="${data.image_data}" style="max-height: 300px; padding: 10px" />
                <hr />
                <div style="color: #7FDBFF; font-size: 24px">Predicted Depth: ${data.predicted_depth}</div>
              `;

              // Detach the webcam after capturing the image
              Webcam.reset();
            })
            .catch(error => {
              console.error('Error:', error);
            });
          });
        }
      });
    } else {
      console.error("'camera-btn' button not found.");
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(setupWebcam, 1000);
});