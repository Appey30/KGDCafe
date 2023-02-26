
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
const captureBtn = document.getElementById('capture');
captureBtn.addEventListener('click', () => {
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
  }, 100)
  var itoDataURL=canvas.toDataURL();
  performRecognition(itoDataURL)
  
})

      // Perform face recognition using unique identifier
      
      //  markAttendance(uniqueId);
      
      
   

// Perform face recognition using unique identifier
function performRecognition(toDataURL) {
  // Convert the face image to a base64-encoded string
  const base64Image = toDataURL;

  

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

