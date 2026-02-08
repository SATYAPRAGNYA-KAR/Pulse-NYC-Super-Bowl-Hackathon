// Global state
const state = {
    currentVideoUrl: null,
    videoDuration: 0,
    videoTitle: '',
    player: null,
    processedChunks: {},
    isPlaying: false,
    currentTime: 0,
    chunkDuration: 5,
    processingQueue: [],
    analytics: {
        totalChunks: 0,
        avgProcessingTime: 0,
        eventsDetected: 0,
        peakExcitement: 0
    }
};

// API Configuration
const API_BASE = window.location.origin;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupNavigation();
    setupVideoInput();
    setupYouTubePlayer();
    
    // Check backend health
    checkBackendHealth();
}

// Navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageName = link.dataset.page;
            switchPage(pageName);
            
            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function switchPage(pageName) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
        
        // Update analytics if switching to analytics page
        if (pageName === 'analytics') {
            updateAnalytics();
        }
    }
}

// Video Input Setup
function setupVideoInput() {
    const loadBtn = document.getElementById('loadVideoBtn');
    const urlInput = document.getElementById('videoUrlInput');
    
    loadBtn.addEventListener('click', () => {
        const url = urlInput.value.trim();
        if (url) {
            loadVideo(url);
        } else {
            showError('Please enter a valid YouTube URL');
        }
    });
    
    // Allow Enter key to load video
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadBtn.click();
        }
    });
}

async function loadVideo(url) {
    showLoading(true);
    hideError();
    
    try {
        // Get video info from backend
        const response = await fetch(`${API_BASE}/api/video/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_url: url })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load video');
        }
        
        // Store video info
        state.currentVideoUrl = url;
        state.videoDuration = data.duration;
        state.videoTitle = data.title;
        
        // Show video info
        displayVideoInfo(data);
        
        // Load YouTube player
        loadYouTubeVideo(url);
        
        // Show processing section
        document.getElementById('processingSection').style.display = 'block';
        
        // Initialize timeline
        initializeTimeline();
        
        showToast('Video loaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error loading video:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

function displayVideoInfo(data) {
    const infoDiv = document.getElementById('videoInfo');
    infoDiv.innerHTML = `
        <strong>${data.title}</strong><br>
        Duration: ${formatTime(data.duration)} | Chunk Size: ${data.chunk_duration}s
    `;
    infoDiv.classList.add('show');
    
    document.getElementById('totalTime').textContent = formatTime(data.duration);
}

// YouTube Player Setup
let playerReady = false;

function setupYouTubePlayer() {
    // YouTube API will call this when ready
    window.onYouTubeIframeAPIReady = () => {
        playerReady = true;
        console.log('YouTube API ready');
    };
}

function loadYouTubeVideo(url) {
    const videoId = extractVideoId(url);
    
    if (!videoId) {
        showError('Invalid YouTube URL');
        return;
    }
    
    // Wait for API to be ready
    const checkReady = setInterval(() => {
        if (window.YT && window.YT.Player) {
            clearInterval(checkReady);
            createPlayer(videoId);
        }
    }, 100);
}

function createPlayer(videoId) {
    state.player = new YT.Player('videoPlayer', {
        videoId: videoId,
        playerVars: {
            'playsinline': 1,
            'controls': 1,
            'modestbranding': 1
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    console.log('Player ready');
    setupPlayerControls();
    
    // Start time tracking
    startTimeTracking();
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        state.isPlaying = true;
        updateStatus('Playing');
    } else if (event.data == YT.PlayerState.PAUSED) {
        state.isPlaying = false;
        updateStatus('Paused');
    } else if (event.data == YT.PlayerState.ENDED) {
        state.isPlaying = false;
        updateStatus('Ended');
    }
}

function setupPlayerControls() {
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    
    playBtn.addEventListener('click', () => {
        if (state.player) {
            state.player.playVideo();
        }
    });
    
    pauseBtn.addEventListener('click', () => {
        if (state.player) {
            state.player.pauseVideo();
        }
    });
}

function startTimeTracking() {
    setInterval(() => {
        if (state.player && state.isPlaying) {
            const currentTime = state.player.getCurrentTime();
            state.currentTime = currentTime;
            
            // Update display
            document.getElementById('currentTime').textContent = formatTime(currentTime);
            
            // Check if we need to process current chunk
            const chunkIndex = Math.floor(currentTime / state.chunkDuration);
            processChunkIfNeeded(chunkIndex);
            
            // Prefetch next chunk
            prefetchNextChunk(chunkIndex);
        }
    }, 500); // Check every 500ms
}

// Chunk Processing
async function processChunkIfNeeded(chunkIndex) {
    const startTime = chunkIndex * state.chunkDuration;
    
    // Don't process if already processed or in queue
    if (state.processedChunks[startTime] || state.processingQueue.includes(startTime)) {
        return;
    }
    
    // Add to queue
    state.processingQueue.push(startTime);
    updateTimelineChunk(chunkIndex, 'processing');
    
    const processingStartTime = Date.now();
    
    try {
        const response = await fetch(`${API_BASE}/api/process/chunk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_url: state.currentVideoUrl,
                start_time: startTime,
                duration: state.chunkDuration
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Processing failed');
        }
        
        // Calculate latency
        const latency = Date.now() - processingStartTime;
        document.getElementById('latency').textContent = `${latency}ms`;
        
        // Store processed chunk
        state.processedChunks[startTime] = data;
        
        // Update UI
        updateTranscript(data.transcript);
        visualizeAudio(data.amplitudes);
        detectEvents(data);
        updateTimelineChunk(chunkIndex, 'completed');
        updateCurrentChunk(chunkIndex);
        
        // Update analytics
        state.analytics.totalChunks++;
        state.analytics.avgProcessingTime = 
            (state.analytics.avgProcessingTime * (state.analytics.totalChunks - 1) + latency) / 
            state.analytics.totalChunks;
        
        // Remove from queue
        const queueIndex = state.processingQueue.indexOf(startTime);
        if (queueIndex > -1) {
            state.processingQueue.splice(queueIndex, 1);
        }
        
        console.log(`Chunk ${chunkIndex} processed in ${latency}ms`);
        
    } catch (error) {
        console.error('Error processing chunk:', error);
        updateTimelineChunk(chunkIndex, 'error');
        
        // Remove from queue
        const queueIndex = state.processingQueue.indexOf(startTime);
        if (queueIndex > -1) {
            state.processingQueue.splice(queueIndex, 1);
        }
    }
}

