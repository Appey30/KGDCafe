const video = document.getElementById('video');
const faceOffset = 50;
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri('../static/models'),
  faceapi.nets.faceLandmark68Net.loadFromUri('../static/models'),
  faceapi.nets.faceRecognitionNet.loadFromUri('../static/models'),
  faceapi.nets.faceExpressionNet.loadFromUri('../static/models')
  faceapi.nets.ssdMobilenetv1.loadFromUri('../static/models')
]).then(startVideo)
.then(() => console.log('Models loaded successfully'))
.catch(err => console.error(err))



function startVideo() {
console.log('startVideo() called')
  navigator.getUserMedia(
    { video: {} },
    stream => video.srcObject = stream,
    err => console.error(err)
  )
}

// Detect faces and display captured image
video.addEventListener('play', async () => {
  const canvas = faceapi.createCanvasFromMedia(video)
  document.body.append(canvas)

  const displaySize = { width: video.width, height: video.height }
  faceapi.matchDimensions(canvas, displaySize)

  setInterval(async () => {
    const detections = await faceapi.detectAllFaces(video, new faceapi.SsdMobilenetv1Options()).withFaceLandmarks().withFaceDescriptors()
    alert('detections:  '+detections)
    const resizedDetections = faceapi.resizeResults(detections, displaySize)

    // Clear canvas and draw detections
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
    faceapi.draw.drawDetections(canvas, resizedDetections)

    // Display captured image
    if (resizedDetections.length > 0) {
    alert('resizedDetections.length:  '+resizedDetections.length)
      const faceCanvas = document.createElement('canvas')
      const faceContext = faceCanvas.getContext('2d')
      faceCanvas.width = resizedDetections[0].detection.box.width
      faceCanvas.height = resizedDetections[0].detection.box.height
      faceContext.drawImage(video, resizedDetections[0].detection.box.x, resizedDetections[0].detection.box.y, resizedDetections[0].detection.box.width, resizedDetections[0].detection.box.height, 0, 0, faceCanvas.width, faceCanvas.height)
      document.body.append(faceCanvas)
      performRecognition(resizedDetections)
    }
  }, 100)
})







  
function performRecognition(detections) {
alert('I am going to perform Recognition')
};
