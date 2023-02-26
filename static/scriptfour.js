const video = document.getElementById('video');
const faceOffset = 50;
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
  const canvas = faceapi.createCanvasFromMedia(video)
  document.body.append(canvas)
  const displaySize = { width: video.width, height: video.height }
  faceapi.matchDimensions(canvas, displaySize)
  setInterval(async () => {
    const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceDescriptors()
    const resizedDetections = faceapi.resizeResults(detections, displaySize)
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
    faceapi.draw.drawDetections(canvas, resizedDetections)
    faceapi.draw.drawFaceLandmarks(canvas, resizedDetections)
    faceapi.draw.drawFaceExpressions(canvas, resizedDetections)
    alert('resizedDetections1: '+JSON.stringify(resizedDetections))
    if (resizedDetections.length > 0) {
      performRecognition(resizedDetections)
      alert('resizedDetections2: '+JSON.stringify(resizedDetections))
    }
  }, 100)
})


function performRecognition(detections) {
  const canvas = document.createElement('canvas')
  canvas.width = detections.inputSize.width
  alert('canvas.width: '+canvas.width)
  canvas.height = detections.inputSize.height
  alert('canvas.height: '+canvas.height)
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