async function prefetchNextChunk(currentChunkIndex) {
    const nextChunkIndex = currentChunkIndex + 1;
    const startTime = nextChunkIndex * state.chunkDuration;
    
    // Only prefetch if not already processed or processing
    if (!state.processedChunks[startTime] && !state.processingQueue.includes(startTime)) {
        // Don't await - let it process in background
        processChunkIfNeeded(nextChunkIndex);
    }
}

// UI Updates
function updateTranscript(transcript) {
    const display = document.getElementById('transcriptDisplay');
    if (transcript && transcript.text) {
        display.textContent = transcript.text;
        display.scrollTop = display.scrollHeight;
    }
}

function visualizeAudio(amplitudes) {
    const canvas = document.getElementById('audioCanvas');
    const ctx = canvas.getContext('2d');
    
    if (!amplitudes || amplitudes.length === 0) return;
    
    // Clear canvas
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw waveform
    const barWidth = canvas.width / amplitudes.length;
    const maxAmplitude = Math.max(...amplitudes);
    
    amplitudes.forEach((amplitude, i) => {
        const normalizedHeight = (amplitude / (maxAmplitude || 1)) * canvas.height;
        const x = i * barWidth;
        const y = canvas.height - normalizedHeight;
        
        // Color gradient based on amplitude
        const hue = 200 + (amplitude * 100);
        ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
        ctx.fillRect(x, y, barWidth - 1, normalizedHeight);
    });
}

