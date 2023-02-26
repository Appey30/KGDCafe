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

video.addEventListener('loadedmetadata', () => {
  const captureBtn = document.getElementById('capture')
  captureBtn.addEventListener('click', () => {
    const canvas = faceapi.createCanvasFromMedia(video)
    const displaySize = { width: video.width, height: video.height }
    faceapi.matchDimensions(canvas, displaySize)
    faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceExpressions()
      .then(detections => {
        const resizedDetections = faceapi.resizeResults(detections, displaySize)
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
        faceapi.draw.drawDetections(canvas, resizedDetections)
        performRecognition(resizedDetections)
      })
  })
})

function performRecognition(detections) {
console.log('performRecognitionperformRecognitionperformRecognitionperformRecognitionperformRecognition')
  const canvas = document.createElement('canvas')
  canvas.width = video.width
  canvas.height = video.height
  const ctx = canvas.getContext('2d')
  if (detections && detections.detections) {
    detections.detections.forEach(detection => {
      const box = detection.detection.box
      const x = box.x < 0 ? 0 : box.x
      const y = box.y < 0 ? 0 : box.y
      const width = box.x + box.width > canvas.width ? canvas.width - box.x : box.width
      const height = box.y + box.height > canvas.height ? canvas.height - box.y : box.height
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