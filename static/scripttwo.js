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
const captureBtn  = document.getElementById('capture');
captureBtn.addEventListener('click', () => {
  const canvas = faceapi.createCanvasFromMedia(video)
  document.body.append(canvas)
  const displaySize = { width: video.width, height: video.height }
  faceapi.matchDimensions(canvas, displaySize)

const options = new faceapi.TinyFaceDetectorOptions();
    faceapi.detectAllFaces(canvas, options).withFaceLandmarks().withFaceExpressions()
      .then(function(results) {
        // Process face detection results
        const resizedResults = faceapi.resizeResults(results, { width: video.videoWidth, height: video.videoHeight });
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
        faceapi.draw.drawDetections(canvas, resizedResults);
        var itoDataURL = canvas.toDataURL()
        // Perform face recognition using unique identifier
        performRecognition(itoDataURL);
      })
  .catch(function(error) {
    console.error(error);
  });
  });
      // Perform face recognition using unique identifier
      
      //  markAttendance(uniqueId);
      
      
   

// Perform face recognition using unique identifier
function performRecognition(toDataURL) {

  const base64Image = toDataURL;
  console.log(base64Image)
  // Make an API call to retrieve the unique identifier of the employee associated with the detected face
  $.ajax({
    type: 'POST',
    url:"{% url 'staffthree.html' %}",
    data:{
    'image':JSON.stringify(base64Image),  
    csrfmiddlewaretoken: '{{ csrf_token }}'
    },
    success: function(data) {
      // Call the callback function with the unique identifier
      alert('Success')
    },
    error: function(error) {
    alert('Errrooooooor')
    }
  });
}

