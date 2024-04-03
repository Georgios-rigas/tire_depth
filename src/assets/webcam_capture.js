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
            jpeg_quality: 90,
            constraints: {
              facingMode: { ideal: 'environment' } // Use the rear camera
            }
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
              // Check if a tire is detected in the captured image
              if (data.predicted_depth === 'No tire detected in the image') {
                // Update the output div with the captured image and the "no tire detected" message
                document.getElementById('output-image-upload').innerHTML = `
                  <img src="${data.image_data}" style="max-height: 150px; padding: 20px" />
                  <div style="color: #9932CC; font-size: 25px">No tire detected in the image</div>
                `;
              } else {
                // Update the output div with the captured image and predicted depth
                document.getElementById('output-image-upload').innerHTML = `
                  <img src="${data.image_data}" style="max-height: 150px; padding: 20px" />
                  <div style="color: #9932CC; font-size: 25px">Estimated Depth: ${data.predicted_depth}mm</div>
                `;
              }
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