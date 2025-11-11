import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Typography,
  Box,
  ToggleButtonGroup,
  ToggleButton,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import VideoCard from './VideoCard';
import CaptionViewer from './CaptionViewer';
import LoadingDialog from './LoadingDialog';
import ModelSelector from './ModelSelector';
import { videoAPI } from '../services/api';

const VideoList = () => {
  const [videos, setVideos] = useState([]);
  const [filteredVideos, setFilteredVideos] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [processingMessage, setProcessingMessage] = useState('');
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  
  // Caption viewer state
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);
  
  // Model selection state
  const [modelSelectorOpen, setModelSelectorOpen] = useState(false);
  const [availableModels, setAvailableModels] = useState(null);
  const [defaultModel, setDefaultModel] = useState('qwen2vl');
  const [pendingFilename, setPendingFilename] = useState(null);
  const [pendingRegenerate, setPendingRegenerate] = useState(false);

  // Fetch available models
  const fetchModels = async () => {
    try {
      const data = await videoAPI.getModels();
      setAvailableModels(data.models);
      setDefaultModel(data.default || 'qwen2vl');
    } catch (err) {
      console.error('Error fetching models:', err);
    }
  };

  // Fetch videos
  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await videoAPI.getVideos();
      setVideos(data);
      applyFilter(data, filter);
    } catch (err) {
      setError('Failed to load videos. Is the backend running?');
      console.error('Error fetching videos:', err);
    } finally {
      setLoading(false);
    }
  };

  // Apply filter
  const applyFilter = (videoList, currentFilter) => {
    let filtered = videoList;
    
    if (currentFilter === 'captioned') {
      filtered = videoList.filter(v => v.has_caption);
    } else if (currentFilter === 'not-captioned') {
      filtered = videoList.filter(v => !v.has_caption);
    }
    
    setFilteredVideos(filtered);
  };

  // Handle filter change
  const handleFilterChange = (event, newFilter) => {
    if (newFilter !== null) {
      setFilter(newFilter);
      applyFilter(videos, newFilter);
    }
  };

  // Open model selector
  const handleGenerateCaption = (filename, regenerate = false) => {
    setPendingFilename(filename);
    setPendingRegenerate(regenerate);
    setModelSelectorOpen(true);
  };

  // Generate caption with selected model and custom prompt
  const handleModelSelected = async (modelKey, customPrompt) => {
    if (!pendingFilename) return;
    
    try {
      setProcessing(true);
      const modelName = availableModels?.[modelKey]?.display_name || modelKey;
      setProcessingMessage(
        pendingRegenerate
          ? `Regenerating caption with ${modelName}...`
          : `Generating caption with ${modelName}...`
      );

      await videoAPI.generateCaption(pendingFilename, modelKey, customPrompt, pendingRegenerate);
      
      setSnackbar({
        open: true,
        message: `Caption generated successfully with ${modelName}!`,
        severity: 'success',
      });

      // Refresh video list
      await fetchVideos();
    } catch (err) {
      setSnackbar({
        open: true,
        message: `Failed to generate caption: ${err.response?.data?.detail || err.message}`,
        severity: 'error',
      });
      console.error('Error generating caption:', err);
    } finally {
      setProcessing(false);
      setPendingFilename(null);
      setPendingRegenerate(false);
    }
  };

  // Generate audio from video
  const handleGenerateAudio = async (filename) => {
    try {
      setProcessing(true);
      setProcessingMessage('Extracting audio from video...');

      await videoAPI.generateAudio(filename);
      
      setSnackbar({
        open: true,
        message: 'Audio generated successfully!',
        severity: 'success',
      });

      // Refresh video list
      await fetchVideos();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message;
      setSnackbar({
        open: true,
        message: `Failed to generate audio: ${errorMessage}`,
        severity: 'error',
      });
      console.error('Error generating audio:', err);
    } finally {
      setProcessing(false);
    }
  };

  // View caption(s)
  const handleViewCaption = (video) => {
    setSelectedVideo(video);
    setViewerOpen(true);
  };

  // Refresh videos after caption generation in viewer
  const handleCaptionGeneratedInViewer = async () => {
    await fetchVideos();
  };

  // Close viewer
  const handleCloseViewer = () => {
    setViewerOpen(false);
    setSelectedVideo(null);
  };

  // Regenerate from viewer
  const handleRegenerateFromViewer = async () => {
    if (selectedVideo) {
      handleCloseViewer();
      await handleGenerateCaption(selectedVideo.filename, true);
    }
  };

  // Fetch models and videos on mount
  useEffect(() => {
    fetchModels();
    fetchVideos();
    const interval = setInterval(fetchVideos, 10000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update filtered videos when filter changes
  useEffect(() => {
    applyFilter(videos, filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  if (loading && videos.length === 0) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h6" component="h1" gutterBottom>
          Video Caption Service
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Generate captions using For any video file
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Filter and Stats */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
        flexWrap="wrap"
        gap={2}
      >
        <ToggleButtonGroup
          value={filter}
          exclusive
          onChange={handleFilterChange}
          size="small"
        >
          <ToggleButton value="all">
            All ({videos.length})
          </ToggleButton>
          <ToggleButton value="captioned">
            Captioned ({videos.filter(v => v.has_caption).length})
          </ToggleButton>
          <ToggleButton value="not-captioned">
            Not Captioned ({videos.filter(v => !v.has_caption).length})
          </ToggleButton>
        </ToggleButtonGroup>

        <Typography variant="body2" color="text.secondary">
          Auto-refreshing every 10 seconds
        </Typography>
      </Box>

      {/* Video Grid */}
      {filteredVideos.length === 0 ? (
        <Alert severity="info">
          {filter === 'all'
            ? 'No videos found. Place video files in the backend/videos directory.'
            : filter === 'captioned'
            ? 'No captioned videos found.'
            : 'All videos have captions!'}
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredVideos.map((video) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={video.filename}>
              <VideoCard
                video={video}
                onGenerateCaption={handleGenerateCaption}
                onViewCaption={handleViewCaption}
                onGenerateAudio={handleGenerateAudio}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Model Selector Dialog */}
      <ModelSelector
        open={modelSelectorOpen}
        onClose={() => setModelSelectorOpen(false)}
        onSelect={handleModelSelected}
        models={availableModels}
        defaultModel={defaultModel}
      />

      {/* Loading Dialog */}
      <LoadingDialog open={processing} message={processingMessage} />

      {/* Caption Viewer */}
      {selectedVideo && (
        <CaptionViewer
          open={viewerOpen}
          onClose={handleCloseViewer}
          videoFilename={selectedVideo.filename}
          videoUrl={videoAPI.getVideoStreamUrl(selectedVideo.filename)}
          onRegenerate={handleCaptionGeneratedInViewer}
        />
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default VideoList;

