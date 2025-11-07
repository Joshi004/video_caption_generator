import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Stack,
  Divider,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { videoAPI } from '../services/api';

const CaptionViewer = ({
  open,
  onClose,
  videoFilename,
  videoUrl,
  onRegenerate,
}) => {
  const [allCaptions, setAllCaptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [availableModels, setAvailableModels] = useState({});
  const [generating, setGenerating] = useState(null);

  // Fetch all captions when dialog opens
  useEffect(() => {
    if (open && videoFilename) {
      fetchAllCaptions();
      fetchModels();
    }
  }, [open, videoFilename]);

  const fetchAllCaptions = async () => {
    try {
      setLoading(true);
      const data = await videoAPI.getAllCaptions(videoFilename);
      setAllCaptions(data.captions || []);
    } catch (error) {
      console.error('Error fetching captions:', error);
      setAllCaptions([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    try {
      const data = await videoAPI.getModels();
      setAvailableModels(data.models || {});
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const handleGenerateWithModel = async (modelKey) => {
    try {
      setGenerating(modelKey);
      await videoAPI.generateCaption(videoFilename, modelKey, null, false);
      await fetchAllCaptions();
    } catch (error) {
      console.error(`Error generating with ${modelKey}:`, error);
    } finally {
      setGenerating(null);
    }
  };

  const handleRegenerateModel = async (modelKey) => {
    try {
      setGenerating(modelKey);
      await videoAPI.generateCaption(videoFilename, modelKey, null, true);
      await fetchAllCaptions();
    } catch (error) {
      console.error(`Error regenerating with ${modelKey}:`, error);
    } finally {
      setGenerating(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (seconds) => {
    return `${seconds.toFixed(1)}s`;
  };

  const getCaptionForModel = (modelKey) => {
    return allCaptions.find(c => c.model_key === modelKey);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{videoFilename}</Typography>
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3 }}>
        <Box
          display="flex"
          flexDirection={{ xs: 'column', md: 'row' }}
          gap={3}
          height="100%"
        >
          {/* Left: Video Player (50%) */}
          <Box flex={1} minWidth="0">
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ height: '100%', p: 0 }}>
                <video
                  controls
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    backgroundColor: '#000',
                  }}
                  src={videoUrl}
                >
                  Your browser does not support the video tag.
                </video>
              </CardContent>
            </Card>
          </Box>

          {/* Right: All Model Captions (50%) */}
          <Box
            flex={1}
            minWidth="0"
            sx={{
              overflowY: 'auto',
              maxHeight: '100%',
            }}
          >
            <Typography variant="h6" gutterBottom color="primary">
              Model Captions
            </Typography>

            {loading ? (
              <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
              </Box>
            ) : (
              <Stack spacing={2}>
                {/* Show captions for each available model */}
                {Object.keys(availableModels).map((modelKey) => {
                  const modelInfo = availableModels[modelKey];
                  const caption = getCaptionForModel(modelKey);

                  return (
                    <Accordion 
                      key={modelKey}
                      defaultExpanded={!!caption}
                      sx={{
                        border: '1px solid',
                        borderColor: caption ? 'success.light' : 'grey.300',
                        '&:before': { display: 'none' },
                      }}
                    >
                      <AccordionSummary 
                        expandIcon={<ExpandMoreIcon />}
                        sx={{
                          backgroundColor: caption ? 'success.50' : 'grey.50',
                          '&:hover': { backgroundColor: caption ? 'success.100' : 'grey.100' },
                        }}
                      >
                        <Box display="flex" alignItems="center" gap={1} width="100%">
                          {caption ? (
                            <CheckCircleIcon color="success" fontSize="small" />
                          ) : (
                            <Box sx={{ width: 20, height: 20, borderRadius: '50%', bgcolor: 'grey.300' }} />
                          )}
                          <Typography variant="subtitle1" fontWeight="bold">
                            {modelInfo.display_name}
                          </Typography>
                          {caption && (
                            <Chip label={caption.model_key.toUpperCase()} size="small" color="primary" />
                          )}
                        </Box>
                      </AccordionSummary>
                      
                      <AccordionDetails>
                        {/* Action Button */}
                        <Box display="flex" justifyContent="flex-end" mb={2}>
                          {caption ? (
                            <Button
                              startIcon={<RefreshIcon />}
                              variant="outlined"
                              size="small"
                              onClick={() => handleRegenerateModel(modelKey)}
                              disabled={generating === modelKey}
                            >
                              {generating === modelKey ? 'Regenerating...' : 'Regenerate'}
                            </Button>
                          ) : (
                            <Button
                              startIcon={<AddIcon />}
                              variant="contained"
                              size="small"
                              onClick={() => handleGenerateWithModel(modelKey)}
                              disabled={generating === modelKey}
                            >
                              {generating === modelKey ? 'Generating...' : 'Generate'}
                            </Button>
                          )}
                        </Box>

                        {/* Caption Content or Placeholder */}
                        {caption ? (
                          <>
                            {/* Metadata */}
                            <Stack direction="row" spacing={2} mb={2}>
                              <Box display="flex" alignItems="center" gap={0.5}>
                                <AccessTimeIcon fontSize="small" color="action" />
                                <Typography variant="caption" color="text.secondary">
                                  Generated: {formatDate(caption.generated_at)}
                                </Typography>
                              </Box>
                              <Typography variant="caption" color="text.secondary">
                                Processing: {formatDuration(caption.processing_time_seconds)}
                              </Typography>
                            </Stack>

                            <Divider sx={{ mb: 2 }} />

                            {/* Show Prompt Used */}
                            {caption.prompt && (
                              <Box 
                                mb={2} 
                                p={1.5} 
                                sx={{ 
                                  backgroundColor: 'info.lighter',
                                  borderRadius: 1,
                                  borderLeft: 3,
                                  borderColor: 'info.main'
                                }}
                              >
                                <Typography 
                                  variant="caption" 
                                  fontWeight="bold" 
                                  color="info.dark"
                                  display="block"
                                  gutterBottom
                                >
                                  📝 Prompt Used:
                                </Typography>
                                <Typography 
                                  variant="body2" 
                                  sx={{ 
                                    fontStyle: 'italic',
                                    color: 'text.secondary'
                                  }}
                                >
                                  "{caption.prompt}"
                                </Typography>
                              </Box>
                            )}

                            {/* Caption Text */}
                            <Box
                              sx={{
                                maxHeight: 300,
                                overflowY: 'auto',
                                p: 2,
                                backgroundColor: 'grey.50',
                                borderRadius: 1,
                              }}
                            >
                              <Typography 
                                variant="caption" 
                                fontWeight="bold" 
                                color="text.secondary"
                                display="block"
                                gutterBottom
                              >
                                Caption:
                              </Typography>
                              <Typography
                                variant="body2"
                                sx={{
                                  whiteSpace: 'pre-wrap',
                                  lineHeight: 1.8,
                                }}
                              >
                                {caption.caption}
                              </Typography>
                            </Box>
                          </>
                        ) : (
                          <Alert severity="info">
                            No caption generated with {modelInfo.display_name} yet.
                            Click "Generate" above to create one.
                          </Alert>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  );
                })}

                {allCaptions.length === 0 && !loading && (
                  <Alert severity="warning">
                    No captions generated for this video yet. Close this dialog and click "Generate Caption" to create one.
                  </Alert>
                )}
              </Stack>
            )}
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default CaptionViewer;



