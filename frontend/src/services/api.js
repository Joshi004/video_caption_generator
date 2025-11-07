import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8011';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for video processing
});

// API endpoints
export const videoAPI = {
  // Get all videos
  getVideos: async () => {
    const response = await api.get('/api/videos');
    return response.data;
  },

  // Get single video info
  getVideoInfo: async (filename) => {
    const response = await api.get(`/api/videos/${filename}`);
    return response.data;
  },

  // Get available AI models
  getModels: async () => {
    const response = await api.get('/api/videos/available-models');
    return response.data;
  },

  // Get video stream URL
  getVideoStreamUrl: (filename) => {
    return `${API_BASE_URL}/api/videos/${filename}/stream`;
  },

  // Generate caption with model selection
  generateCaption: async (filename, model = 'qwen2vl', prompt = null, regenerate = false) => {
    const params = { model, regenerate };
    const data = prompt ? { prompt } : {};
    
    const response = await api.post(
      `/api/videos/${filename}/caption`,
      data,
      { params }
    );
    return response.data;
  },

  // Get all captions from all models
  getAllCaptions: async (filename) => {
    const response = await api.get(`/api/videos/${filename}/all-captions`);
    return response.data;
  },

  // Get existing caption (first available)
  getCaption: async (filename) => {
    const response = await api.get(`/api/videos/${filename}/caption`);
    return response.data;
  },

  // Delete caption
  deleteCaption: async (filename) => {
    const response = await api.delete(`/api/videos/${filename}/caption`);
    return response.data;
  },
};

// Health check
export const healthCheck = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
};

export default api;


