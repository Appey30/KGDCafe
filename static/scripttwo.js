const video = document.getElementById('video');
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri('../static/models'),
  faceapi.nets.faceLandmark68Net.loadFromUri('../static/models'),
  faceapi.nets.faceRecognitionNet.loadFromUri('../static/models'),
  faceapi.nets.faceExpressionNet.loadFromUri('../static/models')
]).then(startVideo)


function startVideo() {
  navigator.getUserMedia(
    { video: {} },
    stream => video.srcObject = stream,
    err => console.error(err)
  )
}

video.addEventListener('play', () => {
  var resizedDetections = '';
  const canvas = faceapi.createCanvasFromMedia(video)
  document.body.append(canvas)
  const displaySize = { width: video.width, height: video.height }
  faceapi.matchDimensions(canvas, displaySize)
  setInterval(async () => {
    const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceExpressions()
    resizedDetections = faceapi.resizeResults(detections, displaySize)
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
    faceapi.draw.drawDetections(canvas, resizedDetections)
    faceapi.draw.drawFaceLandmarks(canvas, resizedDetections)
    faceapi.draw.drawFaceExpressions(canvas, resizedDetections)
  }, 100).then(performRecognition(resizedDetections))
  
})

      // Perform face recognition using unique identifier
      
      //  markAttendance(uniqueId);
      
      
   

// Perform face recognition using unique identifier
function performRecognition(detections) {
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
    url: '{% url "staffthree.html" %}',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ image: base64Image }),
    success: function(data) {
      // Call the callback function with the unique identifier
      alert('Success')
    }
  });
}

