document.addEventListener('DOMContentLoaded', () => {
  // === DOM ELEMENTS ===
  const micBtn = document.getElementById('mic-btn');
  const uploadBtn = document.getElementById('upload-btn');
  const fileInput = document.getElementById('file-input');
  const statusLogo = document.getElementById('status-logo');
  const statusTitle = document.getElementById('status-title');
  const statusSubtitle = document.getElementById('status-subtitle');
  const bpmValue = document.getElementById('bpm-value');
  const canvas = document.getElementById('waveformCanvas');
  const ctx = canvas.getContext('2d');

  const tipsBtn = document.getElementById('tips-btn');
  const measureTipsPopup = document.getElementById('measure-tips-popup');
  const tipsCloseBtn = document.getElementById('tips-close-btn');

  // === APP STATE ===
  const TOTAL_SECONDS = 10;
  let isRecording = false;
  let mode = 'idle';
  let secondsElapsed = 0;
  let timerInterval = null;
  let mediaRecorder = null;
  let audioChunks = [];

  // Audio visualization
  let audioCtx = null;
  let analyser = null;
  let dataArray = null;
  let bufferLength = 0;

  // === POPUP ===
  function closeAllPopups() {
    if (measureTipsPopup) measureTipsPopup.style.display = 'none';
  }
  if (tipsBtn) {
    tipsBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      const isVisible = measureTipsPopup.style.display === 'block';
      closeAllPopups();
      measureTipsPopup.style.display = isVisible ? 'none' : 'block';
    });
  }
  if (tipsCloseBtn) {
    tipsCloseBtn.addEventListener('click', (event) => {
      event.preventDefault();
      closeAllPopups();
    });
  }
  window.addEventListener('click', () => closeAllPopups());
  if (measureTipsPopup) {
    measureTipsPopup.addEventListener('click', (event) => event.stopPropagation());
  }

  // === CANVAS RESIZE ===
  function resizeCanvasToDisplaySize() {
    const dpr = window.devicePixelRatio || 1;
    const displayWidth = canvas.clientWidth;
    const displayHeight = canvas.clientHeight;
    const needResize =
      canvas.width !== Math.floor(displayWidth * dpr) ||
      canvas.height !== Math.floor(displayHeight * dpr);
    if (needResize) {
      canvas.width = Math.floor(displayWidth * dpr);
      canvas.height = Math.floor(displayHeight * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }
  window.addEventListener('resize', resizeCanvasToDisplaySize);

  // === AUDIO WAVEFORM VISUALIZATION ===
  function setupAnalyser(stream) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    const source = audioCtx.createMediaStreamSource(stream);
    source.connect(analyser);
    bufferLength = analyser.fftSize;
    dataArray = new Uint8Array(bufferLength);
  }

  function drawWaveform() {
    resizeCanvasToDisplaySize();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const width = canvas.width;
    const height = canvas.height;
    const centerY = height / 2;

    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.7)';

    if (analyser && isRecording) {
      analyser.getByteTimeDomainData(dataArray);
      const sliceWidth = width / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * height / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
    } else {
      ctx.moveTo(0, centerY);
      ctx.lineTo(width, centerY);
    }

    ctx.stroke();
    requestAnimationFrame(drawWaveform);
  }

  // === SWEETALERT HELPERS ===
  function swalLoadingPredict() {
    return Swal.fire({
      title: "Analyzing audio...",
      html: `<div style="font-size:15px;color:#555;margin-top:8px;">
               Please wait while Voxify processes your breathing pattern.<br>
               <b>Extracting features...</b><br>
               <i>Running deep model inference...</i>
             </div>`,
      allowOutsideClick: false,
      showConfirmButton: false,
      didOpen: () => { Swal.showLoading(); },
      heightAuto: false
    });
  }

  function swalError(title, text) {
    return Swal.fire({ icon: 'error', title, text, confirmButtonText: 'OK', heightAuto: false });
  }
  function swalConfirm({ title, text, confirmText = 'Yes', cancelText = 'No' }) {
    return Swal.fire({
      icon: 'question', title, text,
      showCancelButton: true,
      confirmButtonText: confirmText,
      cancelButtonText: cancelText,
      reverseButtons: true,
      heightAuto: false
    });
  }
  function toastInfo(title) {
    return Swal.fire({
      toast: true, position: 'top-end', icon: 'info', title,
      showConfirmButton: false, timer: 1800, timerProgressBar: true, heightAuto: false
    });
  }

  // === STATUS HELPERS ===
  function setStatus(title, subtitle, ok = false) {
    if (statusTitle) statusTitle.textContent = title || '';
    if (statusSubtitle) statusSubtitle.textContent = subtitle || '';
    if (micBtn) micBtn.classList.toggle('active', ok);
  }
  function resetStats() { if (bpmValue) bpmValue.textContent = '--'; }

  // === TIMER ===
  function startTimer(onFinish) {
    secondsElapsed = 0;
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      secondsElapsed++;
      statusTitle.textContent = `Measuring... (${secondsElapsed}/${TOTAL_SECONDS}s)`;
      if (secondsElapsed >= TOTAL_SECONDS) {
        clearInterval(timerInterval);
        if (typeof onFinish === 'function') onFinish();
      }
    }, 1000);
  }
  function stopTimer() { clearInterval(timerInterval); }

  // === MIC RECORDING ===
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setupAnalyser(stream);
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mode = 'mic';
      isRecording = true;
      resetStats();
      setStatus(`Measuring... (0/${TOTAL_SECONDS}s)`, 'Breathe normally.', true);

      mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await finishMeasurement(audioBlob);
      };

      mediaRecorder.start();
      startTimer(() => stopRecording(true));
    } catch (err) {
      console.error(err);
      await swalError('Microphone error', 'Cannot access microphone.');
    }
  }

  async function stopRecording(isFinished = false) {
    isRecording = false;
    mode = 'idle';
    stopTimer();
    setStatus('Tap the mic to start', 'Hold your device close to the source of breathing sound', false);
    resetStats();
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
  }

  // === FINISH MEASUREMENT ===
  async function finishMeasurement(blob = null) {
    try {
      swalLoadingPredict();
      if (blob) {
        const formData = new FormData();
        formData.append('audio_file', blob, 'recorded.wav');

        // --- [Tambahan: cek dengan model filter dulu] ---
        const filterResponse = await fetch('/filter', { method: 'POST', body: formData });
        const filterData = await filterResponse.json();

        if (filterData.status === 'rejected') {
          Swal.close();
          await swalError('Not a Breathing Sound', filterData.message || 'Please try again.');
          return;
        }
        // ------------------------------------------------

        // Jika lolos filter → lanjut ke prediksi penyakit
        const response = await fetch('/predict', { method: 'POST', body: formData });
        if (response.redirected) {
          Swal.close();
          window.location.href = response.url;
        } else {
          const data = await response.json();
          Swal.close();
          await swalError('Failed', data.error || 'Prediction failed');
        }
      } else {
        Swal.close();
        window.location.href = '/report';
      }
    } catch (err) {
      console.error(err);
      Swal.close();
      await swalError('Upload failed', 'Please try again later.');
    }
  }

  // === FILE UPLOAD ===
  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      if (!file.type.startsWith('audio/')) {
        await swalError('Unsupported file', 'Please select an audio file (.wav, .mp3, .m4a, etc.)');
        e.target.value = '';
        return;
      }
      if (file.size > 25 * 1024 * 1024) {
        await swalError('File too large', 'Please choose a file ≤ 25 MB');
        e.target.value = '';
        return;
      }

      try {
        swalLoadingPredict();
        const formData = new FormData();
        formData.append('audio_file', file);

        // --- [Tambahan: cek dengan model filter dulu] ---
        const filterResponse = await fetch('/filter', { method: 'POST', body: formData });
        const filterData = await filterResponse.json();

        if (filterData.status === 'rejected') {
          Swal.close();
          await swalError('Not a Breathing Sound', filterData.message || 'Please try again.');
          return;
        }
        // ------------------------------------------------

        const response = await fetch('/predict', { method: 'POST', body: formData });
        if (response.redirected) {
          Swal.close();
          window.location.href = response.url;
        } else {
          const data = await response.json();
          Swal.close();
          await swalError('Failed', data.error || 'Prediction failed');
        }
      } catch (err) {
        console.error(err);
        Swal.close();
        await swalError('Upload failed', 'Please try again later');
      } finally {
        e.target.value = '';
      }
    });
  }

  // === MIC BUTTON EVENT ===
  if (micBtn) {
    micBtn.addEventListener('click', async () => {
      if (mode !== 'mic') {
        startRecording();
      } else {
        stopTimer();
        const res = await swalConfirm({
          title: `Stop recording at ${secondsElapsed}s?`,
          text: 'Process this recording or try again?',
          confirmText: 'Process',
          cancelText: 'Try again'
        });
        if (res.isConfirmed) {
          stopRecording(true);
        } else {
          stopRecording(false);
          toastInfo('Reset. Ready to record again.');
        }
      }
    });
  }

  // === START DRAW LOOP ===
  drawWaveform();
});
