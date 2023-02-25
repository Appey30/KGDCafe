const video = document.getElementById('video') 
    Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri('../static/models'),
      faceapi.nets.faceLandmark68Net.loadFromUri('../static/models'),
      faceapi.nets.faceRecognitionNet.loadFromUri('../static/models'),
      faceapi.nets.faceExpressionNet.loadFromUri('../static/models')
    ]).then(startVideo)

    // Get video stream and start capturing images
    function startVideo() {
      navigator.mediaDevices.getUserMedia(
        { video: {} },
        stream => video.srcObject = stream,
        err => console.error(err)
      )
    }

    // Capture employee face image and perform recognition
    const captureBtn = document.getElementById('capture')
    captureBtn.addEventListener('click', () => {
      const canvas = faceapi.createCanvasFromMedia(video)
      const displaySize = { width: video.width, height: video.height }
      faceapi.matchDimensions(canvas, displaySize)
      faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceExpressions().then(detections => {
        const resizedDetections = faceapi.resizeResults(detections, displaySize)
        canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
        faceapi.draw.drawDetections(canvas, resizedDetections)
        performRecognition(resizedDetections).then(uniqueId => {
          markAttendance(uniqueId)
        })
      })
    })

    // Perform face recognition using unique identifier
    function performRecognition(detections) {
      // Convert the face image to a base64-encoded string
      const canvas = document.createElement('canvas')
      canvas.width = detections.inputSize.width
      canvas.height = detections.inputSize.height
      const ctx = canvas.getContext('2d')
      detections.detections.forEach(detection => {
        const box = detection.detection.box
        const x = box.x < 0 ? 0 : box.x
        const y = box.y < 0 ? 0 : box.y
        const width = box.x + box.width > canvas.width ? canvas.width - box.x : box.width
        const height = box.y + box.height > canvas.height ? canvas.height - box.y : box.height
        ctx.drawImage(video, x, y, width, height, box.x, box.y, width, height)
      })
      const base64Image = canvas.toDataURL()

      // Make an API call to retrieve the unique identifier of the employee associated with the detected face
      return new Promise((resolve, reject) => {
        $.ajax({
          url: "{% url 'stafftwo.html' %}",
          type: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({ image: base64Image }),
          success: function(data) {
            resolve(data.employeeId)
            alert("Match")
          },
          error: function(xhr, status, error) {
            reject(error)
          }
        })
      })
    }

    // Mark employee attendance using the unique identifier
    function markAttendance(uniqueId) {
       //Make an API call to mark attendance of the employee with the provided unique identifier
      $.ajax({
        url: "{% url 'stafftwo.html' %}",
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ employeeId: uniqueId })
      })
    }