function detectEvents(chunkData) {
    const { amplitudes, transcript } = chunkData;
    
    if (!amplitudes || !transcript) return;
    
    const maxAmplitude = Math.max(...amplitudes);
    const avgAmplitude = amplitudes.reduce((a, b) => a + b, 0) / amplitudes.length;
    
    // Update peak excitement
    if (maxAmplitude > state.analytics.peakExcitement) {
        state.analytics.peakExcitement = maxAmplitude;
    }
    
    // Detect high-excitement moments
    if (maxAmplitude > 0.7 || avgAmplitude > 0.5) {
        addEvent(chunkData.start_time, 'High Excitement', transcript.text.substring(0, 100));
        state.analytics.eventsDetected++;
    }
    
    // Keyword detection
    const keywords = ['touchdown', 'fumble', 'interception', 'score', 'penalty'];
    const text = transcript.text.toLowerCase();
    
    keywords.forEach(keyword => {
        if (text.includes(keyword)) {
            addEvent(chunkData.start_time, `Detected: ${keyword}`, transcript.text.substring(0, 100));
            state.analytics.eventsDetected++;
        }
    });
}

function addEvent(timestamp, eventType, description) {
    const eventsList = document.getElementById('eventsList');
    
    // Clear placeholder
    if (eventsList.textContent.includes('No events')) {
        eventsList.innerHTML = '';
    }
    
    const eventItem = document.createElement('div');
    eventItem.className = 'event-item';
    eventItem.innerHTML = `
        <span class="event-time">${formatTime(timestamp)}</span>
        <strong>${eventType}</strong><br>
        ${description}...
    `;
    
    eventsList.insertBefore(eventItem, eventsList.firstChild);
    
    // Keep only last 5 events
    while (eventsList.children.length > 5) {
        eventsList.removeChild(eventsList.lastChild);
    }
}

function updateStatus(status) {
    document.getElementById('processingStatus').textContent = status;
}

function updateCurrentChunk(chunkIndex) {
    document.getElementById('currentChunk').textContent = chunkIndex;
}

// Timeline
function initializeTimeline() {
    const timeline = document.getElementById('timeline');
    timeline.innerHTML = '';
    
    const totalChunks = Math.ceil(state.videoDuration / state.chunkDuration);
    
    for (let i = 0; i < totalChunks; i++) {
        const chunk = document.createElement('div');
        chunk.className = 'timeline-chunk';
        chunk.dataset.chunkIndex = i;
        
        const startTime = i * state.chunkDuration;
        
        chunk.innerHTML = `
            <div class="chunk-time">${formatTime(startTime)}</div>
            <div class="chunk-status">Pending</div>
        `;
        
        chunk.addEventListener('click', () => {
            if (state.player) {
                state.player.seekTo(startTime);
            }
        });
        
        timeline.appendChild(chunk);
    }
}

function updateTimelineChunk(chunkIndex, status) {
    const chunk = document.querySelector(`[data-chunk-index="${chunkIndex}"]`);
    if (!chunk) return;
    
    chunk.classList.remove('processing', 'completed', 'error');
    
    const statusDiv = chunk.querySelector('.chunk-status');
    
    if (status === 'processing') {
        chunk.classList.add('processing');
        statusDiv.textContent = 'Processing...';
    } else if (status === 'completed') {
        chunk.classList.add('completed');
        statusDiv.textContent = 'Done';
    } else if (status === 'error') {
        statusDiv.textContent = 'Error';
    }
}

// Analytics
function updateAnalytics() {
    document.getElementById('totalChunks').textContent = state.analytics.totalChunks;
    document.getElementById('avgProcessing').textContent = 
        `${Math.round(state.analytics.avgProcessingTime / 1000)}s`;
    document.getElementById('eventsDetected').textContent = state.analytics.eventsDetected;
    document.getElementById('peakExcitement').textContent = 
        `${Math.round(state.analytics.peakExcitement * 100)}%`;
}

// Utility Functions
function extractVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

function showError(message) {
    const errorDiv = document.getElementById('videoError');
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}

function hideError() {
    const errorDiv = document.getElementById('videoError');
    errorDiv.classList.remove('show');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
}

async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('Backend is healthy');
        }
    } catch (error) {
        console.error('Backend health check failed:', error);
        showToast('Warning: Backend may not be running', 'warning');
    }
}