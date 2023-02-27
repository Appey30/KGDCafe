const video = document.getElementById('video');
const faceOffset = 0;
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri('../static/models'),
  faceapi.nets.faceLandmark68Net.loadFromUri('../static/models'),
  faceapi.nets.faceRecognitionNet.loadFromUri('../static/models'),
  faceapi.nets.faceExpressionNet.loadFromUri('../static/models'),
  faceapi.nets.ssdMobilenetv1.loadFromUri('../static/models')
]).then(startVideo)
.then(() => console.log('Models loaded successfully'))
.catch(err => console.error(err))


function startVideo() {
  console.log('startVideo() called')
  navigator.getUserMedia(
    { video: {} },
    stream => {
      video.srcObject = stream
      video.addEventListener('loadedmetadata', () => {
        video.play()
      })
    },
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

    const resizedDetections = faceapi.resizeResults(detections, displaySize)

    // Clear canvas and draw detections
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
    faceapi.draw.drawDetections(canvas, resizedDetections)

    // Display captured image
    if (resizedDetections.length > 0) {
      const faceCanvas = document.createElement('canvas')
      const faceContext = faceCanvas.getContext('2d')
      faceCanvas.width = resizedDetections[0].detection.box.width
      faceCanvas.height = resizedDetections[0].detection.box.height
      faceContext.drawImage(video, resizedDetections[0].detection.box.x + faceOffset, resizedDetections[0].detection.box.y, resizedDetections[0].detection.box.width, resizedDetections[0].detection.box.height, 0, 0, faceCanvas.width, faceCanvas.height)
      document.body.append(faceCanvas)
      performRecognition(resizedDetections)
    }
  }, 100)
})

function performRecognition(detections) {
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')

  if (detections.detections && detections.detections.length > 0) {
    detections.detections.forEach(detection => {
      const box = detection.detection.box
      const x = box.x + faceOffset // add an offset to the right
      const y = box.y
      const width = box.width
      const height = box.height
      ctx.drawImage(video, x, y, width, height, box.x, box.y, width, height)
    })

    const base64Image = canvas.toDataURL()

    const img = document.createElement('img')
    img.src = base64Image
    document.body.append(img)

    fetch('/static/staffthree', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image: base64Image })
    })
    .then(response => response.json())
    .then(data => {
      markAttendance(data.employeeId)
    })
  } else {
    console.log('No faces detected')
  }
}

function markAttendance(uniqueId) {
console.log('markAttendancemarkAttendancemarkAttendancemarkAttendancemarkAttendance')
  fetch('/static/staffthree', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ employeeId: uniqueId })
  })
}
