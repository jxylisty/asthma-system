import { ref } from 'vue'

let speechSynthesis = null
let voices = []
let currentUtterance = null

const isSpeaking = ref(false)
const currentText = ref('')

function initSpeech() {
  if ('speechSynthesis' in window) {
    speechSynthesis = window.speechSynthesis
    
    const loadVoices = () => {
      voices = speechSynthesis.getVoices().filter(v => v.lang.startsWith('zh'))
      if (voices.length === 0) {
        voices = speechSynthesis.getVoices()
      }
    }
    
    loadVoices()
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices
    }
  }
}

function getVoices() {
  return voices
}

function speak(text, options = {}) {
  if (!speechSynthesis) {
    initSpeech()
    if (!speechSynthesis) {
      console.warn('浏览器不支持语音合成')
      return
    }
  }

  stop()

  const utterance = new SpeechSynthesisUtterance(text)
  
  if (options.voice) {
    const voice = voices.find(v => v.name === options.voice || v.lang === options.voice)
    if (voice) {
      utterance.voice = voice
    }
  }
  
  if (options.rate !== undefined) {
    utterance.rate = options.rate
  }
  
  if (options.pitch !== undefined) {
    utterance.pitch = options.pitch
  }
  
  utterance.onstart = () => {
    isSpeaking.value = true
    currentText.value = text
  }
  
  utterance.onend = () => {
    isSpeaking.value = false
    currentText.value = ''
  }
  
  utterance.onerror = () => {
    isSpeaking.value = false
    currentText.value = ''
  }

  currentUtterance = utterance
  speechSynthesis.speak(utterance)
}

function stop() {
  if (speechSynthesis) {
    speechSynthesis.cancel()
    isSpeaking.value = false
    currentText.value = ''
    currentUtterance = null
  }
}

function pause() {
  if (speechSynthesis && isSpeaking.value) {
    speechSynthesis.pause()
    isSpeaking.value = false
  }
}

function resume() {
  if (speechSynthesis && currentUtterance) {
    speechSynthesis.resume()
    isSpeaking.value = true
  }
}

export function useSpeech() {
  initSpeech()
  
  return {
    isSpeaking,
    currentText,
    speak,
    stop,
    pause,
    resume,
    getVoices,
    initSpeech
  }
}
