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

//video.addEventListener('loadedmetadata', () => {
  const captureBtn = document.getElementById('capture')
  captureBtn.addEventListener('click', () => {
    const canvas = faceapi.createCanvasFromMedia(video)
    const displaySize = { width: video.width, height: video.height }
    faceapi.matchDimensions(canvas, displaySize)
    faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceExpressions()
      .then(detections => {
        alert('iiiiiidetections:  '+JSON.stringify(detections))
        alert('iiiiiiidisplaySize:  '+JSON.stringify(displaySize))
        const resizedDetections = faceapi.resizeResults(detections, displaySize)
        alert('iiiiiiiresizedDetections:  '+JSON.stringify(resizedDetections))
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
        faceapi.draw.drawDetections(canvas, resizedDetections)
        performRecognition(resizedDetections)
      })
  })
//})

function performRecognition(result) {
alert('result:  '+JSON.stringify(result))
alert('result.detection:  '+JSON.stringify(result[0].detection))
alert('result.detection.length:  '+result[0].detection.length))
  const canvas = document.createElement('canvas')
  canvas.width = video.width
  canvas.height = video.height
  const ctx = canvas.getContext('2d')
  if (result && result[0].detection && result[0].detection.length > 0) {
  alert('detecteddetecteddetecteddetecteddetected')
    const faces = result.detection[0].detections
alert('facesfacesfacesfaces:  '+JSON.stringify(faces))
    faces.forEach(face => {
      const box = face.detection.box
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
  console.log('passdetectionspassdetectionspassdetectionspassdetectionspassdetections')
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