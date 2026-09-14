const start = document.querySelector('#startCall');
const end = document.querySelector('#endCall');
const state = document.querySelector('#voiceState');
const transcript = document.querySelector('#transcript');
const waveform = document.querySelector('#waveform');
const fields = [...document.querySelectorAll('.voice-form input, .voice-form select')];
let active = null;

function status(text) { state.textContent = text; }
function line(speaker, text) {
  const row = document.createElement('div');
  row.className = 'transcript-line';
  const label = document.createElement('b');
  label.textContent = speaker;
  const content = document.createElement('span');
  content.textContent = text;
  row.append(label, content);
  transcript.append(row);
  transcript.scrollTop = transcript.scrollHeight;
  return content;
}
async function stop(message = 'Call ended') {
  const call = active;
  active = null;
  if (call) {
    call.abort.abort();
    clearTimeout(call.limit);
    clearTimeout(call.wait);
    await call.room?.disconnect();
    call.audio.forEach(el => el.remove());
  }
  fields.forEach(el => el.disabled = false);
  start.disabled = false;
  start.classList.remove('hidden');
  end.classList.add('hidden');
  waveform.classList.remove('active');
  status(message);
}
end.addEventListener('click', () => stop());
// Never leave the microphone running behind the text-chat tab.
document.addEventListener('demochange', event => {
  if (event.detail !== 'voiceTab' && active) stop('Call ended. Ready for another conversation.');
});
window.addEventListener('pagehide', () => { active?.room?.disconnect(); });
start.addEventListener('click', async () => {
  if (active) return;
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    status('Microphone access requires HTTPS or localhost.'); return;
  }
  const call = { abort: new AbortController(), audio: [], segments: new Map() };
  active = call;
  fields.forEach(el => el.disabled = true);
  start.classList.add('hidden');
  end.classList.remove('hidden');
  transcript.replaceChildren();
  status('Connecting...');
  // Distinguish "never reached LiveKit" from "connected, but no agent worker picked up the call".
  call.wait = setTimeout(() => {
    if (active !== call) return;
    stop(call.room?.state === 'connected'
      ? 'The voice assistant did not join. It may be offline. Please try again shortly.'
      : 'Connection timed out. Please try again.');
  }, 30000);
  try {
    const response = await fetch('/api/voice/token', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      signal: call.abort.signal,
      body: JSON.stringify({ name: document.querySelector('#callName').value.trim(),
        company: document.querySelector('#callCompany').value.trim(),
        goal: document.querySelector('#callGoal').value,
        language: document.querySelector('#callLanguage').value }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(typeof error.detail === 'string' ? error.detail : 'Voice service is unavailable. Please try again later.');
    }
    const config = await response.json();
    const { Room, RoomEvent, Track } = await import('https://cdn.jsdelivr.net/npm/livekit-client@2.15.6/+esm');
    if (active !== call) return;
    const room = new Room();
    call.room = room;
    room.on(RoomEvent.TrackSubscribed, track => {
      if (active !== call || track.kind !== Track.Kind.Audio) return;
      const audio = track.attach();
      audio.hidden = true;
      document.body.append(audio);
      call.audio.push(audio);
    });
    room.on(RoomEvent.TranscriptionReceived, (segments, participant) => {
      if (active !== call) return;
      for (const segment of segments) {
        const key = `${participant?.identity}:${segment.id}`;
        let el = call.segments.get(key);
        if (!el) {
          el = line(participant?.identity === room.localParticipant.identity ? 'You' : 'AI', '');
          call.segments.set(key, el);
        }
        el.textContent = segment.text;
      }
      transcript.scrollTop = transcript.scrollHeight;
    });
    room.on(RoomEvent.ParticipantAttributesChanged, (_changes, participant) => {
      if (active !== call) return;
      const value = participant.attributes['lk.agent.state'];
      if (value) {
        clearTimeout(call.wait);
        status(({ listening: 'Listening - your turn', thinking: 'Thinking...', speaking: 'Speaking - you can interrupt' })[value] || 'Connected');
        waveform.classList.toggle('active', value === 'speaking');
      }
    });
    room.on(RoomEvent.Disconnected, () => { if (active === call) stop('Call disconnected. You can start again.'); });
    await room.connect(config.server_url, config.participant_token);
    if (active !== call) { await room.disconnect(); return; }
    await room.startAudio();
    await room.localParticipant.setMicrophoneEnabled(true, {
      echoCancellation: true, noiseSuppression: true, autoGainControl: true,
    });
    if (active !== call) { await room.disconnect(); return; }
    status('Connected - waiting for the assistant');
    call.limit = setTimeout(() => { if (active === call) stop('Call complete. Thank you!'); }, config.duration_seconds * 1000);
  } catch (error) {
    if (active !== call) return;
    const message = error.name === 'NotAllowedError'
      ? 'Microphone permission was denied. Allow it in your browser and try again.'
      : error.message || 'Unable to connect. Please try again.';
    await stop(message);
  }
});
