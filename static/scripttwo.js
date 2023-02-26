const video = document.getElementById('video');

// Attach loadedmetadata event handler to video element
video.addEventListener('loadedmetadata', function() {
  // Create canvas element and resize it to match video size
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  // Attach click event handler to capture button
  const captureBtn = document.getElementById('capture');
  captureBtn.addEventListener('click', function() {
    // Draw current video frame onto canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Perform face detection on canvas
    const detectionPromise = faceapi.detectAllFaces(canvas, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceExpressions();
    detectionPromise.then(function(detections) {
      // Process face detection results
      const resizedDetections = faceapi.resizeResults(detections, { width: video.videoWidth, height: video.videoHeight });
      canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
      faceapi.draw.drawDetections(canvas, resizedDetections);

      // Perform face recognition using unique identifier
     // performRecognition(resizedDetections, function(uniqueId) {
      //  markAttendance(uniqueId);
      alert('Reached perform recognition and mark attendance')
      //});
    });
  });
});

// Perform face recognition using unique identifier
function performRecognition(detections, callback) {
  // Convert the face image to a base64-encoded string
  const canvas = document.createElement('canvas');
  canvas.width = detections.inputSize.width;
  canvas.height = detections.inputSize.height;
  const ctx = canvas.getContext('2d');
  detections.detections.forEach(function(detection) {
    const box = detection.detection.box;
    const x = box.x < 0 ? 0 : box.x;
    const y = box.y < 0 ? 0 : box.y;
    const width = box.x + box.width > canvas.width ? canvas.width - box.x : box.width;
    const height = box.y + box.height > canvas.height ? canvas.height - box.y : box.height;
    ctx.drawImage(video, x, y, width, height, box.x, box.y, width, height);
  });
  const base64Image = canvas.toDataURL();

  // Make an API call to retrieve the unique identifier of the employee associated with the detected face
  $.ajax({
    url: '/api/employee-recognition',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ image: base64Image }),
    success: function(data) {
      // Call the callback function with the unique identifier
      callback(data.employeeId);
    }
  });
}

// Mark employee attendance using the unique identifier
function markAttendance(uniqueId) {
  // Make an API call to mark attendance of the employee with the provided unique identifier
  $.ajax({
    url: '/api/mark-attendance',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ employeeId: uniqueId }),
    success: function(data) {
      console.log('Attendance marked successfully.');
    }
  });
}